# GAS Tool Screenshot Capture

Google Spreadsheet + GAS ツールのセットアップフロー 7 枚を Playwright headed で撮影する汎用スクリプト。

## 前提条件

- Playwright + Chromium インストール済み
- `~/.cache/ms-playwright/google-profile` に Google ログイン済みプロファイルが存在すること
- DISPLAY=:0 が利用可能 (headless=False)

## インストール

```bash
pip install playwright
playwright install chromium
```

## 使い方

```bash
# review_reply_tool
pkill -f google-chrome 2>/dev/null; sleep 3
DISPLAY=:0 python3 scripts/playwright/capture_gas_tool.py \
  --tool review_reply_tool \
  --url "https://docs.google.com/spreadsheets/d/1ncAq0HSmm7Cm1FKb5tNKy3nPlnM68i7sCJB_9-gnfEo/edit" \
  --menu "⭐ 口コミ返信AI"

# sns_post_tool
DISPLAY=:0 python3 scripts/playwright/capture_gas_tool.py \
  --tool sns_post_tool \
  --url "https://docs.google.com/spreadsheets/d/1ISqPne1lptEvlnbU0qzg4AkL2n2Eqio0AGdEPTdWofg/edit" \
  --menu "📱 SNS投稿AI"

# email_reply_tool
DISPLAY=:0 python3 scripts/playwright/capture_gas_tool.py \
  --tool email_reply_tool \
  --url "https://docs.google.com/spreadsheets/d/1ipLh5P-5lZdW3bH2I39cPf0QZVKgdYCFVC_In_jOvkM/edit" \
  --menu "📧 メール返信AI"

# ec_description_tool
DISPLAY=:0 python3 scripts/playwright/capture_gas_tool.py \
  --tool ec_description_tool \
  --url "https://docs.google.com/spreadsheets/d/.../edit" \
  --menu "🛒 EC商品説明AI"
```

出力先を変更したい場合は `--output-dir /path/to/dir` を追加。

## 撮影される 7 枚

| ファイル | 内容 |
|---------|------|
| 01_gas_editor.png | Apps Script エディタ |
| 02_menu_open.png | カスタムメニュー展開 |
| 03_setup_menu.png | セットアップ項目ハイライト |
| 04_api_dialog.png | API キー入力ダイアログ |
| 04b_settings_sheet.png | 設定シートタブ |
| 05_setup_complete.png | セットアップ完了ダイアログ |
| 06_generate_result.png | 生成実行結果 |

## 既知の制限

- **01_gas_editor.png**: 「拡張機能」メニューから Apps Script を開くが、GAS タブが既に開いている場合は `expect_page` がタイムアウトする。フォールバックとしてスプレッドシートの現在状態を撮影する。
- **カスタムメニュー不可視**: ページ読み込み直後はカスタムメニュー (GAS 初回実行) が表示されないことがある。10 秒待機後に再実行すること。
- Chrome LOCK: スクリプト冒頭で `pkill -f google-chrome` + `sleep 3` を実行済み。それでも失敗する場合は `rm -f ~/.config/google-chrome/SingletonLock` を試すこと。
