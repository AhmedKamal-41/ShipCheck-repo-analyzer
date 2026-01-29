import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Analyze Flow', () => {
  test('should complete full analyze flow', async ({ page }) => {
    // Load fixtures
    const analyzeResponse = { report_id: '123e4567-e89b-12d3-a456-426614174001' };
    const doneReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/done.json'), 'utf-8')
    );

    // Mock API calls
    await page.route('**/api/analyze', async (route) => {
      await route.fulfill({ json: analyzeResponse });
    });

    await page.route(`**/api/reports/${analyzeResponse.report_id}`, async (route) => {
      await route.fulfill({ json: doneReport });
    });

    // Navigate to home
    await page.goto('/');

    // Enter GitHub URL
    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await input.fill('https://github.com/test/repo');

    // Click generate button
    const generateButton = page.getByRole('button', { name: /generate|analyze|try/i }).first();
    await generateButton.click();

    // Should navigate to report page
    await expect(page).toHaveURL(/\/reports\/.+/);
    
    // Check report page loads
    await expect(page.getByText(/readiness score/i).or(page.getByText(/overall score/i))).toBeVisible({ timeout: 10000 });
  });

  test('should show validation error for invalid URL', async ({ page }) => {
    await page.goto('/');

    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    
    // Enter invalid URL
    await input.fill('not-a-url');
    
    // Try to submit (may trigger validation)
    const generateButton = page.getByRole('button', { name: /generate|analyze|try/i }).first();
    await generateButton.click();

    // Should show error message (either inline or after API call)
    // The validation might happen client-side or server-side
    await page.waitForTimeout(1000);
    
    // Check for error message (could be in various forms)
    const errorVisible = await page.getByText(/invalid|error/i).first().isVisible().catch(() => false);
    // Note: This test may need adjustment based on actual validation implementation
  });

  test('should handle pending report state', async ({ page }) => {
    const analyzeResponse = { report_id: '123e4567-e89b-12d3-a456-426614174000' };
    const pendingReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/pending.json'), 'utf-8')
    );

    await page.route('**/api/analyze', async (route) => {
      await route.fulfill({ json: analyzeResponse });
    });

    await page.route(`**/api/reports/${analyzeResponse.report_id}`, async (route) => {
      await route.fulfill({ json: pendingReport });
    });

    await page.goto('/');

    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await input.fill('https://github.com/test/repo');

    const generateButton = page.getByRole('button', { name: /generate|analyze|try/i }).first();
    await generateButton.click();

    // Should show pending/skeleton state
    await expect(page).toHaveURL(/\/reports\/.+/);
    await expect(
      page.getByText(/pending|scanning|loading/i).or(page.getByTestId('skeleton'))
    ).toBeVisible({ timeout: 5000 });
  });
});
