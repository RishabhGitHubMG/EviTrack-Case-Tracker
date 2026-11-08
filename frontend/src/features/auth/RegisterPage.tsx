import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import type { components } from '../../api/schema.gen';
import { api, type ApiError } from '../../api/client';
import { Button, Checkbox, Input, PasswordStrength, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';

const roles = ['case_manager', 'investigator', 'custodian', 'reviewer'] as const;
const schema = z.object({
  name: z.string().trim().min(2, 'Enter your full name.'),
  email: z.string().trim().email('Enter a valid email address.'),
  phone: z.string(),
  requested_role: z.enum(roles, { message: 'Choose a role.' }),
  password: z.string().min(12, 'Use at least 12 characters.').regex(/[A-Z]/, 'Add an uppercase letter.').regex(/[a-z]/, 'Add a lowercase letter.').regex(/\d/, 'Add a number.').regex(/[^A-Za-z0-9]/, 'Add a symbol.'),
  password2: z.string(),
}).refine((values) => values.password === values.password2, { path: ['password2'], message: 'Passwords do not match.' });

type FormValues = z.infer<typeof schema>;

function fieldMessage(error: unknown, name: string) {
  if (typeof error !== 'object' || error === null || !('fields' in error)) return undefined;
  const fields = error.fields as Record<string, unknown> | null;
  const value = fields?.[name];
  return Array.isArray(value) ? String(value[0]) : typeof value === 'string' ? value : undefined;
}

export default function RegisterPage() {
  useDocumentMeta({ title: 'Request access | EviTrack', description: 'Request an EviTrack account for your team.' });
  const navigate = useNavigate();
  const [values, setValues] = useState<FormValues>({ name: '', email: '', phone: '', requested_role: 'investigator', password: '', password2: '' });
  const [errors, setErrors] = useState<Partial<Record<keyof FormValues, string>>>({});
  const [message, setMessage] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const update = (name: keyof FormValues, value: string) => {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
    setMessage('');
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!termsAccepted) {
      setMessage('Accept the prototype terms before submitting.');
      return;
    }
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      setErrors(Object.fromEntries(parsed.error.issues.map((issue) => [issue.path[0], issue.message])));
      return;
    }

    setSubmitting(true);
    setMessage('');
    try {
      const result = await api<components['schemas']['RegistrationStatus']>('/auth/register/', { method: 'POST', body: JSON.stringify(parsed.data) });
      if (result.status === 'pending_approval') navigate('/register/pending', { replace: true });
    } catch (error) {
      const apiError = error as ApiError;
      setErrors({
        name: fieldMessage(apiError, 'name'),
        email: fieldMessage(apiError, 'email'),
        phone: fieldMessage(apiError, 'phone'),
        requested_role: fieldMessage(apiError, 'requested_role'),
        password: fieldMessage(apiError, 'password'),
        password2: fieldMessage(apiError, 'password2'),
      });
      setMessage(apiError.message || 'We could not submit your request. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-card" aria-labelledby="register-title">
      <div className="auth-card__heading"><p className="auth-eyebrow">Join your team</p><h1 id="register-title">Request access</h1><p>Submit your details. An administrator will review your request.</p></div>
      {message && <p className="auth-alert" role="alert">{message}</p>}
      <form className="auth-form" onSubmit={submit} noValidate>
        <Input label="Full name" name="name" autoComplete="name" required value={values.name} error={errors.name} onChange={(event) => update('name', event.target.value)} />
        <Input label="Email" name="email" type="email" autoComplete="email" required value={values.email} error={errors.email} onChange={(event) => update('email', event.target.value)} />
        <Input label="Phone (optional)" name="phone" type="tel" autoComplete="tel" value={values.phone} error={errors.phone} onChange={(event) => update('phone', event.target.value)} />
        <div className="auth-form__field">
          <span id="requested-role-label">Role requested</span>
          <Select value={values.requested_role} onValueChange={(value) => update('requested_role', value)}>
            <SelectTrigger id="requested_role" aria-labelledby="requested-role-label"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="case_manager">Case Manager</SelectItem>
              <SelectItem value="investigator">Investigator / Advocate</SelectItem>
              <SelectItem value="custodian">Evidence Custodian</SelectItem>
              <SelectItem value="reviewer">Read-only Reviewer</SelectItem>
            </SelectContent>
          </Select>
          {errors.requested_role && <span className="ui-field__error">{errors.requested_role}</span>}
        </div>
        <Input label="Password" name="password" type="password" autoComplete="new-password" required value={values.password} error={errors.password} onChange={(event) => update('password', event.target.value)} />
        <PasswordStrength password={values.password} />
        <Input label="Confirm password" name="password2" type="password" autoComplete="new-password" required value={values.password2} error={errors.password2} onChange={(event) => update('password2', event.target.value)} />
        <div className="auth-terms"><Checkbox required checked={termsAccepted} aria-label="Accept the prototype terms" onChange={(event) => setTermsAccepted(event.target.checked)} /> <span>I agree to use dummy data only in this prototype.</span></div>
        <Button type="submit" className="auth-submit" loading={submitting}>Request access</Button>
      </form>
      <p className="auth-card__footer">Already have access? <Link to="/login">Sign in</Link></p>
    </section>
  );
}
