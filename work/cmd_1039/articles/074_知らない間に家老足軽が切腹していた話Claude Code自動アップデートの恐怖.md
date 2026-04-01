# 知らない間に家老足軽が切腹していた話Claude Code自動アップデートの恐怖

**URL**: https://note.com/sasuu/n/nc7865f118af9

---

知らない間に家老・足軽が切腹していた話 （Claude Code自動アップデートの恐怖）

知らない間に家老・足軽が切腹していた話（Claude Code自動アップデートの恐怖）

朝起きて tmux に接続したら、将軍以外の全軍が消滅していた。

僕は10体以上のエージェントをtmuxで並列起動してマルチエージェントシステムを運用してるんです けど、夜中にClaude Codeが勝手にアップデート（v2.1.31 → v2.1.37）して、OAuth認証とAPIキー認 証が衝突するようになった。

結果、将軍（Claude Max）は無事だったけど、API経由でGLM-4.7を使ってた家老・足軽チームが全 滅。

sasuu｜非エンジニアのAI活用術 2026年2月17日 12:00

「自動アップデート」という名の切腹命令で、一夜にして軍勢が崩壊しました。

事件発生: 朝起きたら軍勢が消えていた

僕は「将軍システム」というマルチエージェント構成で開発してます。

将軍（Claude Opus 4.6）: 有料プラン、全体指揮

家老（GLM-4.7）: タスク分解・進捗管理

足軽4体（GLM-4.7）: 並列実行部隊

GLMを使ってるのはコスト戦略で、年5,000円でほぼ使い放題だから足軽部隊に最適なんですよね。

で、前日の夜まで問題なく動いてた。

朝起きてtmuxに接続したら……

なんだこれ。

ログを見たら、全員こんなエラーを吐いてました。

将軍: ✅ 動いてる 家老: ❌ エラーで固まってる 足軽1〜4: ❌ 全員エラーで固まってる

"Both a token (claude.ai) and an API key (ANTHROPIC_API_KEY) are set"

原因: Claude Codeが夜中に勝手にアップデート していた

調べたら、Claude Codeが夜中に 勝手に v2.1.31 から v2.1.37 にアップデートしてました。

自動アップデート、デフォルトでONなんですよね。

v2.1.37から「OAuth認証とAPIキー認証の共存」ができなくなった。正確には、Claude Maxにログイ ンしてる状態（OAuth）で ANTHROPIC_API_KEY を設定すると、「両方設定されてるぞ」って弾かれ るようになった。

つまり：

将軍だけOAuth認証のままだから影響なし。

でもAPI経由で動いてた家老・足軽は 全員「OAuth情報を検知してしまう」せいで起動不能 になっ た。

まるで将軍の存在が原因で家老以下が切腹させられたような状況。

切腹メカニズム: なぜ家老だけが死んだのか

【v2.1.31（前夜）】 将軍: Claude Max（OAuth） ✅ 家老・足軽: API経由でGLM-4.7 ✅

【v2.1.37（翌朝）】 将軍: Claude Max（OAuth） ✅ 変わらず 家老・足軍: API経由でGLM-4.7 ❌ 弾かれる

「会員制レストラン」で例えるとわかりやすい。

将軍 は「会員カード（有料プラン）」で入店 → 問題なし

家老・足軽 は「合鍵（APIキー）」で別の部屋（GLMサーバー）に入ってた → 問題なかった

ところがレストランが改装（アップデート）したら：

「会員カードを持ってる人は、合鍵は使えません」というルールに変わった。

しかも 同じ建物（マシン）にいるだけで会員カード所持が検知される という仕様。

家老・足軽は合鍵しか持ってないのに、建物に将軍がいるせいで「会員カードあるじゃん」って弾か れるようになった。

これが「OAuth+APIキー衝突問題」の正体です。

理不尽すぎる。

発見までのタイムラグ: なぜ朝まで気づかなかった か

夜中にアップデートが走ったけど、すぐには気づかなかった理由がある。

エージェントは 既に起動済み だったから、メモリ上では動いてたんですよね。

でも次に何かコマンドを実行しようとした瞬間、API接続が発生して その瞬間にエラー吐いて固まっ た。

つまり：

つまり深夜のどこかで一斉に切腹してて、朝になって発見した形です。

本当に怖い。

復旧作戦: 別HOMEディレクトリ + プロキシサーバ ー

この問題、簡単には解決しません。

「じゃあAPIキーだけ使えばいいじゃん」って思うでしょ？でも将軍はClaude Maxにログインしてな いと使えないから、OAuth認証は外せない。

「じゃあ全部Opusにすればいいじゃん」って？それは月10万円コースなのでNG。

結果、こういう構成にしました：

対策1: 別HOMEディレクトリ（家老・足軽専用）

OAuth情報が入ってない .claude.json を置いた専用ディレクトリを作成。

