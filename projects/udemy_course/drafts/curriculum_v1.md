# Udemy講座カリキュラム v1
## 「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全実践」

- 版: v1
- 作成: 2026-04-24 / 足軽7号 (subtask_cmd_1445)
- 出典: memory/project_udemy_3engineering.md + work/cmd_1444/* + cmd_1442/1443 実装実績
- 想定受講生: Claude Code または類似 AI コーディングエージェントを業務利用しているソフトウェアエンジニア・情報発信者。社内ワークフロー自動化を自分で設計・運用したい中〜上級者
- Bloom レベル: L6 (Create) — 受講後、受講生は自分のプロジェクトに 3 階層統合システムを「構築」できる

---

## 0. 講座全体設計

### 0.1 本講座の立ち位置（市場調査結果）

Udemy 日本語圏で「プロンプト/コンテキスト/ハーネス」各単独講座は複数存在するが、**3 階層を通貫して実装まで踏み込む講座は 2026-04-24 時点でゼロ** (cmd_1444 調査結果 `work/cmd_1444/udemy_engineering.json` 60 件解析)。

| 階層 | 既存ベストセラー例 | 既存の到達点 | 本講座の差分 |
|------|-------------------|-------------|-------------|
| L1 プロンプト | 国内ベストセラー複数 (10+ 件) | 単発プロンプト設計まで | プロジェクト全体の階層設計の中で位置づけ |
| L2 コンテキスト | 国内ベストセラー 2 件 (コンテキストエンジニアリング入門系 / Agent Skills 解説系) | エディタ単体での第二の脳 | 9 体マルチエージェント間のコンテキスト分配・永続化 |
| L3 ハーネス | 国内ベストセラー 2 件 (ハーネスエンジニアリング概論系 / ハーネス設計ガイド系) | 概論または設計ガイド | `scripts/*.sh` 18 本 + cmd_1442 採用 12 ハーネスの生産実装 |
| 3 階層統合 | **該当なし** | — | cmd_1443 で実装した三層アーキを flagship 教材化 |

### 0.2 カリキュラム構成

```
序章                     :  30 min × 1 本  (無料プレビュー)
L1 プロンプト基礎       :  45 min × 4 本
L2 コンテキスト実装     :  60 min × 5 本
L3 ハーネス実装 12 例   :  60 min × 6 本
L3 flagship case study  :  90 min × 1 本  (cmd_1443 三層アーキ)
総合演習                :  60 min × 2 本
附録 (差別化・ビジネス導線・トラブルシュート): 30 min × 3 本

合計: 22 レクチャー / 約 18 時間
```

### 0.3 受講生の最終成果物 (L6 Create)

受講完了時、受講生は以下 5 点を自分のリポジトリに保有している:

1. `CLAUDE.md` + `instructions/*.md` セット (L2 実装)
2. `SessionStart` / `PreToolUse` / `PostToolUse` / `Stop` / `PreCompact` 各ライフサイクルに対応した hook スクリプト 5 本以上 (L3 実装)
3. claude-mem または同等メモリバックエンドへの `add_observations` 自動経路 (L2+L3 統合)
4. `queue/inbox/*.yaml` + `inbox_watcher.sh` 相当のメールボックス (マルチエージェント化の土台)
5. 自分のドメインに合わせた `cmd_intake_hook.sh` (起票時 mem-search + 4 系統自動 add_observations) の動くコード

### 0.4 受講前提

- Claude Code または同等 CLI (Cursor / Cline / Codex CLI 等) の基本操作経験
- シェルスクリプト (bash) の読み書き可能レベル
- git 基本操作

---

## 序章: AI 開発 3 階層モデルとは (L0: Remember + Understand)

**所要**: 30 min / **無料プレビュー**

### 学習目標
- 3 階層 (L1 プロンプト / L2 コンテキスト / L3 ハーネス) の定義を自分の言葉で説明できる
- なぜ単独層では「AI が変な返事をする」「文脈を忘れる」「同じ失敗を繰り返す」が解消しないかを階層別に切り分けられる
- 本講座の終着点 (L6 Create) を把握する

### アウトライン
1. 3 階層モデル図 (1 枚スライド・全講座通貫)
2. 各層の failure mode 実例 3 本ずつ
3. 既存ベストセラー講座マップと本講座の位置づけ
4. 最終成果物ツアー (受講後の受講生のリポジトリを 3 分で見せる)

### 成果物
- なし (視聴のみ)

### 差別化ポイント
「第 0 講で構築済みリポジトリをまず見せる」= Marketing Trip 著者流 before/after 提示。受講動機を冒頭で固定する。

---

## L1 プロンプトエンジニアリング基礎 (章 1-4)

L1 は既存ベストセラー多数の飽和領域。本講座では **「L2/L3 と噛み合うプロンプトとは何か」** に絞り込み、既存講座との重複を避ける。

### 第 1 章 プロンプトを「関数」として設計する

**所要**: 45 min / Bloom: L3 Apply

#### 学習目標
- プロンプトを (入力契約・処理指示・出力契約) の 3 パートで構成できる
- 失敗プロンプトを診断し、どのパートが壊れているか特定できる

#### アウトライン
1. 「指示」ではなく「関数シグネチャ」発想 (入力/出力の型を決める)
2. 3 パート構成テンプレ (`<input>` + `<task>` + `<output_format>`)
3. 既存ベストセラー講座との差分: 本講座は「L2 コンテキストから渡す入力」を想定した設計

#### 演習課題
- 受講生の日常業務タスク 1 件を選び、口頭指示 → 3 パート関数プロンプト化。before/after を提出

#### 成果物
- `prompts/task_XX_v1.md` (受講生リポジトリに保存)

### 第 2 章 構造化プロンプトと失敗パターン

**所要**: 45 min / Bloom: L4 Analyze

#### 学習目標
- Chain-of-Thought / Few-shot / XML タグ構造化 の 3 技法を使い分けできる
- ハルシネーション・指示無視・出力崩壊 の 3 大 failure mode を再現実験で観察できる

#### アウトライン
1. CoT / Few-shot / XML タグ それぞれの適用判断フローチャート
2. 失敗プロンプトライブラリ (実例 9 本・すべて殿プロジェクトの実事故から採取)
3. 診断 checklist (10 項目)

#### 演習課題
- 用意された failure プロンプト 3 本を、受講生自身で診断 → 修正 → 再実行し、修正前後の出力を比較レポート化

#### 成果物
- `prompts/diagnoses/case_1-3.md`

### 第 3 章 「階層的プロンプト」: CLAUDE.md / instructions / task YAML の役割分担

**所要**: 45 min / Bloom: L4 Analyze + L5 Evaluate

#### 学習目標
- プロジェクト全体ルール (CLAUDE.md) / 役割別指示 (instructions/\*.md) / タスク指示 (task YAML) の責任境界を設計できる
- 1 つのプロンプトを 3 層に分解するリファクタリング手順を実行できる

#### アウトライン
1. 「全部 CLAUDE.md に書く」アンチパターン (殿プロジェクトで実際に context 爆発した事例)
2. 3 層分解アルゴリズム (フローチャート 1 枚)
3. 変更頻度 × 適用範囲 のマトリクスで置き場所を決定

#### 演習課題
- 受講生既存プロジェクトの CLAUDE.md を解析 → 3 層分解提案書を作成 → 実際に分解して commit

#### 成果物
- `CLAUDE.md` (スリム化後) + `instructions/*.md` 複数

### 第 4 章 プロンプト品質 Gate: advisor() と QC template

**所要**: 45 min / Bloom: L5 Evaluate

#### 学習目標
- 自作プロンプトを実行前に別モデル (Opus / GPT-5 等) でレビューする advisor パターンを実装できる
- QC template (PASS/FAIL 判定基準) を自プロジェクト用に設計できる

#### アウトライン
1. advisor 呼出の実装 3 方式 (claude-agent-sdk / CLI 2 回呼び出し / proxy 横取り) と費用比較
2. QC template の作り方 (殿プロジェクトの `shared_context/qc_template.md` を教材化)
3. L1 プロンプトに advisor を組み込む際の落とし穴 (fabrication 許容の緩さ等)

#### 演習課題
- 受講生の第 1 章成果物プロンプトに advisor 呼出を追加 → 5 件の自プロジェクトタスクで QC template で評価

#### 成果物
- `scripts/advisor_wrap.sh` (受講生オリジナル) + `shared_context/qc_template.md`

---

## L2 コンテキストエンジニアリング実装 (章 5-9)

L2 は Cursor × Obsidian 等の既存ベストセラーが存在するが、エディタ単体または個人ユース止まり。本講座は **9 体マルチエージェント構成** を前提にコンテキスト配分を設計する。

### 第 5 章 コンテキストウィンドウ経済学

**所要**: 60 min / Bloom: L4 Analyze

#### 学習目標
- Opus 1M / Sonnet 200K / Haiku 200K のコンテキスト予算を実運用数字で設計できる
- Auto-compact / /clear / summary 生成 の 3 イベントでロスする情報を予測できる

#### アウトライン
1. コンテキスト消費源 3 大カテゴリ (ツール結果・ファイル読込・会話履歴) と計測方法
2. 殿プロジェクトの実コンテキスト予算 (claude-mem 12K observations / MEMORY.md 118 行 / instructions 平均 350 行)
3. 予算超過の failure mode と復旧コスト

#### 演習課題
- 受講生プロジェクトの直近 1 週間のセッションを tokens 計測 → 消費源マトリクス作成

#### 成果物
- `reports/context_budget_analysis.md`

### 第 6 章 永続コンテキスト層 (claude-mem / MCP memory / Agent Skills)

**所要**: 60 min / Bloom: L4 Analyze + L5 Evaluate

#### 学習目標
- claude-mem (file-based) / MCP memory (graph) / Agent Skills (knowledge) の 3 バックエンドを使い分けできる
- 「コードから分かることを memory に書くな」ルールを自プロジェクトに適用できる

#### アウトライン
1. 3 バックエンド比較表 (永続性・検索性・容量・コスト)
2. memory 書き込みルール 4 箇条 (user/feedback/project/reference)
3. MEMORY.md 索引ファイルの設計パターン (殿プロジェクト 118 行実例を逐行解説)

#### 演習課題
- 受講生が過去 1 ヶ月に学んだ教訓 10 件を、4 カテゴリに分類 → memory/*.md + MEMORY.md に落とし込む

#### 成果物
- `memory/*.md` + `memory/MEMORY.md`

### 第 7 章 セッション再起動耐性 (SessionStart / PreCompact / rehydrate)

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### 学習目標
- SessionStart hook で「自己識別 → memory 読み込み → 役割指示読み込み → YAML キュー復元」の 4 段階復旧を実装できる
- PreCompact hook で「要約圧縮前に保存したい情報」をファイルに吐き出せる
- /rehydrate slash で明示的にセッション復元できる

#### アウトライン
1. 再起動が起きる 4 シナリオ (/clear / auto-compact / crash / user quit) と各シナリオの情報ロス
2. SessionStart hook テンプレ (殿プロジェクト `scripts/sessionstart_hook.sh` を教材化)
3. PreCompact hook で `queue/precompact/{agent}.yaml` を保存するパターン
4. /rehydrate slash command 実装 (`.claude/commands/rehydrate.md`)

#### 演習課題
- 受講生プロジェクトに SessionStart hook を実装 → 意図的に /clear → 完全復旧するか自己テスト

#### 成果物
- `scripts/sessionstart_hook.sh` + `scripts/precompact_hook.sh` + `.claude/commands/rehydrate.md`

### 第 8 章 マルチエージェント間のコンテキスト配分

**所要**: 60 min / Bloom: L6 Create

#### 学習目標
- エージェント別の役割 YAML (`instructions/shogun.md` 等) で役割・禁止行動・通信プロトコルを定義できる
- `inbox_watcher.sh` 相当のメールボックス基盤を実装できる
- エージェント間の責任境界 (「実装は足軽・管理は家老」「QC は軍師」等) を設計できる

#### アウトライン
1. エージェント階層設計 (殿プロジェクト 4 層: Shogun / Karo / Ashigaru / Gunshi)
2. メールボックス (`queue/inbox/*.yaml` + flock + inotifywait) 実装コード読解
3. Chain of command と bypass 禁止ルールの自動検出 (PreToolUse hook で `to_shogun_allowed: false` をチェック)

#### 演習課題
- 受講生プロジェクトに 2 体エージェント構成 (親/子) を立ち上げ → 1 タスクを親から子に委譲 → 子からの報告を親が受領する最小動作ループを実装

#### 成果物
- `queue/inbox/*.yaml` + `scripts/inbox_watcher.sh` + `scripts/inbox_write.sh` + `instructions/{親役割}.md` + `instructions/{子役割}.md`

### 第 9 章 コンテキスト劣化検出と自動更新

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### 学習目標
- memory 内容の staleness を検出するルール (「名前付きファイルパスは存在確認」等) を設計できる
- 週次/月次で memory レビュー cron を実装できる

#### アウトライン
1. 「メモリは snapshot in time」原則と staleness 判定 3 ルール
2. `scripts/cmd_1443_p10` で実装した月次 feedback レビュー cron を教材化
3. semantic search (`scripts/semantic_search.py`) による memory 横断検索の実装
4. 実事例参照: cmd_1441 (cmem Phase2/3 todolist 整理 + MCN 申請 + スキル化候補 3 カテゴリ統合) を「memory staleness 検出と再整理」のケーススタディとして提示

#### 演習課題
- 受講生プロジェクトの memory/*.md を staleness 判定 → 古い記述を更新 or 削除するレビュースクリプト実装

#### 成果物
- `scripts/memory_review.sh` (cron 実行可能な形式)

---

## L3 ハーネスエンジニアリング実装 (章 10-15)

L3 は本講座の**差別化の核**。既存ベストセラー 2 本はマイクロラーニング概論止まりで、運用規模の実装例が市場に存在しない。

### 第 10 章 ハーネスとは: Claude Code lifecycle 7 イベント

**所要**: 60 min / Bloom: L2 Understand + L3 Apply

#### 学習目標
- Claude Code の 7 イベント (SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Stop / PreCompact / Notification) の発火タイミングを正確に説明できる
- 各イベントでできること・できないことを切り分けできる

#### アウトライン
1. 7 イベント flow 図 (1 枚スライド)
2. 各イベントで受け取れる入力・変更できる出力
3. `.claude/settings.json` hook 登録の書式
4. 「このイベントで解決したい問題は何か」決定マトリクス

#### 演習課題
- 受講生プロジェクトに最小の PreToolUse hook (特定コマンド実行時に echo するだけ) を登録 → 実動作確認

#### 成果物
- `.claude/settings.json` 編集 + `scripts/hook_hello.sh`

### 第 11 章 完了 Gate ハーネス (H1 + H10 統合型)

**所要**: 60 min / Bloom: L6 Create

#### 学習目標
- PostToolUse hook で「完了条件」を機械的に検証する done_gate を実装できる
- advisor 呼出率メトリクスを PostToolUse hook 内で計測できる
- 「人間の目視」に頼らない完了判定を設計できる

#### アウトライン
1. 「完了」と「未完了の完了報告」が混在する失敗パターン (殿プロジェクト実事故)
2. `scripts/done_gate.sh` コード読解 (cmd_1443_p01 実装を逐行解説)
3. advisor 呼出回数を log から抽出し、完了率に反映するロジック

#### 演習課題
- 受講生プロジェクトのタスク完了条件を 5 項目以上リスト化 → `done_gate.sh` に移植 → 未達時 ERROR 返す PostToolUse hook として登録

#### 成果物
- `scripts/done_gate.sh` (受講生プロジェクト版)

### 第 12 章 silent fail 検出ハーネス (H4)

**所要**: 60 min / Bloom: L6 Create

#### 学習目標
- log ファイルを inotifywait で監視する daemon を設計できる
- 「成功報告だが実際は失敗」パターンを log 文字列から検出できる
- self-feedback loop を防ぐ exclusion filter を実装できる

#### アウトライン
1. silent fail 定義と殿プロジェクトでの実観測事例
2. `scripts/silent_fail_watcher.sh` (cmd_1443_p04) コード読解
3. systemd user service 化による常駐運用
4. WARN buffer aggregation / flusher パターン

#### 演習課題
- 受講生プロジェクトの直近 1 週間の log から silent fail 候補パターンを 3 個抽出 → watcher に組み込み → 再現テスト

#### 成果物
- `scripts/silent_fail_watcher.sh` + systemd user service unit file

### 第 13 章 Phase 間ゲートと cmd intake ハーネス (H3 + H8 + H9)

**所要**: 60 min / Bloom: L6 Create

#### 学習目標
- cmd 起票時に自動で mem-search を実行する PreToolUse hook を実装できる
- 4 系統 (cmem obs / MCP entity / feedback file / dashboard archive) 自動 add_observations を設計できる
- Phase 間で人間のチェックゲートを強制するスキーマ拡張を設計できる

#### アウトライン
1. cmd 起票時の「過去事例検索忘れ」問題と自動化による解消
2. `scripts/cmd_intake_hook.sh` (cmd_1443_p03 = 本プロジェクト実装) コード読解 (※第 16 章 flagship で詳述)
3. Phase 間ゲートの YAML schema (`phase_gate_required: true`) と ntfy 強制通知

#### 演習課題
- 受講生プロジェクトの cmd 書式に mem-search pre-hook を追加 → 過去類似事例がある場合に警告を表示するよう実装

#### 成果物
- `scripts/cmd_intake_hook.sh` (受講生版) + cmd YAML schema 拡張

### 第 14 章 殿激怒を feedback 自動化する lord-angry slash (H11)

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### 学習目標
- ステークホルダー (殿/上司/顧客) の強い不満発言を半自動で feedback 文書に落とし込む slash command を設計できる
- 「自動 commit 禁止・レビュー方式」の半自動パターンを実装できる

#### アウトライン
1. フィードバックの属人化・暗黙知化問題
2. `.claude/commands/lord-angry.md` (cmd_1442 H11 = cmd_1443_p08) の設計思想
3. レビュー方式 (y 承認 / e 修正 / n 破棄) 実装パターン

#### 演習課題
- 受講生のステークホルダー過去発言から強い不満 3 件を抽出 → lord-angry slash の対象パターンを自プロジェクト用にカスタマイズ

#### 成果物
- `.claude/commands/{受講生のステークホルダー名}-angry.md`

### 第 15 章 残り 7 ハーネスカタログと選定判断

**所要**: 60 min / Bloom: L4 Analyze + L5 Evaluate

cmd_1442 で採用された 12 ハーネス (H1-H13 minus H6) のうち、第 11-14 章で扱った 4 件を除く 8 件を概観し、受講生が自プロジェクトに「どれを採用すべきか」を判断できるようにする。

#### 学習目標
- 12 ハーネスそれぞれの適用条件・コスト・期待効果を比較できる
- 自プロジェクトの failure profile から、採用すべきハーネスを 3 件以上選定できる

#### アウトライン (カタログ)

| ID | ハーネス名 | 主問題 | 実装 | 適用条件 |
|----|-----------|-------|------|---------|
| H2 | dashboard 残骸 lifecycle hook | 判断フラグの消し忘れ | `scripts/context_watcher.sh` + nightly_audit | dashboard 運用ありの場合 |
| H5 | cmd YAML lint (PreToolUse) | YAML schema 違反の検出遅延 | `scripts/posttool_yaml_check.sh` 拡張 (yq) | タスク発令が YAML ベース |
| H7 | hotfix 3 回 → skill 提案 cron | 場当たり修正の常態化 | weekly cron + claude-mem 集計 | 場当たり修正を report に書く習慣あり |
| H12 | cron_inventory + quarterly review | cron の blackbox 化 | `shared_context/cron_inventory.md` + nightly_audit | cron 3 本以上運用 |
| H13 | 月次 feedback レビュー cron | feedback 肥大化・staleness | monthly cron + dashboard 連携 | memory/feedback_*.md 20 本以上 |
| (補) pretool_check.sh | ファイルパス違反事前阻止 | 書き込み事故 | PreToolUse hook | Write/Edit の誤爆リスクあり |
| (補) userprompt_ntfy_check.sh | 通知漏れ | UserPromptSubmit hook | スマホ連携運用 |
| (補) watcher_supervisor.sh | watcher 自体の停止 | daemon 監視 | watcher 3 本以上 |

(注: `scripts/` には上記 + pretool_check_relpath / ratelimit_check / semantic_index_hook / stop_karo_check / filechanged_cmd_check / cron_health_check / gcp_billing_check / sasuu_quality_check / genai_check_urls / posttool_cmd_check / stop_hook_inbox / precompact_hook 等、合計 18 本程度の hook/watcher が運用中。受講生は第 15 章で自プロジェクトに必要な 3-5 本だけを採用する方針)

#### 演習課題
- 受講生プロジェクトの直近 1 ヶ月の失敗記録を整理 → 12 ハーネス中 3 件を選定 → 選定理由と期待効果を選定表に記述

#### 成果物
- `reports/harness_selection.md` (選定表 + 採用計画)

---

## 第 16 章 flagship case study: cmd_1443 三層アーキ (L1+L2+L3 統合)

**所要**: 90 min / Bloom: L6 Create / **本講座最重要章**

本プロジェクト cmd_1443_p03 で実装された **三層アーキテクチャ** を 1 章で通しで解剖する。3 階層統合の実例として、本講座で学んだすべてが 1 つの hook スクリプトに結実する。

### 学習目標
- L1 (プロンプト設計) / L2 (コンテキスト注入) / L3 (hook) を 1 つの機能に統合する設計を再現できる
- 「primary API が死んだ時の fallback 3 点」パターンを自プロジェクトに適用できる

### 学習の流れ
1. **問題設定** (10 min): cmd 起票時に過去事例を検索し忘れる → 似た事故を繰り返す問題
2. **L1 層の設計** (15 min): mem-search クエリ文の生成ルール (awk + 日本語名詞抽出)
3. **L2 層の設計** (20 min): 4 系統自動 add_observations の設計
   - (i) cmem obs POST `/api/observations`
   - (ii) `mcp__memory__add_observations` (rule_yaml_first)
   - (iii) feedback_*.md: 殿激怒キーワード検出で lord-angry slash 予約
   - (iv) dashboard_archive/ に cmd 追記
4. **L3 層の設計** (20 min): PreToolUse hook 登録と shogun_to_karo.yaml 編集時発火
5. **fallback 3 点** (15 min): primary が死んでも学びが失われない設計
   - 監査ログ: `logs/cmd_intake_obs.jsonl` (将来 API 対応時に一括再取込可能)
   - pending queue: `queue/pending_mcp_obs.yaml` (MCP 側が生きた時に消化)
   - SessionStart ingest: Shogun/Karo/Gunshi が起動時に pending queue を消化
6. **失敗事例と教訓** (10 min): 実装中に遭遇した 3 つの落とし穴

### 演習課題
- 受講生プロジェクトに同等の「起票時自動補完 + 4 系統保存 + 3 系統 fallback」を実装
- primary メモリが落ちた状態で起票 → fallback 3 点が動くことを自己テスト

### 成果物
- `scripts/cmd_intake_hook.sh` (受講生版・3 層統合)
- `scripts/cmem_search.sh` (受講生版)
- `logs/cmd_intake_obs.jsonl` (監査ログ)
- `queue/pending_mcp_obs.yaml` (fallback queue)
- SessionStart hook ingest ブロック

---

## 総合演習 (章 17-18)

### 第 17 章 総合演習 Part 1: 自プロジェクトに 3 階層統合を組み込む

**所要**: 60 min / Bloom: L6 Create

受講生が第 1-16 章で作った個別成果物を**統合**する。

#### 演習内容
- Step 1: 受講生プロジェクトの現状診断 (3 階層別の成熟度評価)
- Step 2: Gap 分析 → 補完計画
- Step 3: 1 週間分の実装ロードマップ作成
- Step 4: Day 1 分実装に着手

#### 成果物
- `plans/3layer_roadmap.md` + Day 1 実装 commit

### 第 18 章 総合演習 Part 2: 2 体マルチエージェント化 + ハーネス 3 件

**所要**: 60 min / Bloom: L6 Create

第 8 章の 2 体エージェント構成に、第 11/12/13 章のハーネスから 3 件を選んで組み込む。

#### 演習内容
- 親エージェント → 子エージェント委譲フローに done_gate / silent_fail_watcher / cmd_intake_hook を組み込む
- 意図的に failure 注入 → ハーネスが検出・ブロックすることを確認

#### 成果物
- 動く 2 体マルチエージェント + 3 ハーネスのリポジトリ

---

## 附録

### 附録 A. 差別化戦略 (30 min)

本講座が市場でユニークな理由と、受講生が **自分の講座/記事/案件** に応用する際のテンプレ。

#### 内容
- 「3 階層統合は市場ゼロ」調査根拠 (cmd_1444 60 件分析データ公開)
- 9 体マルチエージェント実運用の weight (既存ベストセラーは 1-2 体)
- 18 hook 実装カタログ (既存ベストセラーは概論止まり)
- 受講生が自分のニッチを見つける 3 ステップフレームワーク

### 附録 B. ビジネス導線設計 (30 min・オプション)

本講座の後ろに何を置くかの設計論。Marketing Trip メソッド (work/cmd_1444/udemy_strategy_summary.md + marketing_trip_videos_summary.md) を参照。

#### 内容
- Udemy 入門 3-5h 枠 1,000 円フロント (Marketing Trip メソッド標準パターン) → ボーナスレクチャー → 32% オプトイン → DRM ※本講座 18h 本編は中級価格帯 (3,000-4,980 円) 想定・v2 U3 で入門 3-5h 分割版との関係を確定
- house list 300 名 → 5% 成約 → 年 1000 万
- AI 開発コンサル / マルチエージェント構築受託 / オンラインスクール の単価レンジ
- 本講座受講生が自分のバックエンド商品を設計するワークシート

※ この附録は「講座ペダゴジー」ではなく「ビジネス展開」の副読材扱い。必要な受講生のみ視聴。

### 附録 C. トラブルシュート集 (30 min)

本講座の実演中に遭遇しやすい問題と対処。

#### 内容
- Claude Code 設定ファイル競合
- hook が発火しない 5 大原因
- claude-mem 書き込み失敗時の復旧
- マルチエージェント pane が死んだ時の再起動手順
- cost 爆発の防衛策 (batch size / advisor frequency / context budget)

---

## 章別サマリ表

| # | 章 | 所要 | Bloom | 成果物 |
|---|----|------|-------|--------|
| 0 | 序章 | 30 min | L0 | なし (無料プレビュー) |
| 1 | プロンプトを関数として | 45 min | L3 | `prompts/task_XX_v1.md` |
| 2 | 構造化と failure 診断 | 45 min | L4 | `prompts/diagnoses/*.md` |
| 3 | 階層的プロンプト (CLAUDE.md 分解) | 45 min | L4-L5 | CLAUDE.md + instructions/\*.md |
| 4 | advisor + QC template | 45 min | L5 | `scripts/advisor_wrap.sh` + `qc_template.md` |
| 5 | コンテキスト経済学 | 60 min | L4 | `reports/context_budget_analysis.md` |
| 6 | 永続コンテキスト 3 バックエンド | 60 min | L4-L5 | `memory/*.md` + `MEMORY.md` |
| 7 | 再起動耐性 (SessionStart + PreCompact + rehydrate) | 60 min | L5-L6 | 3 hook + slash |
| 8 | マルチエージェント間コンテキスト配分 | 60 min | L6 | inbox 基盤 + 2 役割 instructions |
| 9 | コンテキスト劣化検出・自動更新 | 60 min | L5-L6 | `scripts/memory_review.sh` |
| 10 | ハーネスとは (lifecycle 7 イベント) | 60 min | L2-L3 | 最小 PreToolUse hook |
| 11 | 完了 Gate (H1+H10) | 60 min | L6 | `scripts/done_gate.sh` |
| 12 | silent fail 検出 (H4) | 60 min | L6 | `scripts/silent_fail_watcher.sh` + unit file |
| 13 | cmd intake + Phase gate (H3+H8+H9) | 60 min | L6 | `scripts/cmd_intake_hook.sh` + schema |
| 14 | lord-angry slash (H11) | 60 min | L5-L6 | `.claude/commands/{ステークホルダー}-angry.md` |
| 15 | 残り 7 ハーネスカタログ + 選定 | 60 min | L4-L5 | `reports/harness_selection.md` |
| **16** | **flagship: cmd_1443 三層アーキ** | 90 min | L6 | `cmd_intake_hook.sh` + fallback 3 点 |
| 17 | 総合演習 1: 3 階層統合 | 60 min | L6 | `plans/3layer_roadmap.md` + Day1 commit |
| 18 | 総合演習 2: 2 体 + 3 ハーネス | 60 min | L6 | 動く 2 体マルチエージェント |
| A | 附録: 差別化戦略 | 30 min | — | — |
| B | 附録: ビジネス導線 | 30 min | — | 自分のバックエンド設計ワークシート |
| C | 附録: トラブルシュート | 30 min | — | — |

**合計**: 22 レクチャー / 約 18 時間

---

## 差別化ポイント (Marketing Trip メソッドの「既存ベストセラーの隙間」要件への対応)

1. **3 階層統合は市場ゼロ** (cmd_1444 60 件調査で確認): プロンプト単独 / コンテキスト単独 / ハーネス単独の講座はレッドオーシャンだが、3 層を貫通して実装例を提示する講座は 2026-04-24 時点で存在しない。
2. **9 体マルチエージェント並列実運用の実例**: 既存ベストセラーの多くは 1-2 体エージェント。本講座は 9 体 (足軽 7 + 家老 + 軍師) の実運用で蓄積した知見を教材化。
3. **ハーネス 13 項目 (cmd_1442 計画 H1-H13) から採用 12 項目 + 補助 hook 6 本 = 計 18 本の生産実装カタログ**: 既存ベストセラー 2 件 (概論 / 設計ガイド) は概念止まり。本講座は `scripts/*.sh` 18 本の実コード読解を含む。
4. **失敗事例の豊富さ**: 実運用で起きた事故 (context 爆発 / silent fail / dashboard 残骸 / hotfix 未報告 / git add 巻き込み等) を 20 件以上教材化。
5. **flagship case study (第 16 章)**: cmd_1443_p03 で実装した三層アーキを 1 章使って解剖。既存講座では見られない深度。

---

## 未決事項 (v2 で解決すべき項目)

- [ ] 各章の「演習課題」の合格基準 (rubric) を 3 段階で明文化
- [ ] 附録 B (ビジネス導線) を講座内に含めるか別販売するか決定 (殿判断案件)
- [ ] flagship 第 16 章の 90 min 動画分割 (1 本か 3 本か)
- [ ] 無料プレビュー範囲の最終確定 (序章のみか、序章 + 第 1 章か)
- [ ] 講座価格設定 (Marketing Trip は 1,000 円推奨・殿承認済み?)
- [ ] コースタイトル最終版 (現在: 「AI 開発の 3 階層 — プロンプト / コンテキスト / ハーネス エンジニアリング完全実践」を仮題として採用)

---

## 参考資料

- `memory/project_udemy_3engineering.md` (テーマ確定経緯)
- `work/cmd_1444/udemy_engineering.json` (3 エンジニアリング 60 件調査)
- `work/cmd_1444/udemy_strategy_summary.md` (Marketing Trip PDF 要約)
- `work/cmd_1444/marketing_trip_videos_summary.md` (動画 2 本要約)
- `work/cmd_1442/execution_plan_v3.md` (12 ハーネス採用根拠)
- `scripts/cmd_intake_hook.sh` (flagship 実装・本プロジェクト作)
- `scripts/done_gate.sh` / `silent_fail_watcher.sh` / `phase_gate_checker.sh` (L3 教材化対象)
- `CLAUDE.md` / `instructions/*.md` (L2 教材化対象)

---

## 変更履歴

- 2026-04-24 v1: 足軽 7 号 (subtask_cmd_1445) 初版作成
