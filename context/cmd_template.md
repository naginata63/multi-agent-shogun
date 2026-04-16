# cmd発行テンプレート（将軍用）

将軍がshogun_to_karo.yamlにcmd書く際、以下のルールをcommandに含めること。
memoryにある教訓でも、ここに書かなければ家老・足軽には伝わらない。

## 必須フィールド

```yaml
- id: cmd_XXXX
  timestamp: 'ISO 8601'
  lord_original: "殿の発言をそのまま記載（加工・要約禁止）"
  north_star: "なぜこのcmdがビジネス目標に貢献するか"
  purpose: "完了条件（1文）"
  acceptance_criteria:
    - "具体的・検証可能な条件1"
    - "具体的・検証可能な条件2"
    - "dashboard.mdが最新状態に更新されていること"
  command: |
    （以下タスク詳細）

    ## 共通ルール（必ず含めよ）
    - 出力先パスを明記せよ（動画関連は work/{YYYYMMDD}_{タイトル}/output/cmd_XXXX/ 配下）
    - 新規.pyはプロジェクトのscripts/配下（例: multi-agent-shogun/projects/dozle_kirinuki/scripts/）に保存せよ。python3 -c ワンライナー使い捨て禁止。再現可能な形でスクリプトを残せ。既存スクリプトで対応できる場合は既存を使え
    - 作業前に skills/ と既存スクリプトを確認し、使えるものがあれば使え
    - Gemini APIはテキスト処理に使うな（Claude CLI Opus 4.6を使え）。ただしEmbeddingはGemini許可
    - 画像生成はVertex API経由gemini-3.1-flash-image-preview
    - ffmpegはh264_nvenc（GPU）。libx264禁止
    - 中間成果物はファイルに保存（/tmp禁止、work/配下）
    - git commit & push済みであること

  project: project-id
  priority: high/medium/low
  status: pending
```

## タスク種別ごとの追加ルール

### 漫画ショート
```
- manga-shortスキル（skills/manga-short/）を使え
- panels JSON → スキル実行の流れ。スクリプト新規作成するな
- expression_design_v5.md必須参照
- member_profiles.yaml参照
- キャラリファレンス: assets/dozle_jp/character/selected/ 配下
- セリフ配置: 中央〜上部（下部・右下禁止）
- 9:16縦向き
```

### HL/SH候補選定
```
- context/highlight_command_template.md 参照
- context/shorts_command_template.md 参照
- AIが勝手にシーンを選ぶな。候補リスト提示→殿が選ぶ
```

### STT/字幕処理
```
- vocal_stt_pipeline.py を使え
- 話者IDは実名必須（A/B/Cアルファベット不可）
- Gemini SRT廃止済み。使うな
```

### 画像生成
```
- ガチャ上限3回（殿許可なく追加禁止）
- 1パネル試し打ち→殿確認→OK→残り生成
- 問題パネルだけ再生成（全パネル再生成禁止）
```
