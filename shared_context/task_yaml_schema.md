# task YAML / cmd YAML Schema (cmd_1443 p06 + p07 統合)

task YAML (`queue/tasks/{ashigaru*,gunshi}.yaml`) および cmd YAML (`queue/shogun_to_karo.yaml`) の共通スキーマ定義。
pretool_check.sh の lint (CHK4-CHK8) がここを規範とする。

- **策定**: 2026-04-24 / ashigaru4 (cmd_1443_p06 + p07 合流)
- **上書き対象**: `context/cmd_template.md` の verify 欄ガイダンスは本書に集約 (cmd_template.md はポインタのみ残す)
- **編集責務**: 家老 (task YAML) / 将軍 (cmd YAML)。足軽は status 遷移と verify_result 書込のみ

---

## 1. task YAML スキーマ (`queue/tasks/{ashigaru*,gunshi}.yaml`)

### 1.1 必須フィールド (CHK7 lint 対象・新規 task_id のみ規制)

```yaml
tasks:
- task_id: subtask_XXXX        # 一意 ID (英数+アンダースコア)
  parent_cmd: cmd_XXXX          # 親 cmd_id
  bloom_level: L4               # L1-L6 (config/settings.yaml の capability_tiers 参照)
  status: assigned              # assigned | in_progress | done | blocked | failed
  target_path: /abs/path/to/file.ext   # 変更対象の絶対パス (pretool_check CHK2 で許可パス判定にも使用)
  timestamp: "2026-04-24T20:00:00+09:00"
  description: "1 行要約"
  steps: "Step1:→Step2:→..."    # 1 行推奨 (CHK3 により多行 steps は BLOCK)
  acceptance_criteria:
    - "具体・検証可能な条件1"
    - "具体・検証可能な条件2"
```

**9 項目全て必須**。1 つでも欠けると pretool_check CHK7 が新規 task_id を BLOCK する (既存 task は素通り)。

### 1.2 任意フィールド

```yaml
  notes:
    - "参考設計への link"
    - "完了後の inbox_write コマンド"
  scope_extension: "殿承認による追加要件 (cmd 起票後に発生)"
  blocked_by: [other_task_id]
  unblocked_at: "2026-04-24T19:45:00+09:00"
  prior_blocked_by: [other_task_id]  # 履歴として保持
```

### 1.3 verify 欄 (cmd_1442 H1 harness・opt-in)

本欄宣言時のみ pretool_check CHK5 + done_gate.sh が作動する。無宣言 task は従来通り done 許可 (後方互換)。

```yaml
  verify:
    command: "curl -sf http://localhost:3000/health | grep -q '\"ok\":true'"
    pass_criteria: "exit 0 (grep match) / shell 成功"
    screenshot_url: "http://localhost:3000/dashboard"   # optional (URL verify 時)
    timeout_seconds: 60          # 最大 120
  verify_result: pending          # pending | pass | fail | run_now (auto-runner 起動 sentinel)
  verify_output_path: null        # 実行時に logs/verify_{task_id}_{timestamp}.log が自動記録される
```

**運用フロー** (足軽):
1. verify.command を実行 → pass 確認
2. `verify_result: pass` + `verify_output_path: logs/...` を書込
3. `status: done` に変更 (PreToolUse CHK5 通過)

または auto-runner 利用:
1. `verify_result: run_now` 書込 → PostToolUse `posttool_verify_runner.sh` が verify を自動実行
2. 結果で `verify_result: pass|fail` + `verify_output_path` が書戻される
3. pass なら `status: done`

**URL verify 時のスクショ**: `verify.screenshot_url` があれば足軽が shogun-screenshot skill で保存し、`verify_output_path` にパス追記 (hook から skill 起動は Claude Code 仕様上不可)。

---

## 2. cmd YAML スキーマ (`queue/shogun_to_karo.yaml`)

### 2.1 cmd-level 必須フィールド

```yaml
commands:
- id: cmd_XXXX
  timestamp: "ISO 8601"
  lord_original: "殿の発言をそのまま記載 (加工・要約禁止)"   # CHK4 lint 対象
  north_star: "ビジネス目標への貢献"
  purpose: "完了条件 (1 文)"
  acceptance_criteria:
    - "具体的・検証可能な条件"
  command: |
    (タスク詳細)
  project: project-id
  priority: high | medium | low
  status: pending | in_progress | done
```

