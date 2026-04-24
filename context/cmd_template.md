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
  verify_guidance: |
    # 家老へ: 本cmdを足軽タスクYAMLに落とす際、verify: 欄を必ず含めよ（cmd_1442 H1 harness）
    # task YAML verify: 欄の書式例はセクション「Task YAML verify: 欄（cmd_1442 H1 harness）」参照
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

## Task YAML verify: 欄（cmd_1442 H1 harness）

**適用先**: `queue/tasks/ashigaru{N}.yaml` / `queue/tasks/gunshi.yaml` の各タスクブロック。cmd_template.md 本体ではない（家老が task YAML 起票時に以下スキーマを必ず含めよ）。

### スキーマ

```yaml
- task_id: subtask_XXXX
  status: assigned  # assigned → in_progress → done（done 遷移時 verify_result: pass 必須）
  verify:
    command: "curl -sf http://localhost:3000/health | grep -q '\"ok\":true'"
    pass_criteria: "exit 0 (grep match) / または shell 成功"
    screenshot_url: "http://localhost:3000/dashboard"   # optional: URL verify時
    timeout_seconds: 60
  verify_result: pending   # pending | pass | fail | run_now（auto-runner 起動）
  verify_output_path: null # 実行時に記録（logs/verify_{task_id}_{YYYYMMDD}.log 推奨）
```

### ルール（全エージェント）

1. **verify: 宣言が opt-in**: `verify:` 欄が存在する task のみゲート対象。既存 task は素通り（後方互換）。
2. **status:done 遷移前に verify 実行**: 足軽は自ら `verify.command` を実行し、成功なら `verify_result: pass` + `verify_output_path: ...` を書込 → その後 `status: done` に変更せよ。
3. **PreToolUse ゲート**: `verify:` 宣言済み task で `verify_result: pass` 未達のまま `status: done` 書込は BLOCK される（exit 2、`scripts/pretool_check.sh` CHK5）。
4. **auto-runner 利用**: `verify_result: run_now` と書込→PostToolUse `scripts/posttool_verify_runner.sh` が verify コマンドを自動実行し `verify_result: pass|fail` + `verify_output_path:` を書き戻す（timeout 60s 固定）。
5. **URL verify の screenshot**: `verify.screenshot_url` があれば足軽が shogun-screenshot skill を起動し `verify_output_path` にスクショパスを追記せよ（hook からは起動不可）。
6. **失敗時**: verify_result: fail なら足軽は実装修正 → verify 再実行 → pass になったら status: done。fail のまま done 化は不可。

### 採択例（cmd_1434 OGP import漏れ防止）

```yaml
- task_id: subtask_1434_ogp
  status: assigned
  verify:
    command: "curl -sf http://localhost:3000/api/og?id=123 -o /tmp/og.png && file /tmp/og.png | grep -q PNG"
    pass_criteria: "PNG バイナリが返る（NameError/500 エラーなし）"
    timeout_seconds: 30
  verify_result: pending
```
