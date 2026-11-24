import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

const mobile = { width: 390, height: 844 };

async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter((violation) => ['serious', 'critical'].includes(violation.impact ?? ''))).toEqual([]);
}

test('J1 request access reaches pending approval and sign-in explains the state', async ({ page }) => {
  await page.setViewportSize(mobile);
  const email = `frontend-${Date.now()}@demo.evitrack.test`;
  await page.goto('/register');
  await expect(page.getByRole('heading', { name: 'Request access' })).toBeVisible();
  await page.screenshot({ path: '../docs/screenshots/S2/register-390.png', fullPage: true });
  await expectAccessible(page);

  await page.getByRole('button', { name: 'Request access' }).click();
  await expect(page.getByText('Accept the prototype terms before submitting.')).toBeVisible();
  await page.getByRole('checkbox', { name: 'Accept the prototype terms' }).check();
  await page.getByRole('button', { name: 'Request access' }).click();
  await expect(page.getByText('Enter your full name.')).toBeVisible();
  await page.getByLabel('Full name').fill('EviTrack Test User');
  await page.getByLabel('Email').fill(email);
  await page.locator('input[name="password"]').fill('Case#SafePass2026');
  await page.getByLabel('Confirm password').fill('Case#SafePass2026');
  await page.getByRole('checkbox', { name: 'Accept the prototype terms' }).check();
  await page.getByRole('button', { name: 'Request access' }).click();

  await expect(page.getByRole('heading', { name: 'Your account is awaiting approval' })).toBeVisible();
  await expectAccessible(page);
  await page.getByRole('link', { name: 'Back to sign in' }).click();
  await page.getByLabel('Email').fill(email);
  await page.locator('input[name="password"]').fill('Case#SafePass2026');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.getByText('Your account is awaiting approval.')).toBeVisible();
  await expectAccessible(page);
});

test('J2 demo credentials start an email OTP challenge', async ({ page }) => {
  await page.setViewportSize(mobile);
  await page.goto('/login?next=%2Fdashboard');
  await page.getByLabel('Email').fill('admin@demo.evitrack.test');
  await page.locator('input[name="password"]').fill('Demo#Pass2026');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page).toHaveURL(/\/login\/otp$/);
  await expect(page.getByRole('heading', { name: 'Check your email' })).toBeVisible();
  await expect(page.getByText(/We sent a 6-digit code to/)).toBeVisible();
  await expect(page.getByRole('button', { name: /Resend code in/ })).toBeDisabled();
  await page.screenshot({ path: '../docs/screenshots/S2/otp-390.png', fullPage: true });
  await expectAccessible(page);

  const digits = page.getByRole('group', { name: 'One-time code' }).getByRole('textbox');
  await digits.first().focus();
  await page.keyboard.type('999999');
  await page.getByRole('button', { name: 'Verify' }).click();
  await expect(page.getByRole('alert')).toContainText('attempts left.');
});

test('login validates input and toggles password visibility', async ({ page }) => {
  await page.goto('/login?next=%2Fdashboard');
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  await page.screenshot({ path: '../docs/screenshots/S2/login-1440.png', fullPage: true });
  const password = page.getByRole('textbox', { name: /Password/ });
  await expect(password).toHaveAttribute('type', 'password');
  await page.getByRole('button', { name: 'Show password' }).click();
  await expect(password).toHaveAttribute('type', 'text');
  await expectAccessible(page);
});

test('unauthenticated dashboard redirects to login with next path', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login\?next=%2Fdashboard$/);
});

test('OTP and optional TOTP screens honor only the pending challenge', async ({ page }) => {
  await page.setViewportSize(mobile);
  await page.addInitScript(() => {
    sessionStorage.setItem('evitrack-auth-challenge', JSON.stringify({
      sentToMasked: 'a***@demo.evitrack.test',
      expiresAt: Date.now() + 600_000,
      resendAt: Date.now() + 30_000,
      next: '/dashboard',
    }));
  });

  await page.goto('/login/otp');
  await expect(page.getByRole('heading', { name: 'Check your email' })).toBeVisible();
  await expect(page.getByText('a***@demo.evitrack.test')).toBeVisible();
  const digits = page.getByRole('group', { name: 'One-time code' }).getByRole('textbox');
  await expect(digits).toHaveCount(6);
  await digits.first().focus();
  await page.keyboard.type('123456');
  await expect(page.getByRole('button', { name: 'Verify' })).toBeEnabled();
  await expect(page.getByRole('button', { name: /Resend code in/ })).toBeDisabled();
  await expectAccessible(page);

  await page.goto('/login/totp');
  await expect(page.getByRole('heading', { name: 'Authenticator code' })).toBeVisible();
  await expectAccessible(page);
});
