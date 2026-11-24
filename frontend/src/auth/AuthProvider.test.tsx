import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api/client';
import type { components } from '../api/schema.gen';
import { AuthProvider } from './AuthProvider';
import { PublicOnly, RequireAuth } from './RequireAuth';

vi.mock('../api/client', () => ({ api: vi.fn() }));

afterEach(() => vi.clearAllMocks());

const user = {
  id: 1,
  name: 'Demo Admin',
  email: 'admin@demo.evitrack.test',
  permissions: [],
  preferences: { theme: 'light', email_enabled: true, sms_enabled: false, reminder_hearing: [], reminder_deadline: [] },
  totp_enabled: false,
  unread_notifications: 0,
  pending_custody: 0,
  pending_approvals: 0,
} as components['schemas']['User'];

function CurrentRoute() {
  const location = useLocation();
  return <output aria-label="Current route">{location.pathname}{location.search}</output>;
}

function renderRoutes(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <CurrentRoute />
        <Routes>
          <Route path="/login" element={<PublicOnly><h1>Sign in page</h1></PublicOnly>} />
          <Route path="/dashboard" element={<RequireAuth><h1>Dashboard page</h1></RequireAuth>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('authentication route guards', () => {
  it('sends signed-out dashboard visitors to login with their destination', async () => {
    vi.mocked(api).mockRejectedValue({ status: 401, code: 'not_authenticated' });
    renderRoutes('/dashboard?tab=cases');
    expect(await screen.findByRole('heading', { name: 'Sign in page' })).toBeInTheDocument();
    expect(screen.getByLabelText('Current route')).toHaveTextContent('/login?next=%2Fdashboard%3Ftab%3Dcases');
  });

  it('sends signed-in visitors away from the login page', async () => {
    vi.mocked(api).mockResolvedValue(user);
    renderRoutes('/login');
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Dashboard page' })).toBeInTheDocument());
  });
});
