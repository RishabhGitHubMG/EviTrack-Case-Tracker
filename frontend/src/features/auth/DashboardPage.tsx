import { useNavigate } from 'react-router-dom';
import { useSession } from '../../auth/AuthProvider';
import { Button } from '../../components/ui';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, signOut } = useSession();
  const leave = async () => {
    await signOut();
    navigate('/login', { replace: true });
  };
  return (
    <main className="auth-card" aria-labelledby="dashboard-title">
      <p className="auth-eyebrow">Signed in</p>
      <h1 id="dashboard-title">Welcome, {user?.name}</h1>
      <p>Your authenticated session is ready. The dashboard will be available in the next frontend slice.</p>
      <Button variant="secondary" onClick={() => void leave()}>Sign out</Button>
    </main>
  );
}
