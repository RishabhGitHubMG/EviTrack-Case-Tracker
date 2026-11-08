import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('design system route is accessible in both themes at desktop and mobile widths', async ({ page }) => {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto('/design');
    await page.context().addCookies([{ name: 'evitrack-theme', value: 'light', url: new URL(page.url()).origin }]);
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Design system' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Primary action' })).toBeVisible();

    for (const theme of ['light', 'dark'] as const) {
      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations.filter((violation) => ['serious', 'critical'].includes(violation.impact ?? ''))).toEqual([]);
      if (theme === 'light') {
        await page.getByRole('button', { name: 'Switch to dark mode' }).click();
        await expect(page.locator('html')).toHaveClass(/dark/);
      }
    }
  }
});

test('applies saved theme before the React bundle loads', async ({ page }) => {
  await page.addInitScript(() => {
    document.cookie = 'evitrack-theme=dark; Path=/; SameSite=Lax';
  });
  await page.route('**/src/main.tsx*', (route) => route.abort());
  await page.goto('/design');
  await expect(page.locator('html')).toHaveClass(/dark/);
});

test('design system actions work and theme persists after reload', async ({ page }) => {
  await page.goto('/design');
  await page.getByRole('button', { name: 'Show toast' }).click();
  await expect(page.getByText('Example notification', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Copy value' }).last()).toBeVisible();

  await page.getByRole('button', { name: 'Open confirmation' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog.getByRole('heading', { name: 'Discard changes?' })).toBeVisible();
  await dialog.getByRole('button', { name: 'Confirm' }).click();
  await expect(dialog).not.toBeVisible();

  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await expect(page.locator('html')).toHaveClass(/dark/);
  await page.reload();
  await expect(page.locator('html')).toHaveClass(/dark/);
});
