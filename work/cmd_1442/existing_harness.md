# cmd_1442 Phase2: existing_harness.md

既存のハーネス・仕組み・自動化の棚卸し。failure_clusters.md の 5 クラスタに対するカバー範囲を明示する。

- **作成**: 2026-04-24 / gunshi (subtask_1442a)
- **先行**: work/cmd_1442/failure_clusters.md (Phase1)
- **目的**: 既存ハーネスで「すでに解決済」の領域を特定し、Phase3 harness_proposal.md で**穴 (gap) のみ**を新提案する

---

## 1. 既存ハーネス 一覧 (既知 17件)

| # | ハーネス | 種類 | 稼働状態 | 主機能 |
|---|---------|------|---------|-------|
| H1 | scripts/pretool_check.sh | PreToolUse hook | ✅ 稼働 | target_path 欠落検知・status: in_progress パターン検知・work/cmd_* 書込BLOCK |
| H2 | scripts/posttool_cmd_check.sh | PostToolUse hook | ✅ 稼働 | cmd完了検知・budget 制御 |
| H3 | scripts/posttool_yaml_check.sh | PostToolUse hook | ✅ 稼働 | YAML 編集後の整合性チェック (.venv/bin/python3 でパース) |
| H4 | scripts/precompact_hook.sh | PreCompact hook | ✅ 稼働 | エージェント別 snapshot (dashboard head / pane末尾) 生成 |
| H5 | scripts/inbox_watcher.sh | inotify daemon | ✅ 稼働 | inbox.yaml 変更検知→tmux send-keys nudge |
| H6 | scripts/inbox_write.sh | CLI | ✅ 稼働 | flock でメッセージ永続書込 |
| H7 | scripts/ntfy.sh + ntfy_listener.sh | 通知 | ✅ 稼働 | 殿のスマホへ ntfy 通知 |
| H8 | scripts/cmd_rotate.sh | rotation | 🔴 **50日停止中** | shogun_to_karo.yaml アーカイブ (500行/30KB閾値) |
| H9 | scripts/dashboard_rotate.sh | rotation | 🔴 **50日停止中** | dashboard.md アーカイブ (200行/10KB閾値) |
| H10 | scripts/cmem_search.sh | mem検索 wrapper | ✅ 稼働 (cmd_1440完了) | claude-mem の 3-layer 検索パターン化 |
| H11 | scripts/slim_yaml.sh + slim_yaml.py | YAML 圧縮 | ✅ 稼働 | task YAML 読込前の token 圧縮 |
| H12 | claude-mem v10.6.3 (5 hooks) | observation 蓄積 | ✅ 稼働・WORKER_HOST=0.0.0.0 | 12,166 obs / 1,757 sessions 自動蓄積 |
| H13 | shared_context/qc_template.md | QC 絶対ルール | ✅ 使用中 | 実ファイル読め・3箇所目視・証跡報告 |
| H14 | Session Start / Recovery procedure (CLAUDE.md) | 手順書 | ✅ 遵守 | tmux 自己識別 → read_graph → instructions 必読 |
| H15 | MEMORY.md Shogun Core Rules (鉄則集) | 手順書 | ✅ 参照 | 殿激怒・事故教訓の集約 (292行) |
| H16 | scripts/nightly_audit_*.sh (時刻 2:02) | 静的scan | ✅ 稼働 | STT/video/infra 系の矛盾検出 |
| H17 | scripts/semantic_search.py (crontab 毎時) | Gemini Embedding 検索 | ✅ 稼働 | scripts/srt/memory/context 意味検索 |

---

## 2. 失敗クラスタ × 既存ハーネス カバー範囲マトリクス

