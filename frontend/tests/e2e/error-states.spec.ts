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

    await page.route('http://localhost:8000/api/analyze', async (route) => {
      await route.fulfill({ json: analyzeResponse, status: 200 });
    });

    await page.route(`http://localhost:8000/api/reports/${analyzeResponse.report_id}`, async (route) => {
      await route.fulfill({ status: 404, json: { detail: 'Report not found' } });
    });

    await page.goto('/');

    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await input.fill('https://github.com/test/repo');

    const generateButton = page.getByRole('button', { name: /generate|analyze|try/i }).first();
    
    // Click and wait for either navigation or error message
    await generateButton.click();
    await page.waitForTimeout(2000);
    
    // Should handle 404 error - check for error message on current page
    // Error might be on home page (if validation fails) or report page (if API fails)
    const errorFound = await page.getByText(/not found|error|failed/i).first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(errorFound).toBe(true);
  });

  test('should handle network error', async ({ page }) => {
    await page.route('http://localhost:8000/api/analyze', async (route) => {
      await route.abort('failed');
    });

    await page.goto('/');

    const input = page.getByPlaceholder(/github/i).or(page.getByLabel(/url/i)).first();
    await input.fill('https://github.com/test/repo');

    const generateButton = page.getByRole('button', { name: /generate|analyze|try/i }).first();
    await generateButton.click();
    
    // Wait a bit for error to appear
    await page.waitForTimeout(2000);
    
    // Should show error message - check for error on current page
    const errorFound = await page.getByText(/error|failed|network/i).first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(errorFound).toBe(true);
  });
});
