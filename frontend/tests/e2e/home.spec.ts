import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load home page and display hero section', async ({ page }) => {
    await page.goto('/');
    
    // Check hero section is visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    
    // Check for key elements
    await expect(page.getByText(/repository readiness/i).first()).toBeVisible();
  });

  test('should display features section', async ({ page }) => {
    await page.goto('/');
    
    // Scroll to features or check they're visible
    const featuresHeading = page.getByRole('heading', { name: /what we check/i }).or(
      page.getByRole('heading', { name: /features/i })
    );
    await expect(featuresHeading.first()).toBeVisible({ timeout: 5000 });
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
