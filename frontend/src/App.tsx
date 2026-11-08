import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import DesignPage from './DesignPage';

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
      <Route path="/" element={<Navigate to={import.meta.env.DEV ? '/design' : '/not-found'} replace />} />
      <Route path="/session-expired" element={<main className="design-page"><h1>Session expired</h1><p>Please sign in again.</p></main>} />
      <Route path="*" element={<main className="design-page"><h1>Page not found</h1></main>} />
    </Routes>
  </>;
}