### 2.2 phase_gate 欄 (cmd_1443 p07 H9・多 Phase cmd 用)

cmd.command 内に "Phase N" キーワードが現れる場合 (cmd_1434 等)、各 Phase 境界での殿確認を機械化するため `phase_gate:` 欄を宣言せよ。

```yaml
  phase_gate: required          # required | optional | none (default: none)
  phases:                        # optional: Phase 番号と成果物を明示
    - n: 1
      deliverable: "両クリップ STT 完了・SRT 保存済"
      gate: "殿が SRT 品質 OK 判定"
    - n: 2
      deliverable: "panels JSON 生成済"
      gate: "殿が panel 構成 OK 判定"
    - n: 3
      deliverable: "panel_review.html 生成"
      gate: "殿が review OK 判定"
  lord_preconditions:            # optional: Phase ゲート以外の殿前提条件
    - "D10 (bloom_routing 復活) 決定済"
```

**運用**:
- 家老が Phase N 完了検知時、`scripts/phase_gate_checker.sh <cmd_id> <phase_n>` を呼ぶ
- checker が `scripts/ntfy.sh` で殿通知 + `dashboard.md` 🚨要対応セクションに自動追加
- 殿の「OK / NG / 修正」判断が来るまで Phase N+1 着手禁止
- 違反 (Phase チェックスキップ) は memory/feedback_phase_gate_check.md に既収録 (2026-04-11 殿激怒事例)

**適用対象 cmd** (H9 導入基準):
- cmd.command 内に `Phase 1` / `Phase 2` ... / `Wave A` / `Wave B` ... のキーワードが 2 つ以上現れる
- またはは `Phase N 完了時点で殿確認` 等のレビューゲート記載がある

**scan モード** (任意): `phase_gate_checker.sh --scan` で shogun_to_karo.yaml 全 cmd を走査し、`PHASE_GATE_WARNING: cmd_X has 'Phase' keyword but no phase_gate declared` を stdout 出力。結果は H9 の future hook 連携で利用予定。

---

## 3. pretool_check.sh lint チェック表

| ID | 対象 | 規制 | 既存 task regression 回避 |
|----|------|------|--------------------------|
| CHK1 | Bash tmux capture-pane | `-S -100` 以上必須 | 対象外 |
| CHK2 | 足軽の Write/Edit/Bash | work/cmd_* 直書込・/tmp 書込 BLOCK (target_path 一致は許可) | 常時 |
| CHK3 | task YAML Write/Edit | steps 多行 BLOCK | 常時 |
| CHK4 | shogun_to_karo.yaml 将軍編集 | 新規 cmd 起票に lord_original 欄必須 | 新規 cmd のみ |
| CHK5 | task YAML 編集 | verify: 宣言済 task の status:done 遷移を verify_result:pass 未達なら BLOCK | verify: 欄なしは素通り |
| CHK6 | advisor tool 呼出 | logs/advisor_calls.log 追記 (side-effect のみ・BLOCK しない) | 対象外 |
| CHK7 | queue/tasks/{ashigaru*,gunshi}.yaml 編集 | 新規 task_id に 9 必須フィールド欠落 BLOCK | NEW task_id のみ (既存素通り) |
| CHK8 | Bash `git add` | `.` / `-A` / `--all` / `*` / `-f .` を BLOCK (引用符・heredoc 誤検知回避) | 常時 |

---

## 4. 関連資産

- **pretool/posttool hook**: `.claude/settings.json` に wired
- **pretool_check.sh**: CHK1-CHK8 本体 (scripts/)
- **done_gate.sh**: CHK5 の統合ゲート (scripts/)
- **posttool_verify_runner.sh**: verify_result:run_now sentinel で自動実行 (scripts/)
- **phase_gate_checker.sh**: H9 Phase ゲート (scripts/・本書導入)
- **advisor_proxy.py**: GLM 経路 advisor 呼出 → logs/advisor_calls.log 記録 (scripts/)
- **cmd_template.md**: cmd 起票時の家老向けガイダンス (本 schema doc が verify 欄仕様の正式版)

---

## 5. 変更履歴

| 日付 | 変更 | 出典 subtask |
|------|------|-------------|
| 2026-04-24 | 初版作成 (verify:/phase_gate: 統合・CHK7/CHK8 文書化) | cmd_1443_p07 (ashigaru4) |
