import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import type { components } from '../../api/schema.gen';
import { api, type ApiError } from '../../api/client';
import { Button, OtpInput } from '../../components/ui';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';
import { clearAuthChallenge, isApiError, readAuthChallenge, safeNextPath } from '../../auth/auth-utils';
import { useSession } from '../../auth/AuthProvider';

export default function TotpPage() {
  useDocumentMeta({ title: 'Authenticator code | EviTrack', description: 'Verify the additional authenticator step for your account.' });
  const navigate = useNavigate();
  const { refreshUser } = useSession();
  const challenge = readAuthChallenge();
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');
  const [attemptsLeft, setAttemptsLeft] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  if (!challenge) return <Navigate to="/login" replace />;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (code.length !== 6 || busy) return;
    setBusy(true);
    setMessage('');
    try {
      const result = await api<components['schemas']['AuthStatus']>('/auth/totp/verify/', { method: 'POST', body: JSON.stringify({ code }) });
      if (result.status === 'authenticated') {
        clearAuthChallenge();
        await refreshUser();
        navigate(safeNextPath(challenge.next), { replace: true });
      }
    } catch (error) {
      const apiError = error as ApiError;
      setAttemptsLeft(isApiError(error) ? apiError.attemptsLeft ?? null : null);
      setMessage(apiError.message || 'That authenticator code could not be verified.');
      setCode('');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="auth-card" aria-labelledby="totp-title">
      <div className="auth-card__heading"><p className="auth-eyebrow">Additional verification</p><h1 id="totp-title">Authenticator code</h1><p>Open your authenticator app and enter the 6-digit code.</p></div>
      {message && <p className="auth-alert" role="alert">{message}{attemptsLeft !== null ? ` ${attemptsLeft} attempts left.` : ''}</p>}
      <form className="auth-form" onSubmit={submit}>
        <OtpInput value={code} onChange={setCode} label="Authenticator code" />
        <Button type="submit" className="auth-submit" loading={busy} disabled={code.length !== 6}>Verify</Button>
      </form>
      <p className="auth-card__footer"><Link to="/login/otp">Back to email code</Link></p>
    </section>
  );
}
