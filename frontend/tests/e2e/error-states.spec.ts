import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Error States', () => {
  test('should display error for failed report', async ({ page }) => {
    const failedReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/failed.json'), 'utf-8')
    );

    await page.route(`http://localhost:8000/api/reports/${failedReport.id}`, async (route) => {
      await route.fulfill({ json: failedReport, status: 200 });
    });

    await page.goto(`/reports/${failedReport.id}`);

    // Should show error message
    await expect(
      page.getByText(/error|failed|not found/i).first()
    ).toBeVisible({ timeout: 5000 });
  });

  test('should show retry button for failed report', async ({ page }) => {
    const failedReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/failed.json'), 'utf-8')
    );

    await page.route(`http://localhost:8000/api/reports/${failedReport.id}`, async (route) => {
      await route.fulfill({ json: failedReport, status: 200 });
    });

    await page.goto(`/reports/${failedReport.id}`);

    // Find retry button
    const retryButton = page.getByRole('button', { name: /retry|re-analyze/i }).first();
    await expect(retryButton).toBeVisible({ timeout: 5000 });
  });

  test('should handle API error gracefully', async ({ page }) => {
    const analyzeResponse = { report_id: '123e4567-e89b-12d3-a456-426614174999' };

    await page.route('**/api/analyze', async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes('/api/analyze')) {
        await route.fulfill({ json: analyzeResponse, status: 200 });
      } else {
        await route.continue();
      }
    });

    await page.route(`**/api/reports/${analyzeResponse.report_id}`, async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes(`/api/reports/${analyzeResponse.report_id}`)) {
        await route.fulfill({ status: 404, json: { detail: 'Report not found' } });
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
    await analyzeButton.click();
    
    // Wait for navigation to report page first
    await page.waitForURL(/\/reports\/.+/, { timeout: 10000 }).catch(() => {
      // If navigation doesn't happen, check for error on home page
    });
    
    // Wait a bit for error to appear
    await page.waitForTimeout(2000);
    
    // Should show error message - check for error alert or error text
    const errorFound = await page.getByRole('alert').or(page.getByText(/not found|error|failed/i)).first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(errorFound).toBe(true);
  });

  test('should handle network error', async ({ page }) => {
    await page.route('**/api/analyze', async (route) => {
      if (route.request().url().includes('localhost:8000') || route.request().url().includes('/api/analyze')) {
        await route.abort('failed');
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
    await analyzeButton.click();

    // Wait a bit for error to appear (should stay on home page)
    await page.waitForTimeout(3000);
    
    // Should show error message in the alert - check for error alert or error text
    const errorFound = await page.getByRole('alert').or(page.getByText(/error|failed|request/i)).first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(errorFound).toBe(true);
  });
});
