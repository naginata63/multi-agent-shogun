# cmd起票テンプレート (JSON形式)

queue/cmd_payloads/ に `cmd_XXXX.json` を作成し、`curl --data @queue/cmd_payloads/cmd_XXXX.json` でAPI投入せよ。
JSON直書き (`curl -d '{...}'`) は pretool_check.sh CHK10 で BLOCK される。

## テンプレート

```json
{
  "id": "cmd_XXXX",
  "priority": "high",
  "project": "project-id",
  "lord_original": "殿の発言をそのまま記載（加工・要約禁止）",
  "north_star": "なぜこのcmdがビジネス目標に貢献するか",
  "purpose": "完了条件（1文）",
  "command_text": "## 背景と目的\n\n(なぜこのcmdが必要か)\n\n## 手順\n\n1. ...\n2. ...\n\n## 共通ルール\n- 出力先パスを明記せよ（動画関連は work/{YYYYMMDD}_{タイトル}/output/cmd_XXXX/ 配下）\n- 新規.pyはプロジェクトのscripts/配下に保存。python3 -c ワンライナー使い捨て禁止\n- 作業前に skills/ と既存スクリプトを確認し、使えるものがあれば使え\n- Gemini APIはテキスト処理に使うな（Claude CLI Opus 4.6を使え）。EmbeddingはGemini許可\n- 画像生成はVertex API経由gemini-3.1-flash-image-preview\n- ffmpegはh264_nvenc（GPU）。libx264禁止\n- 中間成果物はファイルに保存（/tmp禁止、work/配下）\n- git commit & push済みであること",
  "acceptance_criteria": [
    "具体的・検証可能な条件1",
    "具体的・検証可能な条件2",
    "dashboard.mdが最新状態に更新されていること"
  ],
  "notify_karo": true
}
```

## 必須フィールド

| フィールド | 説明 |
|-----------|------|
| `id` | cmd_XXXX 形式の一意ID |
| `priority` | high / medium / low |
| `lord_original` | 殿の発言原文（加工禁止） |
| `purpose` | 完了条件（1文） |
| `acceptance_criteria` | 検証可能な完了条件の配列 |
| `command_text` | タスク詳細（共通ルールを必ず含める） |

## 任意フィールド

| フィールド | 説明 |
|-----------|------|
| `project` | プロジェクトID |
| `north_star` | ビジネス目標との紐付け |
| `notify_karo` | 家老への自動通知（default: true） |

## タスク種別ごとの追加ルール

### 漫画ショート
- manga-shortスキル（skills/manga-short/）を使え
- panels JSON → スキル実行の流れ。スクリプト新規作成するな
- expression_design_v5.md必須参照
- member_profiles.yaml参照
- キャラリファレンス: assets/dozle_jp/character/selected/ 配下
- セリフ配置: 中央〜上部（下部・右下禁止）
- 9:16縦向き

### HL/SH候補選定
- context/highlight_command_template.md 参照
- context/shorts_command_template.md 参照
- AIが勝手にシーンを選ぶな。候補リスト提示→殿が選ぶ

### STT/字幕処理
- vocal_stt_pipeline.py を使え
- 話者IDは実名必須（A/B/Cアルファベット不可）
- Gemini SRT廃止済み。使うな

### 画像生成
- ガチャ上限3回（殿許可なく追加禁止）
- 1パネル試し打ち→殿確認→OK→残り生成
- 問題パネルだけ再生成（全パネル再生成禁止）

## 運用フロー

```
1. queue/cmd_payloads/cmd_XXXX.json を作成（本テンプレートをコピー）
2. 各フィールドを埋める（lord_original は必ず殿原文）
3. curl --data @queue/cmd_payloads/cmd_XXXX.json でAPI投入
4. ファイルはそのまま保持（監査ログ）
```

## Task YAML / cmd YAML スキーマ

task YAML の必須フィールド・`verify:` 欄・`phase_gate:` 欄の正式仕様:

→ **`shared_context/task_yaml_schema.md`** (唯一の schema 正典)
