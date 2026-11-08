import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('design system route renders accessibly at desktop and mobile widths', async ({ page }) => {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto('/design');
    await expect(page.getByRole('heading', { name: 'Design system' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Primary action' })).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((violation) => ['serious', 'critical'].includes(violation.impact ?? ''))).toEqual([]);
  }
});
