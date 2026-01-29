import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Visual Regression', () => {
  test.skip('home page visual snapshot', async ({ page }) => {
    // Skip visual tests in CI - they require manual snapshot approval
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Take screenshot
    await expect(page).toHaveScreenshot('home-page.png', {
      fullPage: true,
      maxDiffPixels: 100, // Allow small differences
    });
  });

  test.skip('report page visual snapshot', async ({ page }) => {
    const doneReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/done.json'), 'utf-8')
    );

    await page.route(`http://localhost:8000/api/reports/${doneReport.id}`, async (route) => {
      await route.fulfill({ json: doneReport, status: 200 });
    });

    await page.goto(`/reports/${doneReport.id}`);
    
    // Wait for report to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Extra wait for animations
    
    // Take screenshot
    await expect(page).toHaveScreenshot('report-page.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });
});
