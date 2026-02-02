const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

const BASE_URL = process.env.ACADEMY_BASE_URL ?? 'https://dashadmin.tinybots.academy';
const STORAGE_STATE_PATH =
  process.env.ACADEMY_STORAGE_STATE_PATH ?? path.join(os.homedir(), '.playwright', 'academy.storageState.json');

async function main() {
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(
      `storageState not found at ${STORAGE_STATE_PATH}. Run: pnpm run seed:academy (manual login) to generate it.`,
    );
  }

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
  const page = await context.newPage();

  await page.goto(`${BASE_URL}/overview/`, { waitUntil: 'domcontentloaded' });
  console.log(`Opened: ${page.url()}`);
  console.log('Press Ctrl+C to close');

  await new Promise(() => {});
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});

