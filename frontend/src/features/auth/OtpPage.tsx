import { useEffect, useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import type { components } from '../../api/schema.gen';
import { api, type ApiError } from '../../api/client';
import { Button, OtpInput } from '../../components/ui';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';
import { clearAuthChallenge, formatDuration, readAuthChallenge, safeNextPath, storeAuthChallenge } from '../../auth/auth-utils';
import { useSession } from '../../auth/AuthProvider';
import { useCountdown } from '../../auth/useCountdown';

export default function OtpPage() {
  useDocumentMeta({ title: 'Verify your email | EviTrack', description: 'Enter the one-time code sent to your email address.' });
  const navigate = useNavigate();
  const { refreshUser } = useSession();
  const [challenge, setChallenge] = useState(readAuthChallenge);
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');
  const [attemptsLeft, setAttemptsLeft] = useState<number | null>(null);
  const [lockoutUntil, setLockoutUntil] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const expiry = useCountdown(challenge?.expiresAt ?? null);
  const resendCooldown = useCountdown(challenge?.resendAt ?? null);
  const locked = useCountdown(lockoutUntil);

  useEffect(() => {
    if (!challenge) return;
    if (expiry === 0) setMessage('This code has expired. Return to sign in to request a new one.');
  }, [challenge, expiry]);

  if (!challenge) return <Navigate to="/login" replace />;

  const updateChallenge = (next: typeof challenge) => {
    setChallenge(next);
    storeAuthChallenge(next);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (code.length !== 6 || busy || locked > 0 || expiry === 0) return;
    setBusy(true);
    setMessage('');
    try {
      const result = await api<components['schemas']['AuthStatus']>('/auth/otp/verify/', { method: 'POST', body: JSON.stringify({ code }) });
      if (result.status === 'totp_required') navigate('/login/totp', { replace: true });
      else {
        clearAuthChallenge();
        await refreshUser();
        navigate(safeNextPath(challenge.next), { replace: true });
      }
    } catch (error) {
      const apiError = error as ApiError;
      setAttemptsLeft(apiError.attemptsLeft ?? null);
      if (apiError.code === 'otp_locked') setLockoutUntil(Date.now() + (apiError.retryAfter ?? 900) * 1000);
      setMessage(apiError.message || 'That code could not be verified.');
      setCode('');
    } finally {
      setBusy(false);
    }
  };

  const resend = async () => {
    if (resendCooldown > 0 || busy || locked > 0) return;
    setBusy(true);
    setMessage('');
    try {
      const result = await api<components['schemas']['ResendResponse']>('/auth/otp/resend/', { method: 'POST' });
      updateChallenge({ ...challenge, resendAt: Date.now() + result.resend_in * 1000 });
      setCode('');
      setAttemptsLeft(null);
    } catch (error) {
      const apiError = error as ApiError;
      if (apiError.retryAfter) updateChallenge({ ...challenge, resendAt: Date.now() + apiError.retryAfter * 1000 });
      setMessage(apiError.message || 'A new code could not be sent.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="auth-card" aria-labelledby="otp-title">
      <div className="auth-card__heading"><p className="auth-eyebrow">Email verification</p><h1 id="otp-title">Check your email</h1><p>We sent a 6-digit code to <strong>{challenge.sentToMasked}</strong>.</p><p className="auth-timer">Code expires in {formatDuration(expiry)}</p></div>
      {message && <p className={locked ? 'auth-notice' : 'auth-alert'} role="alert">{message}{attemptsLeft !== null ? ` ${attemptsLeft} attempts left.` : ''}{locked ? ` Try again in ${formatDuration(locked)}.` : ''}</p>}
      <form className="auth-form" onSubmit={submit}>
        <OtpInput value={code} onChange={setCode} />
        <Button type="submit" className="auth-submit" loading={busy} disabled={code.length !== 6 || expiry === 0 || locked > 0}>Verify</Button>
      </form>
      <div className="auth-links"><button type="button" className="auth-link-button" disabled={resendCooldown > 0 || busy || locked > 0} onClick={resend}>{resendCooldown > 0 ? `Resend code in ${formatDuration(resendCooldown)}` : 'Resend code'}</button><Link to="/login">Back to sign in</Link></div>
      {import.meta.env.DEV && <p className="auth-dev-note">Development mode: the code is printed in the server console.</p>}
    </section>
  );
}
