# 📊 戦況報告
最終更新: 2026-04-05 21:20

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### ⚠️ cmd_952 ナレーション動画受託案件 — 殿方針確認待ち

### 🔧 夜間監査 2026-04-05 残項目
- CRITICAL: OAuth token.jsonがリポジトリ内格納
- HIGH: ハードコードパス15+ファイル

### ⚠️ YAMLバリデーションフック/slim_yaml.sh cron タスク未収録
殿が「cmd_1201を書いた。(1)PreToolUseフックにYAMLバリデーション追加 (2)slim_yaml.shのcron毎日3時自動実行。足軽に振れ」と言及したが、shogun_to_karo.yamlに対応エントリなし。
実装するならcmdとして正式に追記されたし。または不要ならこの項目を削除されたし。

## 🔄 進行中

| cmd | 内容 | 担当 | 開始 |
|-----|------|------|------|
| cmd_1201 | 漫画構図汎用ナレッジ文書作成（15件パネルJSON分析）→ manga_composition_knowledge.md | 軍師 | 21:20 |
| cmd_1203 | なぎなた挿絵リテイク（男性キャラ）5枚+note記事挿入 | 足軽3号 | 21:20 |

## ✅ 最近の完了
| cmd | 内容 | 完了日 |
|-----|------|--------|
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
| 3号 | 0.3 | GLM-5.1 | busy | cmd_1203 なぎなた挿絵リテイク |
| 4号 | 0.4 | GLM-5.1 | idle | — |
| 5号 | 0.5 | GLM-5.1 | stuck | cmd_1180（放置） |
| 6号 | 0.6 | GLM-5.1 | idle | — |
| 7号 | 0.7 | GLM-5.1 | idle | — |
| 軍師 | 0.8 | Opus | busy | cmd_1201 漫画ナレッジ |

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