| クラスタ | (a)完了後未確認 | (b)dashboard残骸 | (c)silent fail | (d)hotfix独立発明 | (e)既存資産活用漏れ |
|---------|----------------|------------------|---------------|-------------------|-------------------|
| H1 pretool_check | — | — | — | ○ status検知 | — |
| H2 posttool_cmd_check | △ budget | — | — | — | — |
| H3 posttool_yaml_check | — | △ YAML整合 | — | △ lint | — |
| H4 precompact_hook | — | — | — | — | △ snapshot |
| H5 inbox_watcher | — | — | — | — | — |
| H6 inbox_write | — | — | — | — | — |
| H7 ntfy | △ 通知のみ | △ 🚨追加時 | △ 通知のみ | — | — |
| H8 cmd_rotate **停止** | — | 🔴 未稼働 | — | — | — |
| H9 dashboard_rotate **停止** | — | 🔴 未稼働 | — | — | — |
| H10 cmem_search | — | — | — | — | ○ 手動検索 |
| H11 slim_yaml | — | — | — | — | △ token節約 |
| H12 claude-mem | — | — | — | △ hotfix_notes蓄積 | ○ 蓄積のみ |
| H13 qc_template | ○ 実ファイル読めルール | △ | △ fallback鉄則 | △ 証跡 | △ |
| H14 Session Start | — | — | — | — | ○ read_graph |
| H15 MEMORY.md 鉄則集 | △ 精神論 | △ | △ | △ | △ |
| H16 nightly_audit | △ 静的scan | — | △ ルール違反検知 | — | — |
| H17 semantic_search | — | — | — | — | △ 意味検索 |

**凡例**: ○ = 強くカバー / △ = 部分的カバー / 🔴 = 本来カバーすべきが停止中 / — = 未対応

---

## 3. 大きな穴 (gap) 5つ

### 穴 G1 (クラスタ a): 完了後 curl/ブラウザ自動化が不在
- qc_template.md の **絶対ルール「実ファイル読め」は精神論**・自動化なし
- curl で動作確認、スクリーンショット取得のハーネスが存在しない
- → 将軍 H1 (完了後curl自動) に直結

### 穴 G2 (クラスタ b): rotate スクリプト 2本が停止中
- cmd_rotate.sh / dashboard_rotate.sh は実装済なのに **50日間 trigger 不発** (足軽3号 c カテゴリ C-7 発見)
- shogun_to_karo.yaml ↔ dashboard.md の status 同期もハーネス化されていない
- → 将軍 H2 (dashboard 残骸 clean) + H5 (cmd YAML lint) に直結

### 穴 G3 (クラスタ c): log warn/fallback 自動検知が不在
- ntfy は手動送信のみ・**ログを監視して自動通知する hook がない**
- feedback_fallback_is_abnormal の鉄則を守る自動化なし
- → 将軍 H4 (silent fail 検知) の核心

### 穴 G4 (クラスタ d): hotfix_notes 横断集計が不在
- 各足軽が hotfix_notes 付けるが **集計・パターン抽出は軍師人力**
- 同一 hotfix が N 回発生したら自動で skill 化提案するフローなし
- claude-mem は蓄積するが能動抽出 skill なし
- → 将軍 H7 (hotfix 3回→skill 提案) の核心

### 穴 G5 (クラスタ e): cmd 発令前 mem-search 自動呼出が不在
- cmem_search.sh は手動のみ・**cmd 起票時に自動実行される仕組みなし**
- 「cmd_XXXX と類似 cmd があるか」が任意チェック → 車輪再発明継続
- → 将軍 H3 (mem-search 自動) + H8 (hit0 警告) の核心

---

## 4. 副次的な穴 (gap minor)

- **G6**: claude-mem dateRange bug (軍師 J テーマ2 既知)・`/api/observations` の dateStart/End がサイレント無視・回避ガイド未整備 → feedback_claude_mem_daterange_broken.md 新設 (cmd_1441 p11-v2 Wave1A で進行予定)
- **G7**: cron インベントリ一元化がない・kill_orphan_chrome 毎分過剰・失敗時アラート経路なし (gunshi_j テーマ3)
- **G8**: feedback_*.md 60件の quarterly レビュー未実施・形骸化検知なし (gunshi_j テーマ4)
- **G9**: advisor 呼出率の追跡なし・task YAML 要件 2回必須だが履行追跡が軍師人力 QC のみ
- **G10**: 殿激怒 → memory 追加 が将軍手動・自動化ハーネスなし

