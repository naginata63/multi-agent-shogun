# 📊 戦況報告
最終更新: 2026-04-04 10:56

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### ⚠️ cmd_952 ナレーション動画受託案件 — 殿方針確認待ち

### 🔧 bot再起動必要
`sudo systemctl restart discord-news-bot` — cmd_1100修正反映用

## 🔄 進行中

| cmd | 内容 | 担当 |
|-----|------|------|
（なし）

## ✅ 最近の完了

| cmd | 内容 | 完了日 |
|-----|------|--------|
| cmd_1103 | レベル250漫画P2〜P9×3枚生成（計23枚/P4のみ2枚）比較:http://100.66.15.93:8780/all_panels.html | 4/4 |
| cmd_1100 | Discord配信バグ修正（日付キー辞書形式）+4/4配信済み。⚠️bot再起動要 | 4/4 |
| cmd_1102 | API課金調査: Max≠API別勘定。Haiku $1/$5 per 1M tokens。claude-mem $53-95/月 | 4/4 |
| cmd_1101 | claude-mem不動作原因=Worker AI処理がANTHROPIC_KEY要求（対策: ~/.bashrc設定） | 4/4 |
| cmd_1099 | クリップフルSTT+実名話者ラベル(dozle/qnly) 376語/95.51% ⚠️push要手動 | 4/4 |
| cmd_1098 | 全スクリプト棚卸し196ファイル（使用中130/要確認36/不要30） | 4/4 |
| cmd_1097 | クリップSTT 388語/29セグメント（話者ラベルなし） | 4/4 |
| cmd_1096 | レベル250クリップSTT+マージ字幕完了 | 4/4 |
| cmd_1095 | レベル250クリップ非公開アップ https://www.youtube.com/watch?v=_cLsvqd23GQ | 4/4 |
| cmd_1094 | 31本hotspot分析+replay_score統合（26成功/5本TSなし） | 4/4 |
| cmd_1093 | replay_score統合(3/57本に反映) | 4/4 |
| cmd_1092 | MCPダッシュボードstatus修正+🚨要対応7件反映 | 4/3 |
| cmd_1091 | なぎなたキャラ生成完了 | 4/3 |
| cmd_1090 | API版P6×3回(VERTEX_API_KEY) MD5全異常 | 4/3 |
| cmd_1089 | API版P6成功(1.5MB高品質) | 4/3 |
| cmd_1088 | CDP版P6×3回全成功 | 4/3 |
| cmd_1087 | Gemini WM調査: API経由なら✦付かない | 4/3 |
| cmd_1086 | cdp_manga_panel P6テスト（panels_test.json使用） | 4/3 |
| cmd_1085 | ref×3回一貫性テスト: gen1/gen2成功 | 4/3 |
| cmd_1084 | --ref-imageバグ3点修正成功（MD5不同確認） | 4/3 |
| cmd_1083 | 画像比較ページ公開 | 4/3 |
| cmd_1082 | CDP画像生成に--ref-image CLI引数追加 | 4/3 |
| cmd_1081 | CDPリファレンス付き画像生成成功（P1/P3縦型） | 4/3 |
| cmd_1080 | リプレイヒートマップ×ホットスポット3層統合Top10完了 | 4/3 |
| cmd_1079 | MCPダッシュボード3点修正+JST統一 | 4/3 |
| cmd_1078 | 2月動画34本リプレイヒートマップ取得完了 | 4/3 |
| cmd_1077 | YouTube Studio関連動画設定CDP対応完了 | 4/3 |
| cmd_1075 | サムネ3パターン完了。殿選定待ち | 4/2 |
| cmd_1073 | ドズル社3月まとめv6完了。タイトル殿選定待ち | 4/1 |

## 足軽・軍師 状態

| 足軽 | Pane | CLI | 状態 | 現タスク |
|------|------|-----|------|---------|
| 1号 | 0.1 | GLM-5.1 | idle | — |
| 2号 | 0.2 | GLM-5.1 | idle | — |
| 3号 | 0.3 | GLM-5.1 | idle | — |
| 4号 | 0.4 | GLM-5.1 | idle | — |
| 5号 | 0.5 | GLM-5.1 | idle | — |
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

## 🔍 夜間矛盾検出（4/4 インフラ）
HIGH 2件 / MEDIUM 6件 / LOW 3件
- HIGH: semantic_search.py FAISS cronがBQ移行後も毎時実行(キー期限切れで失敗)
- HIGH: mcp_experiment.shがworktree古いDB使用で本番乖離
- MEDIUM: context_monitor.sh/agent_status.sh pane名不一致
- MEDIUM: agent_status.sh task YAML読み込みがflat構造前提で動かない
詳細: queue/reports/gunshi_nightly_audit_20260404.yaml

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
