import { Link, useLocation } from 'react-router-dom';
import { safeNextPath } from '../../auth/auth-utils';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';

export default function SessionExpiredPage() {
  useDocumentMeta({ title: 'Session expired | EviTrack', description: 'Your session ended. Sign in again to continue.' });
  const location = useLocation();
  const next = safeNextPath((location.state as { next?: string } | null)?.next ?? null);
  return (
    <section className="auth-card auth-card--center" aria-labelledby="expired-title">
      <p className="auth-eyebrow">Session ended</p>
      <h1 id="expired-title">You were signed out due to inactivity.</h1>
      <p>Sign in again to continue where you left off.</p>
      <Link className="ui-button ui-button--primary auth-submit" to={`/login?next=${encodeURIComponent(next)}`}>Sign in again</Link>
    </section>
  );
}
