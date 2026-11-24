import userEvent from '@testing-library/user-event';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../api/client';
import LoginPage from './LoginPage';

vi.mock('../../api/client', () => ({ api: vi.fn() }));

afterEach(() => vi.clearAllMocks());

function renderLogin() {
  return render(<MemoryRouter initialEntries={['/login?next=%2Fdashboard']}><LoginPage /></MemoryRouter>);
}

async function submitCredentials() {
  const user = userEvent.setup();
  await user.type(screen.getByRole('textbox', { name: /Email/ }), 'person@example.test');
  await user.type(screen.getByLabelText(/Password/), 'invalid-password');
  await user.click(screen.getByRole('button', { name: 'Continue' }));
}

describe('login error states', () => {
  it('shows remaining attempts for rejected credentials', async () => {
    vi.mocked(api).mockRejectedValue({ status: 400, code: 'validation_error', message: 'Incorrect email or password.', attemptsLeft: 3 });
    renderLogin();
    await submitCredentials();
    expect(await screen.findByRole('alert')).toHaveTextContent('3 attempts left.');
  });

  it('shows a pending-approval notice instead of an authentication error', async () => {
    vi.mocked(api).mockRejectedValue({ status: 403, code: 'account_pending', message: 'Your account is awaiting approval.' });
    renderLogin();
    await submitCredentials();
    expect(await screen.findByRole('status')).toHaveTextContent('Your account is awaiting approval.');
  });

  it('disables sign-in while the lockout countdown is active', async () => {
    vi.mocked(api).mockRejectedValue({ status: 429, code: 'account_locked', message: 'Account locked.', retryAfter: 60 });
    renderLogin();
    await submitCredentials();
    expect(await screen.findByRole('alert')).toHaveTextContent('Account locked.');
    expect(screen.getByRole('button', { name: 'Continue' })).toBeDisabled();
  });
});
