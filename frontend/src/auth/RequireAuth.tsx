import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useSession } from './AuthProvider';

export function RequireAuth({ children }: { children: ReactNode }) {
  const { loading, user } = useSession();
  const location = useLocation();
  if (loading) return <main className="auth-loading" aria-label="Loading session">Loading…</main>;
  if (!user) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }
  return children;
}

export function PublicOnly({ children }: { children: ReactNode }) {
  const { loading, user } = useSession();
  if (loading) return <main className="auth-loading" aria-label="Loading session">Loading…</main>;
  return user ? <Navigate to="/dashboard" replace /> : children;
}
