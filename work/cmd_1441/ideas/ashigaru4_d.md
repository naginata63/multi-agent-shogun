# subtask_1441d: 設計書 / instructions 古記述棚卸しアイデア

- 担当: ashigaru4 / parent_cmd: cmd_1441 / 作成: 2026-04-24
- 範囲: CLAUDE.md, instructions/, shared_context/, config/settings.yaml, cmd_1404 系 (`--max-tokens` 廃止) の書換漏れ
- 範囲外: memory/ 個別ファイル棚卸し（subtask_1441e の領分）, スクリプト棚卸し（別レーン）
- 切り分け: 本タスク (d) は **古記述・古参照の発見と修正アイデア**。memory/MEMORY.md 等の **整理実行** は 1441e の領分。d で気付いた memory 関連の事象は §2 G7 に「指摘のみ」で記録した

---

## 1. 現状（done / verified）

| 項目 | 確認内容 | 根拠 |
|------|---------|------|
| `--max-tokens` 監査 | cmd_1404 で全件棚卸し完了。`work/cmd_1404/max_tokens_audit.md` に高リスク2件・低リスク1件が列挙済 | commit `18fde90` |
| 高リスク2件の修正 | `projects/dozle_kirinuki/context/remotion_llm_style_design.md:227` と `work/cmd_1393/design.md:169` の `--max-tokens` 文字列は現時点で grep 0 hit | `grep -rn "max-tokens" CLAUDE.md instructions/ shared_context/ projects/dozle_kirinuki/context/ work/cmd_1393/ → 0件` |
| posttool_cmd_check | `--max-tokens 100` を `--model opus --max-budget-usd 0.50` へ差替済 | commit `4445663` |
| dozle 子モジュール | `cmd_1435 --max-tokens removal` で submodule 同期済 | commit `69ed5b9` |
| STT パイプライン | `shared_context/procedures/stt_pipeline.md` / `udemy_stt.md` / `subtask_1429a.md` は AssemblyAI 準拠で記述済 | grep 結果 |
| 役割別 instructions の本体 | `instructions/{ashigaru,karo,gunshi,shogun}.md` は cmd_1441 直前まで継続更新（最終 4/24） | `ls -la instructions/` |
| 役割別 instructions の旧モデル参照 | grep `claude-3 / sonnet-4-5 / sonnet-4-6 / opus-4-6 / kimi / copilot / codex` → 役割本体ファイルでは hit 0 | grep 結果 |

---

## 2. やれてないこと（gap / 未対応）

優先度順。**(P0)** = 殿の判断必要 / 運用影響大。**(P1)** = 軽量整理。**(P2)** = 記録上の残骸。

### G1 (P0) `bloom_routing` 参照が壊れている

- **症状**: `instructions/karo.md` L95-129, L915 と `CLAUDE.md:60` (`bloom_routing_rule`) が `config/settings.yaml` の `bloom_routing` / `capability_tiers` を参照しているが、`config/settings.yaml`（49行）に該当キーが存在しない。
- **影響**: 家老の Step 6.5（Bloom Taxonomy L1-L6 モデルルーティング）の発火条件 `bloom_routing != 'off' in config/settings.yaml` が常に未定義。家老は「スキップ厳禁」と書かれているのに、判定不能のまま暗黙スキップされている可能性が高い。`bloom_level` フィールド自体は subtask_1441d (本タスク) や 1425c2 など各タスク YAML に付与運用が継続されているため、「ラベルだけ書いて動的切替は無効」という乖離状態。
- **citation**:
  - karo.md L120: `condition: "bloom_routing != 'off' in config/settings.yaml"`
  - CLAUDE.md L60: `bloom_routing_rule: "config/settings.yaml の bloom_routing 設定を確認せよ。autoなら家老はStep 6.5を必ず実行。スキップ厳禁。"`
  - settings.yaml (全49行) → grep `bloom_routing|capability_tiers` 0件

### G2 (P1) `instructions/{generated,cli_specific,common,roles}/` が死木

