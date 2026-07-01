---
name: phone-review-serve
description: |
  制作途中の動画/画像を殿がスマホで即確認できるよう、ローカルHTTPサーバー(work/evidence_serve/)に配置しntfy通知する。
  Tailscale経由(http://100.66.15.93:8901/)でLAN外からもアクセス可能。ファイルコピー→<video>タグHTMLラッパー作成→サーバー起動確認→ntfy送信までを一括で行う。
  「ntfyでhtmlサーバーにあっぷ」「殿に確認してもらう」「スマホで見せる」「evidence_serve」「/phone-review-serve」で起動。
  Do NOT use for: YouTube本アップロード（それは/shorts-uploadや各種uploaderスクリプトを使え）。
  Do NOT use for: 恒久的な成果物保存（work/evidence_serveは審査/レビュー用の一時置き場）。
argument-hint: "<動画/画像パス> [表示タイトル]"
allowed-tools: Bash, Read, Write
---

# phone-review-serve — 制作物スマホレビュー配信

## North Star

**「殿に見てもらいたい」→ 1分以内にスマホで再生できるリンクをntfyで届ける。**
YouTube非公開アップは審査に時間がかかり、叩き台レベルの確認には重すぎる。ローカルHTTPサーバー+ntfyなら即時。

## いつ使うか

- 編集途中/叩き台の動画を殿にまず見てもらいたい時
- サムネイル案・パネル画像の比較をスマホで見せたい時
- YouTube非公開アップするほどでもない確認作業

## いつ使わないか

| 状況 | 代わりに |
|------|---------|
| 完成品を実際にYouTube公開/非公開アップしたい | `/shorts-upload` や各uploaderスクリプト |
| 恒久的に保存が必要な成果物 | `work/cmd_XXXX/` 等の正規置き場（.gitignore whitelist登録を検討） |

## 前提: サーバー基盤

- 配信ディレクトリ: `projects/dozle_kirinuki/work/evidence_serve/`
- ポート: **8901**（python3 標準ライブラリ http.server）
- ベースURL: `http://100.66.15.93:8901/`（Tailscale IP・LAN外の殿スマホからも到達可）
- ログ: `/tmp/evidence_server.log`
- **注意**: サーバーは常駐前提だが、再起動等で落ちていることがある。毎回起動確認必須（Step 2）。

## 実行手順

### Step 1: ファイル配置

```bash
cp "<元ファイルパス>" /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/evidence_serve/<name>.mp4
```

- ファイル名は英数字+アンダースコアのみ推奨（URLで直打ちするため日本語・記号は避ける）
- 既存ファイルと衝突しないよう `_v2` 等でバージョン管理

### Step 2: HTMLラッパー作成

`<video>` タグで包んだ軽量HTMLをスマホ向けに用意する（生mp4直リンクだとダウンロード扱いになる端末があるため）。既存例: `work/evidence_serve/cam10_flow.html`

```html
<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>{表示タイトル}</title>
<style>body{background:#111;margin:0;padding:8px;font-family:sans-serif;color:#eee}video{width:100%;max-width:480px;display:block;margin:0 auto;border-radius:8px}p{text-align:center;font-size:13px}</style>
<p>{説明文1行目}</p>
<video src="<name>.mp4#t=0.1" controls playsinline preload=auto></video>
<p>{補足（尺・内容など）}</p>
```

保存先: `work/evidence_serve/<name>.html`

### Step 3: サーバー起動確認

```bash
ss -tlnp 2>/dev/null | grep 8901
```

- **listen中なら何もしない**（多重起動禁止・ポート衝突する）
- **listenしていなければ起動**:
  ```bash
  cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/evidence_serve
  nohup python3 -m http.server 8901 --bind 0.0.0.0 >> /tmp/evidence_server.log 2>&1 &
  disown
  sleep 1
  ```
- 起動後 `curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://100.66.15.93:8901/<name>.html"` で200確認

### Step 4: ntfy通知

```bash
bash /home/murakami/multi-agent-shogun/scripts/ntfy.sh "🎬 {説明}: http://100.66.15.93:8901/<name>.html"
```

- URLは `100.66.15.93`（Tailscale IP）を直接埋め込む。`192.168.2.4`等のLAN内IPは殿のスマホ(LAN外)から届かない
- `queue/ntfy_sent.log` に記録されるので、末尾を見て送信成功を確認できる

## Validation

- Step 3のcurl確認でHTTP 200が返ること
- ntfy送信後 `tail -3 queue/ntfy_sent.log` で当該メッセージが記録されていること

## エラーハンドリング

| 症状 | 対処 |
|------|------|
| `ss` で8901が出てこない | サーバー未起動。Step 3の起動コマンドを実行 |
| curlがHTTP 000/接続拒否 | サーバー起動直後で間に合っていない可能性。1-2秒待って再curl |
| ntfy送信時にシェルエラーが出る | `scripts/ntfy.sh` 内部の非致命的な警告のことがある。`queue/ntfy_sent.log` 末尾で実送信を必ず確認せよ（エラー表示だけで未送信と即断するな） |
| ポート8901が別プロセスに専有されている | `ss -tlnp \| grep 8901` でPID確認→そのプロセスが評価用サーバー自身か確認してから対処（無関係なプロセスをkillしない） |

## 注意点

- **一時レビュー用途限定**: work/evidence_serve/ は殿確認後の恒久保存場所ではない。完成品は別途正規フローで保存/アップロードする
- **ファイル名にURLエンコードが必要な文字を避ける**: 日本語ファイル名は避け、英数字+アンダースコアにする
- **Tailscale IP固定**: `100.66.15.93` はこのマシンのTailscale IP。マシン変更時は `tailscale ip -4` で再確認must

## 関連スキル

| スキル | 関係 |
|--------|------|
| `/shogun-screenshot` | 画像のスクショ取得・加工（配信前段） |
| `/shorts-upload` | 完成品のYouTube非公開アップ（本スキルの次段） |
