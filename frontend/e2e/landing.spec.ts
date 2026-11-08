import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

const desktop = { width: 1440, height: 900 };
const mobile = { width: 390, height: 844 };
const screenshotDir = '../docs/screenshots/S1';

async function seriousViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  return results.violations.filter((violation) => ['serious', 'critical'].includes(violation.impact ?? ''));
}

test.describe('landing page at 1440px', () => {
  test.use({ viewport: desktop, reducedMotion: 'reduce' });

  test('renders hero, sections and SEO tags without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1, name: 'Every case. Every file. Every handover. Proven.' })).toBeVisible();
    await expect(page).toHaveTitle(/EviTrack/);
    await expect(page.locator('meta[name="description"]')).toHaveAttribute('content', /SHA-256/);
    await expect(page.locator('meta[property="og:title"]')).toHaveAttribute('content', /EviTrack/);
    await expect(page.locator('meta[property="og:description"]')).toHaveAttribute('content', /SHA-256/);
    await expect(page.getByRole('heading', { name: 'Everything a case file needs' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Three steps from upload to proof' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Built for evidence that has to hold up' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Ready to stop losing evidence?' })).toBeVisible();
    await expect(page.getByText('This is a prototype.')).toBeVisible();
    await expect(page.locator('#features article')).toHaveCount(6);
    await expect(page.getByRole('region', { name: 'Trust highlights' }).getByRole('listitem')).toHaveCount(4);
    await expect(page.locator('.public-nav')).toHaveCSS('position', 'sticky');
    await expect(page.locator('.public-nav')).not.toHaveCSS('backdrop-filter', 'none');
    expect(errors).toEqual([]);
  });

  test('primary sign-in and request-access CTAs navigate', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Request access' }).click();
    await expect(page).toHaveURL(/\/register$/);
    await page.goto('/');
    await page.getByRole('main').getByRole('link', { name: 'Sign in' }).first().click();
    await expect(page).toHaveURL(/\/login$/);
  });

  test('feature and how-it-works links scroll to their sections', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('html')).toHaveCSS('scroll-behavior', 'auto');
    await page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Features' }).click();
    await expect(page).toHaveURL(/#features$/);
    await expect(page.getByRole('heading', { name: 'Everything a case file needs' })).toBeInViewport();
    await page.getByRole('link', { name: 'See how it works' }).click();
    await expect(page).toHaveURL(/#how-it-works$/);
    await expect(page.getByRole('heading', { name: 'Three steps from upload to proof' })).toBeInViewport();
  });

  test('feature cards lift on hover', async ({ page }) => {
    await page.goto('/');
    const card = page.locator('#features article').first();
    const initialTransform = await card.evaluate((element) => getComputedStyle(element).transform);
    await card.hover();
    await expect.poll(() => card.evaluate((element) => getComputedStyle(element).transform)).not.toBe(initialTransform);
  });

  test('has no serious or critical accessibility violations', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    expect(await seriousViolations(page)).toEqual([]);
  });

  test('saves light and dark screenshots', async ({ page, context }) => {
    await page.goto('/');
    await page.screenshot({ path: `${screenshotDir}/landing-1440-light.png`, fullPage: true });
    await context.addCookies([{ name: 'evitrack-theme', value: 'dark', url: new URL(page.url()).origin }]);
    await page.reload();
    await expect(page.locator('html')).toHaveClass(/dark/);
    await page.screenshot({ path: `${screenshotDir}/landing-1440-dark.png`, fullPage: true });
  });
});

test.describe('landing page at 390px', () => {
  test.use({ viewport: mobile, reducedMotion: 'reduce' });

  test('has no horizontal overflow or console errors and a working mobile menu', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/');
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual(mobile.width);

    const menuButton = page.getByRole('button', { name: 'Open menu' });
    await expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    await menuButton.click();
    await expect(page.getByRole('button', { name: 'Close menu' })).toHaveAttribute('aria-expanded', 'true');
    await page.locator('#site-menu').getByRole('link', { name: 'Security' }).click();
    await expect(page).toHaveURL(/#security$/);
    await expect(page.getByRole('button', { name: 'Open menu' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(mobile.width);
    expect(errors).toEqual([]);
  });

  test('has no serious or critical accessibility violations', async ({ page }) => {
    await page.goto('/');
    expect(await seriousViolations(page)).toEqual([]);
  });

  test('saves light and dark full-page screenshots', async ({ page, context }) => {
    await page.goto('/');
    await page.screenshot({ path: `${screenshotDir}/landing-390-light.png`, fullPage: true });
    await context.addCookies([{ name: 'evitrack-theme', value: 'dark', url: new URL(page.url()).origin }]);
    await page.reload();
    await expect(page.locator('html')).toHaveClass(/dark/);
    await page.screenshot({ path: `${screenshotDir}/landing-390-dark.png`, fullPage: true });
  });
});

test.describe('reveal on scroll', () => {
  test.use({ viewport: desktop });

  test('integrity illustration animates between verdicts', async ({ page }) => {
    await page.goto('/#how-it-works');
    const verified = page.locator('.verdict--verified');
    const modified = page.locator('.verdict--modified');
    await expect(verified).toBeVisible();
    await expect(modified).toBeVisible();
    expect(await verified.evaluate((element) => getComputedStyle(element).animationName)).not.toBe('none');
    expect(await modified.evaluate((element) => getComputedStyle(element).animationName)).not.toBe('none');
  });

  test('sections fade in when scrolled into view', async ({ page }) => {
    await page.goto('/');
    const heading = page.getByRole('heading', { name: 'Everything a case file needs' });
    const wrapper = heading.locator('xpath=ancestor::div[contains(@class,"transition")][1]');
    await expect(wrapper).toHaveClass(/opacity-0/);
    await heading.scrollIntoViewIfNeeded();
    await expect(wrapper).toHaveClass(/opacity-100/);
  });
});

test.describe('reduced motion', () => {
  test.use({ viewport: desktop, reducedMotion: 'reduce' });

  test('disables smooth scrolling, reveal delays, and verdict animation', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('html')).toHaveCSS('scroll-behavior', 'auto');
    const heading = page.getByRole('heading', { name: 'Everything a case file needs' });
    const wrapper = heading.locator('xpath=ancestor::div[contains(@class,"transition")][1]');
    await expect(wrapper).toHaveClass(/opacity-100/);
    await page.getByRole('heading', { name: 'Three steps from upload to proof' }).scrollIntoViewIfNeeded();
    expect(await page.locator('.verdict--verified').evaluate((element) => getComputedStyle(element).animationName)).toBe('none');
  });
});