- **症状**: 4 サブディレクトリ計 26 ファイル全てが mtime `2026-03-02 12:04:32`。`build_instructions.sh` も 7 週間以上未実行。
- **整合性破綻**: GLM 移行・Opus[1m] 全面切替・Bloom routing・Phase A 構造などの直近変更が一切反映されていない。古い `claude -p --max-tokens` パターン例も残存（`copilot-*.md` 等）。
- **読まれているか**: 役割本体 4 ファイル (`shogun/karo/gunshi/ashigaru.md`) からは参照ゼロ。**唯一 `CLAUDE.md:51` のみが `instructions/common/task_flow.md` をコメントで参照**しているが、本文中で読み込み指示はない。
- **影響**: ファイル自体は害なしだが、新規エージェント・スクリプトが誤参照すれば古ルールで動く危険。リポ整理上のノイズも大きい。

### G3 (P2) `CLAUDE.md:51` の死リンク

- **症状**: `# - instructions/common/task_flow.md (Status Reference)` というコメント参照のみ残存。G2 と一体で扱える。
- **対処**: G2 を archive 化するなら本行も書換 or 削除。

### G4 (P2) `procedures/nightly_audit_video.md:15` に WhisperX 言及

- **症状**: `M2: main.py L658 --diarize WhisperX抜け穴 → cmd_1429aで警告追加`。WhisperX はメモリ上「禁止」。
- **判定**: 過去経緯の記録としては妥当だが、現役ガイドでもあるため「移行済」一文を追記して読者の混乱を防ぐ価値あり。CLAUDE.md L313/L320 の WhisperX 言及も同性質（過去事例の記録）。

### G5 (P2) `shared_context/procedures/panel_review_claude_gen.md:34` のモデル指定

- **症状**: `"--model", "claude-opus-4-6"` 固定。Opus は現状 `opus[1m]` (4.7) 統一方針。
- **判定**: 4-6 → 4-7 への置換、または `claude-opus-4-7` 表記に揃える。手順書経由で実行されると 4-6 が呼ばれて 4-7 統一の意図と乖離する。

### G6 (P2) `shared_context/advisor_proxy_design.md` の「サブスク内無料」記述

- **症状**: L12, L88, L127 等で「`claude -p` はサブスク内無料」前提。GLM 移行検討時 (memory `project_glm_migration_apr5`) と整合性確認が必要だが、現状は Opus[1m] 統一で再び Claude Max 環境のため「現時点では正しい」。
- **判定**: 直す必要は無いが、「サブスク前提」を明示する一行を入れておくと将来のモデル切替時に齟齬が出にくい。

### G7 (P2) `MEMORY.md` の自動ロード上限超過（指摘のみ・1441e 領分）

- **症状**: `memory/MEMORY.md` 292 行。`/home/murakami/.claude/projects/.../memory/` のサブディレクトリ仕様では 200 行以降は truncate。
- **判定**: 詳細整理は subtask_1441e に譲るが、d 側の発見として記録する（重複検知のため）。

---

## 3. アイデア（fix proposal — 5+）

### A1 (G1 対応)『bloom_routing 整流化』 ★最優先

**目的**: 現状の死リンクを解消し、karo の Step 6.5 を「実体ある運用」に戻す。

選択肢 2 つ。殿に判定を仰ぐ:

- **A1-a (運用復活案)**: `config/settings.yaml` に以下を追記:
  ```yaml
  bloom_routing: off   # auto | manual | off
  capability_tiers:
    L1: { type: claude, model: "haiku-4-5" }
    L2: { type: claude, model: "haiku-4-5" }
    L3: { type: claude, model: "sonnet-4-6" }
    L4: { type: claude, model: "opus[1m]" }
    L5: { type: claude, model: "opus[1m]" }
    L6: { type: claude, model: "opus[1m]" }
  ```
  まず `off` で commit → 動作確認後 `auto` 切替。
- **A1-b (簡素化案)**: 全エージェント Opus[1m] 統一が現方針なら、karo.md Step 6.5・L915 と CLAUDE.md L60 の `bloom_routing_rule` を削除し、`bloom_level` フィールドは「分類ラベル（参考値）」と定義し直す。

**推奨**: A1-b（現実 = 全 Opus[1m]、ルーティング不要）。A1-a を選ぶなら shogun-bloom-config スキルが既に対話 wizard を持っているので流用可。

