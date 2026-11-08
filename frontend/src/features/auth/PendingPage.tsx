import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';

export default function PendingPage() {
  useDocumentMeta({ title: 'Request received | EviTrack', description: 'Your EviTrack account request is waiting for administrator approval.' });
  return (
    <section className="auth-card auth-card--center" aria-labelledby="pending-title">
      <span className="auth-success-icon"><Check size={25} aria-hidden="true" /></span>
      <p className="auth-eyebrow">Request received</p>
      <h1 id="pending-title">Your account is awaiting approval</h1>
      <p>An administrator will review your request. You can sign in after your account is approved.</p>
      <Link className="ui-button ui-button--primary auth-submit" to="/login">Back to sign in</Link>
    </section>
  );
}
