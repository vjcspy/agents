import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const STORAGE_STATE_PATH =
  process.env.ACADEMY_STORAGE_STATE_PATH ??
  path.join(os.homedir(), '.playwright', 'academy.storageState.json');

test('academy dashboard logs in via storageState', async ({ page }) => {
  test.skip(!fs.existsSync(STORAGE_STATE_PATH), 'Run pnpm run seed:academy to generate storageState');

  await page.goto('/overview/', { waitUntil: 'domcontentloaded' });

  await expect(page).not.toHaveURL(/\/login/i, { timeout: 30_000 });

  const overviewSearch = page.getByPlaceholder(/search for relation or serial/i);
  await expect(overviewSearch).toBeVisible({ timeout: 15_000 });

  if (process.env.ACADEMY_MANUAL === '1') {
    await page.pause();
  }
});
