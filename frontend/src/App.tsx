import { lazy, useEffect } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { PublicLayout } from './components/layout/PublicLayout';
import DesignPage from './DesignPage';

const LandingPage = lazy(() => import('./features/landing/pages/LandingPage'));

function SessionExpirationHandler() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleUnauthorized = () => {
      const next = `${window.location.pathname}${window.location.search}`;
      navigate('/session-expired', { state: { next } });
    };
    window.addEventListener('evitrack:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('evitrack:unauthorized', handleUnauthorized);
  }, [location.pathname, location.search, navigate]);

  return null;
}

export default function App() {
  return <>
    <SessionExpirationHandler />
    <Routes>
      {import.meta.env.DEV && <Route path="/design" element={<DesignPage />} />}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
      </Route>
      <Route path="/session-expired" element={<main className="design-page"><h1>Session expired</h1><p>Please sign in again.</p></main>} />
      <Route path="*" element={<main className="design-page"><h1>Page not found</h1></main>} />
    </Routes>
  </>;
}
