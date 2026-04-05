# 📊 戦況報告
最終更新: 2026-04-05 09:30

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### 🔧 夜間監査 2026-04-05（YouTube/外部連携）
- CRITICAL: GEMINI_API_KEY参照10+ファイル未移行（VERTEX_API_KEY必須）
- CRITICAL: deprecated google.generativeai使用（gemini_transcription_task.py→削除候補）
- CRITICAL: OAuth token.jsonがリポジトリ内格納
- HIGH: ハードコードパス15+ファイル
- MEDIUM: generate_outro.py libx264使用（h264_nvenc違反）
- → 優先1: VERTEX_API_KEY一括移行cmd発令必要
### ⚠️ cmd_952 ナレーション動画受託案件 — 殿方針確認待ち

## 🔄 進行中

| cmd | 内容 | 担当 |
|-----|------|------|
| cmd_1165 | ニンジン世界漫画3周再生成（フルパス指定） | 足軽5号 |

## ✅ 最近の完了

| cmd | 内容 | 完了日 |
|-----|------|--------|
| cmd_1165b | PreToolUseフック4: 家老のtasks/*.yaml相対パス検出 commit d2bca86 | 4/5 |
| cmd_1164 | AI NEWS OGP修正（og:title+description+ogp.png再生成）commit 6cdaac0 | 4/5 |
| cmd_1163 | MCPダッシュボードP1-P6修正（DB統一+自動done誤発動修正）commit 987a284 | 4/5 |
| cmd_1161 | ニンジン世界P1-P7 3周生成（21枚、$1.41） | 4/5 |
| cmd_1158 | shogun_to_karo.yaml done自動アーカイブ（24192→2253行、91%削減）commit 33808a5 | 4/5 |

## 足軽・軍師 状態

| 足軽 | Pane | CLI | 状態 | 現タスク |
|------|------|-----|------|---------|
| 1号 | 0.1 | GLM-5.1 | idle | — |
| 2号 | 0.2 | GLM-5.1 | idle | — |
| 3号 | 0.3 | GLM-5.1 | idle | — |
| 4号 | 0.4 | GLM-5.1 | idle | — |
| 5号 | 0.5 | GLM-5.1 | busy | cmd_1165 |
| 6号 | 0.6 | GLM-5.1 | idle | — |
| 7号 | 0.7 | GLM-5.1 | idle | — |
| 軍師 | 0.8 | Opus | idle | — |

## APIキー状況
- **VERTEX_API_KEY**: 正常（config/vertex_api_key.env）— 唯一の有効Gemini系キー
- **GEMINI_API_KEY（KEY_2）**: 期限切れ
- **KEY_1は使用禁止**（22,000円課金）
- **OPENAI_API_KEY**: 正常（billing上限引き上げ済み）

## チャンネル実績（2026-04-01 13:21更新）
- 登録者**1,007人**（1000人突破！収益化条件クリア！）
- 視聴回数**98.4万回** / 総再生時間**5,925時間**
- ちゃかすMEN **210,081再生**（チャンネル最多）
- 極小MEN **131,804再生**（急伸中）

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
