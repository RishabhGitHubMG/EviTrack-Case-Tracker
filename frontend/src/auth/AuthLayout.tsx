import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Fingerprint, ShieldCheck } from 'lucide-react';
import { Logo } from '../components/layout/PublicLayout';
import '../styles/auth.css';

export function AuthLayout() {
  return (
    <div className="auth-shell">
      <aside className="auth-brand" aria-label="EviTrack security">
        <Logo />
        <div className="auth-brand__message">
          <span className="auth-brand__icon"><Fingerprint size={26} aria-hidden="true" /></span>
          <p className="auth-brand__eyebrow">Evidence with integrity</p>
          <blockquote>“The record is only as strong as the proof behind it.”</blockquote>
          <p className="auth-brand__caption"><ShieldCheck size={16} aria-hidden="true" /> Every handover has a clear record.</p>
        </div>
        <p className="auth-brand__footer">EviTrack · Prototype with dummy data</p>
      </aside>
      <main className="auth-main">
        <div className="auth-mobile-logo"><Logo /></div>
        <Suspense fallback={<p className="auth-loading" role="status">Loading…</p>}><Outlet /></Suspense>
      </main>
    </div>
  );
}
