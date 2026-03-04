const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1evWLOWIBbfvTSDTgUKpdPXBIpdDZmJKK_V0tGACoiS4/edit';
const screenshotsDir = 'projects/ec_description_tool/screenshots';
const CODE_GS_PATH = 'projects/ec_description_tool/Code.gs';

async function waitForLogin(page) {
  if (page.url().includes('accounts.google.com') || page.url().includes('signin')) {
    console.log('=== Googleログインが必要です。ブラウザでログインしてください（最大5分）===');
    await page.waitForURL(url => !url.includes('accounts.google.com'), { timeout: 300000 });
  }
}

(async () => {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const profileDir = path.join(process.env.HOME, '.cache/ms-playwright/google-profile');
  const browser = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 1280, height: 900 }
  });

  // === スプレッドシートを開く ===
  const sheetPage = await browser.newPage();
  await sheetPage.goto(SHEET_URL, { waitUntil: 'load', timeout: 60000 });
  await waitForLogin(sheetPage);
  await sheetPage.waitForTimeout(4000);

  // === GASエディタを開く: 拡張機能 > Apps Script ===
  console.log('GASエディタを開く...');
  let gasPage = null;
  try {
    // 「拡張機能」メニューをクリック
    await sheetPage.click('#docs-extensions-menu');
    await sheetPage.waitForTimeout(1000);
    // 「Apps Script」をクリック → 新タブ
    const [newPage] = await Promise.all([
      browser.waitForEvent('page'),
      sheetPage.click('.goog-menuitem:has-text("Apps Script")')
    ]);
    await newPage.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await newPage.waitForTimeout(5000);  // GASエディタ初期化待ち
    gasPage = newPage;
    console.log('GASエディタ開いた:', gasPage.url());
  } catch(e) {
    throw new Error('GASエディタを開けませんでした: ' + e.message);
  }

  // === 01: GASエディタのスクショ（デプロイ前） ===
  await gasPage.screenshot({ path: `${screenshotsDir}/01_gas_editor.png` });
  console.log('01: GASエディタ撮影完了');

  // === Code.gs をデプロイ ===
  console.log('Code.gsをデプロイ中...');
  const codeContent = fs.readFileSync(CODE_GS_PATH, 'utf-8');

  try {
    // エディタの既存コードを選択して置換
    // CodeMirrorエディタの場合: .CodeMirror-code をクリックしてCtrl+A
    await gasPage.click('.CodeMirror-code, .monaco-editor, [role="textbox"]');
    await gasPage.waitForTimeout(500);
    await gasPage.keyboard.press('Control+a');
    await gasPage.waitForTimeout(200);

    // クリップボード経由でペースト
    await gasPage.evaluate((text) => {
      return navigator.clipboard.writeText(text).catch(() => {
        // フォールバック: document.execCommand
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      });
    }, codeContent);

    await gasPage.keyboard.press('Control+v');
    await gasPage.waitForTimeout(1000);

    // 保存 (Ctrl+S)
    await gasPage.keyboard.press('Control+s');
    await gasPage.waitForTimeout(3000);
    console.log('Code.gsデプロイ・保存完了');
  } catch(e) {
    throw new Error('Code.gsデプロイ失敗: ' + e.message);
  }

  // GASエディタを閉じてスプレッドシートに戻る
  await gasPage.close();
  await sheetPage.bringToFront();

  // === スプレッドシートをリロードしてカスタムメニューを反映 ===
  console.log('スプレッドシートリロード中...');
  await sheetPage.reload({ waitUntil: 'load', timeout: 30000 });
  await sheetPage.waitForTimeout(6000);  // onOpen実行待ち

  // === 02: カスタムメニューボタン確認（メニュー未開状態のメニューバー） ===
  console.log('02: カスタムメニューボタン確認...');
  // 「🛒 EC商品説明AI」メニューボタンを探す（#docs-menubar内）
  const customMenuBtn = sheetPage.locator('#docs-menubar .goog-control').filter({ hasText: 'EC商品説明' }).first();
  if (await customMenuBtn.count() === 0) {
    throw new Error('02: カスタムメニュー「EC商品説明AI」が見つかりません。Code.gsデプロイを確認してください。');
  }
  // メニューバーにカスタムメニューが表示された状態（未開）のスクショ
  await sheetPage.screenshot({ path: `${screenshotsDir}/02_menu_open.png` });
  console.log('02: メニューバー（カスタムメニュー付き）撮影完了');

  // === 03: 「🚀 セットアップ」メニュー項目 ===
  console.log('03: セットアップメニュー項目撮影...');
  await customMenuBtn.click();
  await sheetPage.waitForTimeout(1500);
  const setupLocator = sheetPage.locator('.goog-menuitem').filter({ hasText: 'セットアップ' }).first();
  if (await setupLocator.count() > 0) {
    await sheetPage.screenshot({ path: `${screenshotsDir}/03_setup_menu.png` });
    console.log('03: セットアップメニュー撮影完了');
  } else {
    throw new Error('03: セットアップメニュー項目が見つかりません');
  }

  // === 04: セットアップ実行後の状態（認証ポップアップ or APIダイアログ） ===
  console.log('04: セットアップ実行してダイアログ撮影...');
  await setupLocator.click();
  await sheetPage.waitForTimeout(5000);  // GASダイアログ（iframe）or認証ポップアップ出現待ち

  // 現在の状態をスクショ（何が出てきたか記録）
  await sheetPage.screenshot({ path: `${screenshotsDir}/04_api_dialog.png` });
  console.log('04: セットアップ後状態撮影完了');

  // GAS iframeダイアログがあれば入力して進む
  try {
    const dialogFrame = sheetPage.frameLocator('iframe[src*="docs.google.com"], iframe[src*="script.google.com"]').last();
    const inputField = dialogFrame.locator('input[type="text"], input[type="password"]').first();
    if (await inputField.count({ timeout: 2000 }) > 0) {
      await inputField.fill('YOUR_GEMINI_API_KEY_HERE');
      const okBtn = dialogFrame.locator('button:has-text("OK"), button:has-text("はい")').first();
      if (await okBtn.count() > 0) await okBtn.click();
      await sheetPage.waitForTimeout(5000);
    }
  } catch(e) {
    console.log('iframeダイアログなし（スキップ）');
  }

  // ポップアップが開いていれば閉じる
  try {
    const alertOk = sheetPage.locator('.docs-dialog-ok-button, button:has-text("OK"), button:has-text("閉じる")').first();
    if (await alertOk.count({ timeout: 1000 }) > 0) {
      await alertOk.click();
      await sheetPage.waitForTimeout(2000);
    }
  } catch(e) {}

  // === 05: セットアップ後の「設定」シート確認 ===
  // 設定シートタブに移動して状態確認
  console.log('05: 設定シート撮影...');
  try {
    const settingTab = sheetPage.locator('[id*="sheet-tab"]').filter({ hasText: '設定' }).first();
    if (await settingTab.count({ timeout: 2000 }) > 0) {
      await settingTab.click();
      await sheetPage.waitForTimeout(1500);
    }
  } catch(e) {}
  await sheetPage.screenshot({ path: `${screenshotsDir}/05_setup_complete.png` });
  console.log('05: セットアップ完了画面撮影');

  // === 06: メインシートに戻って生成メニュー確認 ===
  console.log('06: メインシート+生成メニュー撮影...');
  try {
    const mainTab = sheetPage.locator('[id*="sheet-tab"]').filter({ hasText: 'メイン' }).first();
    if (await mainTab.count({ timeout: 2000 }) > 0) {
      await mainTab.click();
      await sheetPage.waitForTimeout(1500);
    }
  } catch(e) {}
  // EC商品説明AIメニューから生成メニューを開いてスクショ
  // butterbar（通知バナー）が消えるまで待つ（最大15秒）
  try {
    await sheetPage.waitForSelector('#docs-butterbar-container:not(:has(.docs-butterbar-link))', { timeout: 15000 });
  } catch(e) {
    console.log('butterbar消えず - 強制クリック試行');
  }

  const customMenuBtn2 = sheetPage.locator('#docs-menubar .goog-control').filter({ hasText: 'EC商品説明' }).first();
  if (await customMenuBtn2.count() > 0) {
    try {
      await customMenuBtn2.click({ force: true, timeout: 5000 });
      await sheetPage.waitForTimeout(1500);
    } catch(e) {
      console.log('06: メニューボタンクリック失敗 - スクショのみ:', e.message.substring(0, 100));
    }
  }
  await sheetPage.screenshot({ path: `${screenshotsDir}/06_generate_result.png` });
  console.log('06: 生成メニュー撮影完了');

  await sheetPage.keyboard.press('Escape');

  await browser.close();
  console.log('=== 全スクショ撮影完了 ===');
})();