23:00 Claude Code自動アップデート開始 23:15 アップデート完了（v2.1.37） 23:16 家老「タスク分解しますね」→ API呼び出し → ❌ エラー 23:16 足軽「承知しました」→ API呼び出し → ❌ エラー ...（以後無限にエラー）... 07:30 僕が起きて tmux に接続 07:31 「全員固まってる！？」←今ここ

mkdir -p /Users/sasou/root/.shogun/.karo-home/.claude

cat > /Users/sasou/root/.shogun/.karo-home/.claude.json << 'EOF'

重要: oauthAccount フィールドを含めない。これがあるとOAuthが優先される。

対策2: プロキシサーバー（API中継役）

Z.AIのAPIに直接接続すると弾かれるケースがあったので、ローカルプロキシを立てて中継させる。

対策3: スクリプト起動（環境変数を確実に渡す）

{ "hasCompletedOnboarding": true, "autoUpdates": false, "bypassPermissionsModeAccepted": true, "customApiKeyResponses": { "approved": ["末尾20文字"], "rejected": [] } } EOF

# proxy.py（簡略版） import http.server import urllib.request import ssl

TARGET = "https://api.z.ai/api/anthropic"

class ProxyHandler(http.server.BaseHTTPRequestHandler): def do_POST(self): content_length = int(self.headers.get('Content-Length', 0)) body = self.rfile.read(content_length)

url = TARGET + self.path req = urllib.request.Request(url, data=body, method='POST') for k, v in self.headers.items(): if k.lower() not in ('host', 'content-length'): req.add_header(k, v)

ctx = ssl.create_default_context() resp = urllib.request.urlopen(req, context=ctx) resp_body = resp.read()

self.send_response(resp.status) for k, v in resp.getheaders(): if k.lower() not in ('transfer-encoding',): self.send_header(k, v) self.end_headers() self.wfile.write(resp_body)

server = http.server.HTTPServer(('127.0.0.1', 18080), ProxyHandler) server.serve_forever()

tmux send-keys 経由でインライン環境変数を渡すと、うまく伝播しないことがある。

だからシェルスクリプトに書いて、確実に渡す：

これをtmuxから起動：

これで復旧しました。

家老・足軽が全員復活して、再び軍勢が動き始めた瞬間は感動しましたね。

教訓: プロダクション運用では自動アップデート無 効化が必須

#!/bin/bash # launch-karo.sh export HOME="/Users/sasou/root/.shogun/.karo-home" export ANTHROPIC_BASE_URL="http://127.0.0.1:18080" export ANTHROPIC_API_KEY="" cd /Users/sasou/root exec claude --model glm-4.7 --append-system-prompt "$(cat .shogun/config/karo-role.m

tmux send-keys -t multiagent:0.0 'bash /Users/sasou/root/bin/launch-karo.sh' tmux send-keys -t multiagent:0.0 Enter

今回の教訓は明確です。

マルチエージェントシステムで Claude Code を使うなら、自動アップデート無効化は必須

.claude.json に以下を設定：

これをやってないと、いつか必ず事故ります。

特に今回みたいに「夜中にアップデート → 翌朝発見」っていうパターンだと、ダウンタイムが長引く んですよね。

もし自分がこれを商用サービスで運用してたら、数時間のサービス停止になってた可能性がある。

怖すぎる。

皮肉: 作業を助けるツールが自分を壊した

{ "autoUpdates": false, "autoUpdaterStatus": "disabled" }

一番皮肉なのは、「開発者の作業効率を上げるツール」が「自動アップデート機能」で自分自身を壊し たこと。

Claude Codeは本当に強力なツールで、僕の開発速度を5倍にしてくれた。

でも「便利にしよう」という善意のアップデートが、逆にシステム全体を止めてしまった。

「お前が将軍の認証情報を見つけたせいで、家老・足軽が全員切腹した」っていう構図。

戦国時代なら「謀反の疑い」で粛清される展開ですよ。

しかも自分で気づいて切腹するんじゃなくて、 アップデートという上意で強制切腹 させられた。

まさに理不尽。

まとめ: マルチエージェント運用の罠

マルチエージェントシステムは強力ですけど、こういう罠もあるんだなって学びました。

Claude Code の自動アップデートは必ず無効化すること

OAuth + APIキーの共存環境では別HOMEディレクトリが必須

tmux send-keys 経由の環境変数は不安定（スクリプト起動を推奨）

プロダクション運用では更新前に必ずテスト環境で検証すること

特に最後のポイントは重要で、「勝手にアップデートされて本番で気づく」っていうのが一番危険なん ですよね。

今後は autoUpdates: false を全エージェントに設定して、アップデート時は手動で検証してから適用 するようにします。

それにしても、朝起きて軍勢が全滅してる光景は衝撃でしたね。

「知らない間に切腹してた」っていうタイトルは誇張じゃなくて、本当にそういう状況だった。

もしマルチエージェントシステムを運用してる人がいたら、ぜひ自動アップデート無効化だけは忘れ ずに。

じゃないと、ある日突然軍勢が消滅しますよ。