### A2 (G2/G3 対応)『古 instructions サブディレクトリ archive 化』

- `instructions/{generated,cli_specific,common,roles}/` を `instructions/archive/202603/` へ `git mv`（履歴保持）。
- `scripts/build_instructions.sh` も同 archive へ移動（再生成しない方針なら）または `# DEPRECATED 2026-03-02 since` ヘッダ付与。
- `CONTRIBUTING.md:57` の記述更新（`build_instructions.sh` 言及行）。
- `CLAUDE.md:51` のコメント行を `# - instructions/karo.md / shogun.md (Status Reference)` 等の現役ファイルに書換、または削除。

### A3 (G4 対応)『WhisperX 言及への "AssemblyAI 移行済" 注記追記』

- `shared_context/procedures/nightly_audit_video.md:15` の WhisperX 行に `（cmd_1106 で AssemblyAI 移行済・WhisperX 経路は警告のみ残存）` を追記。
- CLAUDE.md L313/L320 の WhisperX 言及はそのまま残し、`Intermediate Artifact Rule` 章末に `※ STT 自体は AssemblyAI に移行済（memory feedback_stt_pipeline_location 参照）` 一行追加。

### A4 (G5 対応)『手順書のモデル名 4-6 → 4-7 統一』

- `shared_context/procedures/panel_review_claude_gen.md:34` の `claude-opus-4-6` を `claude-opus-4-7`（または settings.yaml の `cli.agents.<role>.model` を読む形）に書換。
- 同等の `opus-4-6` literal が他にないか確認後、まとめて 1 commit。

### A5 (G6 対応)『advisor_proxy_design.md にモード前提を明記』

- `shared_context/advisor_proxy_design.md` 冒頭に `## 前提環境` セクションを 3 行追加: 「Claude Max サブスク前提 / `claude -p` 無料利用 / GLM 環境では proxy 経由で同等動作」。将来のモデル切替時に齟齬を回避。

### A6『静的整合性チェッカー化（再発防止）』

- 上記 G1 のような「instructions が指す key が settings.yaml に無い」事故を再発させないため、既存スクリプト追加禁止ルールに鑑み `scripts/posttool_cmd_check.sh` 等の既存テスト系スクリプトに `lint:docs` サブコマンドを追加する形が望ましい。
- 検査内容: `karo.md` 中の `config/settings.yaml の <key> を参照` 文言と settings.yaml 実キーの突合。
- 段階導入: まず手動 grep ワンライナーをチェックリスト化 → 安定後にスクリプト化。

### A7『phase 切れの古いタスク YAML アーカイブ』

- 範囲外と思われるが d 観点で気付いた点として記録: `queue/tasks/ashigaru4.yaml` は 1024 行超。`CLAUDE.md` の Task YAML Format に「100件超えたら archive」とあるが運用未実施。Phase B 統合フェーズで `queue/tasks/archive/` 移動を検討する余地あり。

---

## 4. 殿/家老への問いかけ（即決事項）

- **Q1 (A1)**: bloom_routing は復活 (A1-a) か削除 (A1-b) か？ → 推奨 A1-b。
- **Q2 (A2)**: `instructions/{generated,cli_specific,common,roles}/` を archive 化してよいか？ git mv で履歴は残す。
- **Q3 (A6)**: docs lint を `posttool_cmd_check.sh` に統合してよいか？

---

## 5. 参考コマンド集

```bash
# G1 検証再現
grep -rn "bloom_routing\|capability_tiers" config/ instructions/ CLAUDE.md

# G2 死木検出
find instructions/{generated,cli_specific,common,roles} -type f -newer instructions/ashigaru.md
# → 0件出力なら全ファイル古い証拠

# 残存 --max-tokens 検出（false negative チェック）
rg -l "max[_-]tokens" --type md --type yaml --type sh --type py \
   | grep -v "venv\|node_modules\|/.git/\|queue/archive\|queue/cmd_archive\|data/semantic_index\|projects/note_mcp_server\|venv_whisper\|work/cmd_1408\|work/archive"
```
