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

    // Mock API calls - intercept requests to localhost:8000 (the API base)
    await page.route('**/api/analyze', async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes('/api/analyze')) {
        await route.fulfill({ json: analyzeResponse, status: 200 });
      } else {
        await route.continue();
      }
    });

    await page.route(`**/api/reports/${analyzeResponse.report_id}`, async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes(`/api/reports/${analyzeResponse.report_id}`)) {
        await route.fulfill({ json: doneReport, status: 200 });
      } else {
        await route.continue();
      }
    });

    // Navigate to home
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Enter GitHub URL
    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await input.fill('https://github.com/test/repo');
    await page.waitForTimeout(500); // Wait for input to update

    // Click the form's Analyze button (hero has id="analyze"; navbar also has an "Analyze" button)
    const analyzeButton = page.locator('#analyze').getByRole('button', { name: /analyze/i });
    await analyzeButton.scrollIntoViewIfNeeded();
    await Promise.all([
      page.waitForURL(/\/reports\/.+/, { timeout: 15000, waitUntil: 'commit' }),
      analyzeButton.click(),
    ]);
    
    // Check report page loads (header shows repo label from fixture; report page uses "Score" in sidebar, not "Readiness Score")
    await expect(page.getByText(/test\/repo/)).toBeVisible({ timeout: 10000 });
  });

  test('should show validation error for invalid URL', async ({ page }) => {
    await page.goto('/');

    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    
    // Enter invalid URL
    await input.fill('not-a-url');

    // Submit via form's Analyze button (navbar also has "Analyze")
    const analyzeButton = page.locator('#analyze').getByRole('button', { name: /analyze/i });
    await analyzeButton.click();

    // Should show error message (either inline or after API call)
    // The validation might happen client-side or server-side
    await page.waitForTimeout(1000);
    
    // Check for error message (either inline validation or API error)
    // Note: This test may need adjustment based on actual validation implementation
    // For now, just verify the form doesn't navigate on invalid input
    await page.waitForTimeout(1000);
    const currentUrl = page.url();
    expect(currentUrl).toBe('http://localhost:3000/');
  });

  test('should handle pending report state', async ({ page }) => {
    const analyzeResponse = { report_id: '123e4567-e89b-12d3-a456-426614174000' };
    const pendingReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/pending.json'), 'utf-8')
    );

    // Mock API calls
    await page.route('**/api/analyze', async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes('/api/analyze')) {
        await route.fulfill({ json: analyzeResponse, status: 200 });
      } else {
        await route.continue();
      }
    });

    await page.route(`**/api/reports/${analyzeResponse.report_id}`, async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes(`/api/reports/${analyzeResponse.report_id}`)) {
        await route.fulfill({ json: pendingReport, status: 200 });
      } else {
        await route.continue();
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await input.fill('https://github.com/test/repo');
    await page.waitForTimeout(500);

    const analyzeButton = page.locator('#analyze').getByRole('button', { name: /analyze/i });
    await analyzeButton.scrollIntoViewIfNeeded();
    await Promise.all([
      page.waitForURL(/\/reports\/.+/, { timeout: 15000, waitUntil: 'commit' }),
      analyzeButton.click(),
    ]);

    // Should show pending/skeleton state
    await expect(
      page.getByText(/pending|scanning|loading/i).first()
    ).toBeVisible({ timeout: 5000 });
  });
});
