import { lazy, useEffect } from 'react';
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useSession } from './auth/AuthProvider';
import { AuthLayout } from './auth/AuthLayout';
import { PublicOnly, RequireAuth } from './auth/RequireAuth';
import { PublicLayout } from './components/layout/PublicLayout';
import DesignPage from './DesignPage';

const LandingPage = lazy(() => import('./features/landing/pages/LandingPage'));
const LoginPage = lazy(() => import('./features/auth/LoginPage'));
const RegisterPage = lazy(() => import('./features/auth/RegisterPage'));
const PendingPage = lazy(() => import('./features/auth/PendingPage'));
const OtpPage = lazy(() => import('./features/auth/OtpPage'));
const TotpPage = lazy(() => import('./features/auth/TotpPage'));
const DashboardPage = lazy(() => import('./features/auth/DashboardPage'));
const SessionExpiredPage = lazy(() => import('./features/auth/SessionExpiredPage'));

function SessionExpirationHandler() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, loading, expireSession } = useSession();

  useEffect(() => {
    const handleUnauthorized = () => {
      if (loading || !user) return;
      const next = `${window.location.pathname}${window.location.search}`;
      expireSession();
      navigate('/session-expired', { state: { next } });
    };
    window.addEventListener('evitrack:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('evitrack:unauthorized', handleUnauthorized);
  }, [location.pathname, location.search, navigate, user, loading, expireSession]);

  return null;
}

export default function App() {
  return <AuthProvider>
    <SessionExpirationHandler />
    <Routes>
      {import.meta.env.DEV && <Route path="/design" element={<DesignPage />} />}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
      </Route>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
        <Route path="/login/otp" element={<PublicOnly><OtpPage /></PublicOnly>} />
        <Route path="/login/totp" element={<PublicOnly><TotpPage /></PublicOnly>} />
        <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />
        <Route path="/register/pending" element={<PendingPage />} />
        <Route path="/session-expired" element={<SessionExpiredPage />} />
      </Route>
      <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
      <Route path="*" element={<main className="system-page"><h1>Page not found</h1><p>We couldn’t find that page.</p><Link to="/">Return to EviTrack</Link></main>} />
    </Routes>
  </AuthProvider>;
}
