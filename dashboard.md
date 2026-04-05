# 📊 戦況報告
最終更新: 2026-04-06 02:06

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### ⚠️ cmd_1212 TNT漫画 Vertex AI 429対策 — 実装判断
軍師分析完了（gunshi_report_cmd1212.yaml）。根本原因: リトライロジック不在 + 複数エージェント同時画像生成。
推奨実装（優先度1+2のみで大部分解消）:
- **優先1**: exponential backoff リトライ（120s→240s→480s+jitter）→ generate_manga_short.py
- **優先2**: --skip-existing オプション（失敗パネルだけ再生成）
実装を足軽に振ってよいか？


### ⚠️ cmd_952 ナレーション動画受託案件 — 殿方針確認待ち

### 🔧 夜間監査 2026-04-05 残項目
- CRITICAL: OAuth token.jsonがリポジトリ内格納
- HIGH: ハードコードパス15+ファイル


## 🔄 進行中

| cmd | 内容 | 担当 | 開始 |
|-----|------|------|------|
| cmd_1211 | Gemini Vision note_visual_qc.py作成 | 足軽4号 | 23:43 |

## ✅ 最近の完了
| cmd | 内容 | 完了日 |
|-----|------|--------|
| nightly_audit | STTパイプライン矛盾検出 — 矛盾なし（INFO1件: symlink残存のみ） | 4/6 |
| cmd_1214 | generate_manga_short.py リトライ+skip-existing実装完了 | 4/6 |
| cmd_1213 | YAMLバリデーション+cron設定（PostToolUseフック+slim_yaml毎日3時） | 4/6 |
| cmd_1212 | TNT漫画429分析完了 — リトライ不在+複数同時実行が根本原因 → gunshi_report_cmd1212.yaml | 4/6 |
| cmd_1210 | sasuuノート全記事PDF化96件（note API v2 16ページ×6件）→ work/sasuu_articles/ | 4/5 |
| cmd_1209 | note投稿パイプライン整備 — 殿指示により中断（note再投入うまくいかず） | 4/6 |
| cmd_1207 | note記事挿絵4枚挿入（CDP方式・insert_images_shogun_article.js・下書き保存済） | 4/5 |
| cmd_1208 | 漫画パイプライン5項目改善（selfcheck_rules・S1-S8・is_climax・char_prohibitions・テンプレ画像3枚） | 4/5 |
| cmd_1206 | sasuuノート全記事PDF化18件 → work/sasuu_articles/ | 4/5 |
| cmd_1205 | cdp_image_gen.py作成（CDP汎用・--prompt/--output/--ref-image/--size対応・テスト確認済） | 4/5 |

| cmd_1204 | 漫画システム比較分析（斉川ニア記事）→ 高優先3件（セルフチェック2段階・構図パターン・キメゴマ）→ gunshi_report_cmd1204.yaml | 4/5 |
| cmd_1201 | 漫画構図汎用ナレッジ文書作成（15件JSON引用・339行）→ manga_composition_knowledge.md | 4/5 |
| cmd_1200 | note下書き本文投入+カバー画像+ハッシュタグ設定済 → https://note.com/n/nedb886542772 | 4/5 |
| cmd_1199 | GLM-5.1スペック調査（CTX 200K/出力131K/5h1600prompts/画像非対応）→gunshi_report_cmd1199.yaml | 4/5 |
| cmd_1197 | TNTネザー漫画パネル構図分析（5改善点特定→gunshi_report_cmd1197.yaml） | 4/5 |
| cmd_1198 | note下書き投稿（AIエージェント8体記事）→ https://note.com/n/nedb886542772 | 4/5 |
| cmd_1196 | note記事なぎなた挿絵5枚（カバー1+本文4）CDP+記事コメント挿入（commit 2050b00） | 4/5 |
| cmd_1194 | Vertex AI ADC認証一括移行87+箇所+Embedding location hotfix | 4/5 |
| cmd_1188 | PreToolUseフック実装（work/cmd_*防止・テスト4件全PASS） | 4/5 |

## 足軽・軍師 状態

| 足軽 | Pane | CLI | 状態 | 現タスク |
|------|------|-----|------|---------|
| 1号 | 0.1 | GLM-5.1 | idle | — |
| 2号 | 0.2 | GLM-5.1 | idle | — |
| 3号 | 0.3 | GLM-5.1 | idle | — |
| 4号 | 0.4 | GLM-5.1 | busy | cmd_1211 note_visual_qc.py作成中 |
| 5号 | 0.5 | GLM-5.1 | stuck | cmd_1180（放置） |
| 6号 | 0.6 | GLM-5.1 | idle | — |
| 7号 | 0.7 | GLM-5.1 | idle | — |
| 軍師 | 0.8 | Opus | idle | — |

## APIキー状況
- **Vertex AI ADC**: ✅ 復旧済み（殿が通常HOME・GLM HOME両方で確認）
- **VERTEX_API_KEY**: 廃止完了（cmd_1194でADC移行済み）
- **GEMINI_API_KEY**: 期限切れ（廃止方針）
- **OPENAI_API_KEY**: 正常

## チャンネル実績（2026-04-01 13:21更新）
- 登録者**1,007人**（1000人突破！）
- 視聴回数**98.4万回** / 総再生時間**5,925時間**
- ちゃかすMEN **210,081再生**（チャンネル最多）
- 極小MEN **131,804再生**（急伸中）

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
