import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load home page and display hero section', async ({ page }) => {
    await page.goto('/');

    // Hero h1
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // Hero subhead mentions the static-analysis pillars
    await expect(
      page.getByText(/static analysis across runability/i).first()
    ).toBeVisible();
  });

  test('should display features section', async ({ page }) => {
    await page.goto('/');

    // The features section uses an eyebrow ("What we check") above an h2.
    // Match either the eyebrow text or the h2 title.
    const featuresMarker = page
      .getByText(/what we check/i)
      .or(page.getByRole('heading', { name: /six categories/i }));
    await expect(featuresMarker.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display example preview section', async ({ page }) => {
    await page.goto('/');
    
    // Look for example section
    const exampleSection = page.getByText(/example/i).first();
    await expect(exampleSection).toBeVisible({ timeout: 5000 });
  });

  test('should display get started section with input', async ({ page }) => {
    await page.goto('/');
    
    // Find the GitHub URL input
    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await expect(input).toBeVisible({ timeout: 5000 });
  });

  test('should display how it works section', async ({ page }) => {
    await page.goto('/');
    
    // Look for how it works heading
    const howItWorks = page.getByText(/how it works/i).first();
    await expect(howItWorks).toBeVisible({ timeout: 5000 });
  });
});
