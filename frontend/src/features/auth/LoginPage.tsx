import { useState, type FormEvent } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import type { components } from '../../api/schema.gen';
import { api } from '../../api/client';
import { Button, Input } from '../../components/ui';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';
import { formatDuration, isApiError, safeNextPath, storeAuthChallenge } from '../../auth/auth-utils';
import { useCountdown } from '../../auth/useCountdown';

const schema = z.object({ email: z.string().trim().email('Enter a valid email address.'), password: z.string().min(1, 'Enter your password.'), remember_me: z.boolean() });

export default function LoginPage() {
  useDocumentMeta({ title: 'Sign in | EviTrack', description: 'Sign in to manage cases and digital evidence securely.' });
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState('');
  const [pendingApproval, setPendingApproval] = useState(false);
  const [attemptsLeft, setAttemptsLeft] = useState<number | null>(null);
  const [lockoutUntil, setLockoutUntil] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const lockoutSeconds = useCountdown(lockoutUntil);
  const next = safeNextPath(searchParams.get('next'));

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parsed = schema.safeParse({ email, password, remember_me: rememberMe });
    if (!parsed.success) {
      setMessage(parsed.error.issues[0]?.message ?? 'Check your sign-in details.');
      return;
    }
    setSubmitting(true);
    setMessage('');
    setPendingApproval(false);
    try {
      const result = await api<components['schemas']['LoginResponse']>('/auth/login/', { method: 'POST', body: JSON.stringify(parsed.data) });
      storeAuthChallenge({ sentToMasked: result.otp.sent_to_masked, expiresAt: Date.now() + result.otp.expires_in * 1000, resendAt: Date.now() + result.otp.resend_in * 1000, next });
      navigate('/login/otp');
    } catch (error) {
      if (isApiError(error)) {
        if (error.code === 'account_pending') setPendingApproval(true);
        else if (error.code === 'account_locked') setLockoutUntil(Date.now() + (error.retryAfter ?? 900) * 1000);
        else if (error.code === 'validation_error') setAttemptsLeft(error.attemptsLeft ?? null);
        setMessage(error.message);
      } else setMessage('We could not sign you in. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const disabled = submitting || lockoutSeconds > 0;
  return (
    <section className="auth-card" aria-labelledby="login-title">
      <div className="auth-card__heading"><p className="auth-eyebrow">Secure access</p><h1 id="login-title">Sign in</h1><p>Enter your account details to continue.</p></div>
      {pendingApproval && <p className="auth-notice" role="status">Your account is awaiting approval. <Link to="/register/pending">View request status</Link></p>}
      {message && !pendingApproval && <p className={lockoutSeconds ? 'auth-notice' : 'auth-alert'} role="alert">{lockoutSeconds ? `Account locked. Try again in ${formatDuration(lockoutSeconds)}.` : message}{attemptsLeft !== null && !lockoutSeconds ? ` ${attemptsLeft} attempts left.` : ''}</p>}
      <form className="auth-form" onSubmit={submit} noValidate>
        <Input label="Email" name="email" type="email" autoComplete="username" required value={email} error={email && !z.string().email().safeParse(email).success ? 'Enter a valid email address.' : undefined} onChange={(event) => { setEmail(event.target.value); setMessage(''); setAttemptsLeft(null); }} />
        <div className="auth-password-field">
          <Input label="Password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => { setPassword(event.target.value); setMessage(''); setAttemptsLeft(null); }} />
          <button type="button" className="auth-password-toggle" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((visible) => !visible)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button>
        </div>
        <label className="auth-terms"><input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} /> <span>Remember this device</span></label>
        <Button type="submit" className="auth-submit" loading={disabled} disabled={Boolean(lockoutSeconds)}>Continue</Button>
      </form>
      <p className="auth-card__footer">New here? <Link to="/register">Request access</Link></p>
    </section>
  );
}
