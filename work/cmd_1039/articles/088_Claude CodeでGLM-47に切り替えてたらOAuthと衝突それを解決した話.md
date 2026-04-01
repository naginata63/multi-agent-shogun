# Claude CodeでGLM-47に切り替えてたらOAuthと衝突それを解決した話

**URL**: https://note.com/sasuu/n/n6172cbaa42bd

---

Claude CodeでGLM-4.7に切り替えてたら OAuthと衝突。それを解決した話

Claude CodeでGLM-4.7に切り替えてたらOAuth と衝突して解決した話

LLM切り替えのヘッダー画像

Claude Codeが勝手にアップデートされたら、今まで動いていたGLM-4.7への接続が突然壊れた！ 「OAuthとAPIキーの両方が設定されてます」とエラーが出る。

3時間格闘した結果、プロキシサーバー＋別HOME＋スクリプト起動の3点セットで解決しました。

同じ問題に遭遇した人向けに、非エンジニアでもわかるたとえ話と、技術情報をまとめました。

sasuu｜非エンジニアのAI活用術 2026年2月11日 22:32

そもそも何が起きたのか

OAuthとAPIキーの衝突

Claude Codeというツールは、通常Anthropic社のAI（Claude）を使って動く。でも設定を変えれば、 別のAI（例：Z.AIが提供するGLM-4.7）に切り替えて使うこともできる。

僕は「将軍システム」というマルチエージェント構成を運用していて、将軍（指揮官）は有料プラン のClaude、家老・足軽（作業担当10名）はGLM-4.7で動かしていました。

ところがClaude Codeが勝手に自動アップデートされた（v2.1.31 → v2.1.37）。すると、今まで問題な く動いていたGLMへの接続が突然できなくなった。

将軍（有料プラン）は影響なし。API経由で接続していた家老・足軽チームだけが壊れた。

エラーメッセージはこう：

将軍: Claude Max（ログイン）→ Opus 4.6 ✅ 家老・足軽: APIキー → Z.AI → GLM-4.7 ✅

【アップデート前】 将軍: Claude Max（ログイン）→ Opus 4.6 ✅ 家老・足軽: APIキー → Z.AI → GLM-4.7 ✅

【アップデート後】 将軍: Claude Max（ログイン）→ Opus 4.6 ✅ 変わらず 家老・足軽: APIキー → Z.AI → GLM-4.7 ❌ 弾かれる

"Both a token (claude.ai) and an API key (ANTHROPIC_API_KEY) are set"

OAuthとAPIキーが衝突する仕組み（たとえ話）

プロキシアーキテクチャの概念図

Claude Codeは「会員制レストラン」のようなもの。

将軍は「会員カード（有料プランのログイン）」で入店 → 問題なし

家老たちは「合鍵（APIキー）」で別の部屋（GLM）に入っていた → 問題なし

ところがレストランが改装（アップデート）して：

「会員カードを持っている人は、合鍵は使えません」というルールに変わった

家老たちは同じ建物にいるため、会員カードの存在が検知されてしまう

結果、合鍵が無効化されてGLMの部屋に入れなくなった

これがOAuthとAPIキーが衝突する仕組みの正体。

解決策の全体像

別HOME環境によるOAuth分離

2つの対策を組み合わせて解決しました。

対策1: 部屋を分ける（別HOME）

家老たち専用の控室（設定フォルダ）を用意した。ここには会員カード情報が入っていないので、「合 鍵だけの人」として扱ってもらえる。

対策2: 中継役を立てる（プロキシ）

合鍵を直接見せると弾かれるケースがあったので、「中継役」を間に立てた。中継役が合鍵を預かって GLMの部屋に取り次いでくれる。

対策3: メモ用紙で指示する（スクリプト起動）

口頭vsメモ用紙：スクリプト起動の概念

口頭（インライン変数）で「中継役の場所はここ」と伝えると忘れてしまう問題があった。メモ用紙 （シェルスクリプト）に書いて渡したら確実に届くようになった。

手順通りに進めれば誰でも再現できます。

【エンジニア向け】技術詳細

ここからは技術情報になります。同じ環境を再現したい人向けの解説です。

環境情報

問題の根本原因

原因1: Claude Code v2.1.37のOAuth優先仕様

v2.1.31ではuserType: externalとしてAPIキー認証が独立して動作していた。v2.1.37へのアップデート 後、OAuth（Claude Max）が存在する環境でANTHROPIC_API_KEYを設定するとコンフリクトが発 生する。

