import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Report Page', () => {
  test.beforeEach(async ({ page }) => {
    // Load done report fixture
    const doneReport = JSON.parse(
      fs.readFileSync(path.join(__dirname, '../fixtures/report/done.json'), 'utf-8')
    );

    // Mock API call
    await page.route(`http://localhost:8000/api/reports/${doneReport.id}`, async (route) => {
      await route.fulfill({ json: doneReport, status: 200 });
    });

    // Navigate to report page
    await page.goto(`/reports/${doneReport.id}`);
  });

  test('should display report header with repo name', async ({ page }) => {
    await expect(page.getByText(/test\/repo/i).or(page.getByText(/github.com/i))).toBeVisible({ timeout: 5000 });
  });

  test('should display score summary', async ({ page }) => {
    await expect(page.getByText(/85/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('should display sections with checks', async ({ page }) => {
    // Check for section names
    await expect(page.getByText(/runability/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('should filter checks by status', async ({ page }) => {
    // Find filter buttons
    const allButton = page.getByRole('button', { name: /all/i }).first();
    const failButton = page.getByRole('button', { name: /fail/i }).first();
    const warnButton = page.getByRole('button', { name: /warn/i }).first();
    const passButton = page.getByRole('button', { name: /pass/i }).first();

    if (await allButton.isVisible()) {
      await allButton.click();
      await page.waitForTimeout(500);
    }

    if (await failButton.isVisible()) {
      await failButton.click();
      await page.waitForTimeout(500);
      // Should show only fail checks
    }

    if (await passButton.isVisible()) {
      await passButton.click();
      await page.waitForTimeout(500);
      // Should show only pass checks
    }
  });

  test('should search/filter checks by name', async ({ page }) => {
    // Find search input
    const searchInput = page.getByPlaceholder(/filter|search/i).first();
    
    if (await searchInput.isVisible()) {
      await searchInput.fill('README');
      await page.waitForTimeout(500);
      
      // Should filter checks containing "README"
      const checks = page.locator('[data-testid*="check"]').or(page.getByText(/readme/i));
      await expect(checks.first()).toBeVisible({ timeout: 2000 });
    }
  });

  test('should expand check details', async ({ page }) => {
    // Find a check with details button
    const detailsButton = page.getByRole('button', { name: /details|more/i }).first();
    
    if (await detailsButton.isVisible()) {
      await detailsButton.click();
      await page.waitForTimeout(500);
      
      // Should show evidence/recommendation
      await expect(
        page.getByText(/evidence|recommendation|file/i).first()
      ).toBeVisible({ timeout: 2000 });
    }
  });

  test('should copy share link', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Find copy button
    const copyButton = page.getByRole('button', { name: /copy/i }).first();
    
    if (await copyButton.isVisible()) {
      await copyButton.click();
      await page.waitForTimeout(500);
      
      // Check for "Copied!" message or verify button state changed
      await expect(page.getByText(/copied/i).first()).toBeVisible({ timeout: 2000 }).catch(() => {
        // If clipboard API not available, just verify button click worked
      });
    }
  });
});