---

## 5. 稼働中ハーネスの活用強化候補

新規ハーネスを作らず既存を拡張するだけで済む領域:

| 強化候補 | 既存ハーネス | 拡張内容 | コスト |
|---------|------------|---------|--------|
| S1 | H8/H9 rotate 停止復活 | precompact_hook.sh から起動 (gunshi_j C-7) | LOW (1h) |
| S2 | H1 pretool_check | regex `(assigned|in_progress)` + target_path alert 到 karo | LOW (1h・p03-v2 で進行中) |
| S3 | H3 posttool_yaml_check | YAML 重複 status キー検知追加 (ashigaru2_b B-4) | LOW (30min) |
| S4 | H7 ntfy | レベル分け wrapper `ntfy_send.sh "level:title:body"` (p08-v2 で進行中) | MED (2-3h) |
| S5 | H16 nightly_audit | dashboard_archive ↔ shogun_to_karo.yaml 整合性 nightly check (ashigaru2_b B-5) | MED (2h) |
| S6 | H12 claude-mem | dateRange bug 回避ガイド + keyword 単独+created_at 手動filter パターン (cmd_1441 p11-v2) | LOW (30min) |
| S7 | H13 qc_template | severity 数値化 + 冪等性チェック + schema (cmd_1441 p24 相当・gunshi_j テーマ1) | MED (2-3h) |

---

## 6. Phase3 提案の方向性

既存ハーネスの穴 G1〜G10 を埋めるため、**shell/hook/既存 skill 拡張を基本**に新 H1〜H15 ハーネスを評価する。新規 .py 禁止ルール (CLAUDE.md) に準拠。

Phase3 で評価する項目:

| Phase3 評価項目 | 対応クラスタ | 既存ハーネス強化 vs 新設 |
|---------------|-------------|-------------------------|
| H1 完了後curl自動 | (a) | **新設** (完了判定フック) |
| H2 dashboard残骸clean | (b) | S1 rotate復活 + **新設 lifecycle hook** |
| H3 mem-search自動 | (e) | **新設** (cmd起票時hook) |
| H4 silent fail検知 | (c) | **新設** (log tail→ntfy) |
| H5 cmd YAML lint | (b)(d) | **S3 posttool_yaml_check 拡張** |
| H6 LLM選定ガイド | メタ | **新設** (文書化のみ) |
| H7 hotfix 3回→skill提案 | (d) | **新設** (claude-mem hook + 集計) |
| H8 mem-search hit0警告 | (e) | **新設** (cmd_発令前 hook) |
| H9 Phase間殿ゲート | メタ | **文書化 + ntfy wrapper S4 強化** |
| H10 advisor呼出率メトリクス (軍師独自) | 全般 | **新設** (hook + ログ) |
| H11 殿激怒→memory自動追加 (軍師独自) | 全般 | **新設** (slash command or skill) |
| H12 cron インベントリ統合 (gunshi_j由来) | メタ | **新設** (shared_context/cron_inventory.md) |
| H13 月次 feedback レビュー cron (gunshi_j由来) | (e) | **新設** (cron + dashboard連携) |
| H14 log warn 自動 ntfy (軍師独自) | (c) | S4 ntfy_send + **新設 log watcher** |
| H15 hotfix_notes 横断集計 cron (軍師独自) | (d) | **新設** (cron + dashboard🚨追加) |

---

以上、既存17ハーネス × 5クラスタ のカバー範囲マトリクスと穴 G1〜G10 を整理。Phase3 (harness_proposal.md) で H1-H15 を 4 軸評価し、shell/hook/既存 skill 拡張で実装する新ハーネスを提案する。
