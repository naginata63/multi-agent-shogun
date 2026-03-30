# Cloudflare Pages セットアップ手順

genai_viewerの静的サイトをCloudflare Pagesで公開するための手順。

## 前提条件

- Cloudflareアカウント（無料プランで可）
- Node.js 18以上

## セットアップ手順

### 1. Cloudflareアカウント作成

https://dash.cloudflare.com/sign-up にアクセスして無料アカウントを作成。

### 2. wrangler CLIのインストール

```bash
npm install -g wrangler
```

### 3. Cloudflareへのログイン

```bash
wrangler login
```

ブラウザが開くので、Cloudflareアカウントでログインして認証を許可する。

### 4. Pagesプロジェクトの作成

```bash
npx wrangler pages project create genai-daily
```

プロンプトで:
- 「Production branch」には `main` を入力

### 5. 初回デプロイ（手動）

```bash
cd /home/murakami/multi-agent-shogun
REPO_ROOT=$(pwd) bash scripts/genai_build_static.sh
npx wrangler pages deploy dist/ --project-name=genai-daily
```

デプロイ完了後、以下のようなURLが表示される:
```
✨ Deployment complete! Take a look over at https://genai-daily.pages.dev
```

### 6. 以降は自動デプロイ

`genai_daily_report.sh` の末尾に組み込み済みのため、毎日のレポート生成後に自動でビルド＆デプロイされる。

## ディレクトリ構成

```
dist/              ← 静的サイト出力先（git管理外）
├── index.html     ← 全データ埋め込み済みHTML（~200KB）
├── style.css      ← スタイルシート
└── app.js         ← 静的版JavaScript（fetch不要）
```

## 動作確認

ローカルで確認する場合:

```bash
# Pythonの簡易HTTPサーバーで確認
cd /home/murakami/multi-agent-shogun/dist
python3 -m http.server 8581
# ブラウザで http://localhost:8581 を開く
```

または直接ファイルをブラウザで開く（`file://` で動作）:
```bash
xdg-open dist/index.html  # Linux
open dist/index.html       # Mac
```

## 注意事項

- `dist/` は `.gitignore` 対象外なので、必要に応じて追加すること
- 静的版はフィードバックボタンなし（バックエンド不要）
- 検索はクライアントサイドで全データを検索（最大50件）
- wrangler未設定の場合はビルドのみ実行されデプロイはスキップ（ログにWARNが出る）