OS: macOS (Darwin 24.6.0, Apple Silicon ARM64) Claude Code: v2.1.37 Node.js: v24.3.0 シェル: zsh 外部API: Z.AI (https://api.z.ai/api/anthropic) → GLM-4.7モデル 認証: Claude Max（OAuth）+ Z.AI APIキー併用 マルチエージェント: tmuxベース（10エージェント並列）

原因2: 環境変数の渡し方

tmux send-keys経由でインライン環境変数を設定した場合、ANTHROPIC_BASE_URLがClaude Code のNode.jsプロセスに正しく伝播しない。

解決アーキテクチャ

Before/After: 解決前後の比較

実装ファイル

#### 1. プロキシサーバー（proxy.py）

# ❌ 動かない（zsh + tmux send-keys経由） ANTHROPIC_BASE_URL="http://127.0.0.1:18080" ANTHROPIC_API_KEY="xxx" claude --model g

# ✅ 動く（シェルスクリプト経由） export ANTHROPIC_BASE_URL="http://127.0.0.1:18080" export ANTHROPIC_API_KEY="xxx" exec claude --model glm-4.7

┌──────────────┐ ┌─────────────────┐ ┌──────────────────┐ │ Claude Code │───▶│ ローカルプロキシ │───▶│ Z.AI API │ │ (GLM-4.7) │ │ 127.0.0.1:18080 │ │ api.z.ai/api/ │ │ │ │ │ │ anthropic │ │ HOME=別フォルダ│ │ ヘッダー転送 │ │ │ │ API_KEY=Z.AI │ │ x-api-key維持 │ │ GLM-4.7応答 │ └──────────────┘ └─────────────────┘ └──────────────────┘

import http.server import socketserver import urllib.request import ssl

TARGET = "https://api.z.ai/api/anthropic"

class ProxyHandler(http.server.BaseHTTPRequestHandler): def do_POST(self): content_length = int(self.headers.get('Content-Length', 0)) body = self.rfile.read(content_length)

url = TARGET + self.path

#### 2. 専用HOMEディレクトリ

OAuth情報を含まない.claude.jsonを配置したディレクトリを作成する。

重要: oauthAccountフィールドが存在しないことが必須。これがあるとOAuth認証が優先される。

req = urllib.request.Request(url, data=body, method='POST') for k, v in self.headers.items(): if k.lower() not in ('host', 'content-length'): req.add_header(k, v)

ctx = ssl.create_default_context() try: resp = urllib.request.urlopen(req, context=ctx) resp_body = resp.read() self.send_response(resp.status) for k, v in resp.getheaders(): if k.lower() not in ('transfer-encoding',): self.send_header(k, v) self.end_headers() self.wfile.write(resp_body) except urllib.error.HTTPError as e: resp_body = e.read() self.send_response(e.code) self.end_headers() self.wfile.write(resp_body)

def log_message(self, format, *args): pass

class ThreadingProxy(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True

server = ThreadingProxy(('127.0.0.1', 18080), ProxyHandler) print("Proxy on http://127.0.0.1:18080 (threaded)", flush=True) server.serve_forever()

mkdir -p /path/to/.karo-home/.claude

# 最小限の .claude.json（OAuthなし） cat > /path/to/.karo-home/.claude.json << 'EOF' { "hasCompletedOnboarding": true, "autoUpdates": false, "bypassPermissionsModeAccepted": true, "customApiKeyResponses": { "approved": [""], "rejected": [] } } EOF

#### 3. エージェント起動スクリプト（launch-agent.sh）

重要: exportを使うこと。インライン変数（VAR=x claude）はtmux環境で動作しない。

起動手順と動作確認

GLM-4.7接続成功の画面

Step 1: プロキシをバックグラウンドで起動

Step 2: プロキシ動作確認

GLM-4.7の応答が返ればOK。

Step 3: tmuxペインでエージェント起動

#!/bin/bash # Usage: launch-agent.sh export HOME="/path/to/.karo-home" export ANTHROPIC_BASE_URL="http://127.0.0.1:18080" export ANTHROPIC_API_KEY="" cd /path/to/working/directory exec claude --model glm-4.7 --append-system-prompt "$(cat "$1")" --dangerously-skip-

python3 proxy.py &

curl -s http://127.0.0.1:18080/v1/messages \ -H "Content-Type: application/json" \ -H "x-api-key: " \ -H "anthropic-version: 2023-06-01" \ -d '{"model":"glm-4.7","max_tokens":10,"messages":[{"role":"user","content":"hi"}]

tmux send-keys -t : 'bash /path/to/launch-agent.sh /path/to/prompt.md'

Step 4: 動作確認

ペインに「glm-4.7 · API Usage Billing」と表示されればOK。テストメッセージ「say OK」を送って応 答が返ることを確認する。

これで完了です！

自動アップデート無効化（推奨）

同じ問題の再発を防ぐため、.claude.jsonに以下を設定：

まとめ

完成した将軍マルチエージェントシステム

Claude CodeのアップデートでOAuthとAPIキーが衝突する問題、3つの対策で解決しました。

1. 別HOME: OAuth情報がない設定フォルダを用意

2. プロキシ: APIキーを中継するローカルサーバー

3. スクリプト起動: 環境変数を確実に渡す

この問題が発生する条件は以下のすべてに当てはまる場合：

1. Claude Max（有料プラン）にログインしている

2. Claude Code v2.1.37以降を使用している

3. ANTHROPIC_API_KEYで外部API（Z.AI等）に接続したい

4. 同一マシン上でOAuth認証とAPIキー認証を共存させたい

tmux send-keys -t : Enter

{ "autoUpdates": false, "autoUpdaterStatus": "disabled" }

同じ問題に遭遇した人は、ぜひ試してみてください！

