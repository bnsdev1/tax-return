import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page }) => {
  await page.goto('/');
  
  await expect(page.locator('h1')).toContainText('FastAPI + React Monorepo');
  await expect(page.locator('text=React + Vite + TypeScript')).toBeVisible();
});