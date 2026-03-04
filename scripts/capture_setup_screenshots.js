const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1evWLOWIBbfvTSDTgUKpdPXBIpdDZmJKK_V0tGACoiS4/edit';
const screenshotsDir = 'projects/ec_description_tool/screenshots';

async function waitForLogin(page) {
  if (page.url().includes('accounts.google.com') || page.url().includes('signin')) {
    console.log('=== Googleログインが必要です。ブラウザでログインしてください（最大5分）===');
    await page.waitForURL(/google\.com\/(?!accounts)/, { timeout: 300000 });
  }
}

(async () => {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const profileDir = path.join(process.env.HOME, '.cache/ms-playwright/google-profile');
  const browser = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 1280, height: 900 }
  });

  // === 01: GASエディタ ===
  console.log('01: GASエディタ撮影...');
  const gasPage = await browser.newPage();
  await gasPage.goto(SHEET_URL, { waitUntil: 'load', timeout: 60000 });
  await waitForLogin(gasPage);
  await gasPage.waitForTimeout(5000);

  // 拡張機能メニュークリック
  const extMenu = gasPage.locator('.menu-button:has-text("拡張機能")').first();
  if (await extMenu.count() === 0) {
    throw new Error('01: 拡張機能メニュー未発見 - 処理を停止します');
  }
  await extMenu.click();
  await gasPage.waitForTimeout(1000);

  // Apps Script クリック
  const appsScriptItem = gasPage.locator('.goog-menuitem:has-text("Apps Script")').first();
  if (await appsScriptItem.count() === 0) {
    throw new Error('01: Apps Scriptメニュー項目未発見 - 処理を停止します');
  }

  const [newPage] = await Promise.all([
    browser.waitForEvent('page'),
    appsScriptItem.click()
  ]);
  await newPage.waitForLoadState('load', { timeout: 30000 });
  await newPage.waitForTimeout(5000);
  await newPage.screenshot({ path: `${screenshotsDir}/01_gas_editor.png` });
  console.log('01: GASエディタ撮影完了');
  await newPage.close();

  // スプレッドシートに戻る
  await gasPage.bringToFront();
  await gasPage.waitForTimeout(2000);

  // === 02: カスタムメニュー展開 ===
  console.log('02: カスタムメニュー撮影...');
  await gasPage.reload({ waitUntil: 'load', timeout: 30000 });
  await gasPage.waitForTimeout(5000);

  // カスタムメニュー名を確認（AI生成 or EC商品説明AI）
  const customMenuSelectors = [
    '.menu-button:has-text("AI生成")',
    '.menu-button:has-text("EC商品説明")',
    '.menu-button:has-text("🛒")'
  ];
  let customMenu = null;
  for (const sel of customMenuSelectors) {
    const el = gasPage.locator(sel).first();
    if (await el.count() > 0) {
      customMenu = el;
      console.log('02: カスタムメニュー発見:', sel);
      break;
    }
  }
  if (!customMenu) {
    throw new Error('02: カスタムメニュー未発見 (AI生成/EC商品説明) - 処理を停止します');
  }
  await customMenu.click();
  await gasPage.waitForTimeout(1500);
  await gasPage.screenshot({ path: `${screenshotsDir}/02_menu_open.png` });
  console.log('02: メニュー展開撮影完了');

  // === 03: セットアップメニュー項目 ===
  console.log('03: セットアップメニュー項目撮影...');
  // 現在表示されているドロップダウン内のセットアップ項目を探す
  const setupItem = gasPage.locator('.goog-menuitem:has-text("セットアップ")').first();
  if (await setupItem.count() === 0) {
    throw new Error('03: セットアップメニュー項目未発見（ライブGASに存在しない）- 処理を停止します');
  }
  await gasPage.screenshot({ path: `${screenshotsDir}/03_setup_menu.png` });
  console.log('03: セットアップメニュー撮影完了');

  // === 04: APIキー入力ダイアログ ===
  console.log('04: セットアップ実行・ダイアログ撮影...');
  await setupItem.click();
  await gasPage.waitForTimeout(5000);
  await gasPage.screenshot({ path: `${screenshotsDir}/04_api_dialog.png` });

  // GAS iframeダイアログの入力欄を探す
  const dialogFrame = gasPage.frameLocator('iframe').last();
  const inputField = dialogFrame.locator('input[type="text"]');
  if (await inputField.count() === 0) {
    throw new Error('04: GAS iframeダイアログ入力欄未発見 - 処理を停止します');
  }
  await inputField.fill('YOUR_GEMINI_API_KEY_HERE');
  await gasPage.screenshot({ path: `${screenshotsDir}/04_api_dialog.png` });
  console.log('04: APIダイアログ撮影完了');

  const okBtn = dialogFrame.locator('button:has-text("OK"), button:has-text("保存")').first();
  if (await okBtn.count() > 0) {
    await okBtn.click();
  }

  // === 05: セットアップ完了 ===
  console.log('05: セットアップ完了画面撮影...');
  await gasPage.waitForTimeout(5000);
  await gasPage.screenshot({ path: `${screenshotsDir}/05_setup_complete.png` });
  console.log('05: セットアップ完了画面撮影完了');

  // === 06: AI生成結果 ===
  console.log('06: AI生成結果撮影...');
  await gasPage.waitForTimeout(2000);
  await gasPage.screenshot({ path: `${screenshotsDir}/06_generate_result.png` });
  console.log('06: 生成結果撮影完了');

  await browser.close();
  console.log('=== 全スクショ撮影完了 ===');
})();
