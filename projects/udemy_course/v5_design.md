# Udemy 中級編 v5 設計書

**確定日**: 2026-05-05 (殿+将軍ブレストにて確定)
**ステータス**: 設計フェーズ完了・執筆フェーズ未着手
**v4 との関係**: v5 は **ゼロベース執筆** (v4 は参考資料・例示やコード片のみ流用可)

---

## 1. ビジョン

> **「AI を単発の質問相手ではなく、自分専用の常駐ツールとして仕組み化する技術」**

ChatGPT 講座 (プロンプトの書き方) との決定的差別化:
**「Claude を選ぶ理由 = 仕組み化」**

## 2. 受講者ペルソナ + 到達目標

### ペルソナ
- 社会人 2-3 年目 (25-26 歳)
- 文系 or 非情報系学部卒
- 本業は IT/Web 業界 (営業・マーケ・企画・PM サポート等)
- ChatGPT は使ったことあるが「プロンプトエンジニアリング」「LLM」「コンテキスト」等の用語は説明できない
- 初級編完了済 (= 単発プロンプトは書ける)

### 動機
- 副業・転職で AI 活用スキルを身につけたい
- 自分の現場 (営業/マーケ/PM サポート等) の業務を効率化したい
- 「教材で学んだことを、自分のプロジェクトに即適用」したい

### 到達目標
**「自分の業務を Claude で半自動化できる」**

## 3. 困りごとリスト (殿実体験ベース・11 項目)

ch00 のフックとして提示し、ch10 で逆引き辞典として再構成する物語の縦軸:

| # | 困りごと | 解決章 |
|---|---------|--------|
| ① | AI が**推測 (esper) で動く・確認せず突進** | ch02 + ch06 |
| ② | **AI 出力を盲信して失敗** | ch06 (/advisor) |
| ③ | **既存資産を確認せず新規作成する** | ch01 (/command) |
| ④ | **失敗を fallback で隠す** (silent fail) | ch08 |
| ⑤ | **「止めろ」が伝わらない** | ch08 (phase gate) |
| ⑥ | **「言ったのにやってくれない」** | ch05 (3 層) |
| ⑦ | **完了 (done) 伝達が抜ける** | ch04 (memory) |
| ⑧ | **API 変更後にテストせず壊れる** | ch07 (PostToolUse hook) |
| ⑨ | **大事な context を確認しない** | ch07 (PreToolUse hook) |
| ⑩ | **同じ作業を繰り返している** | ch01 (/command) |
| ⑪ | **長文 context の中間情報が読み飛ばされる** (Lost in the Middle) | ch03 + ch04 |

memory 出典: `feedback_no_esper`, `feedback_dont_trust_gunshi_blindly`, `feedback_use_existing_scripts_shogun`, `feedback_fallback_is_abnormal`, `feedback_phase_gate_check`, `feedback_listen_to_lord_first`, `feedback_shogun_done_propagation`, `feedback_test_after_api_change`, `feedback_check_procedures_dir` 他

## 4. 章構成 — 12 章 (約 6 時間)

| # | 章タイトル | 層 | 持ち帰り |
|---|----------|----|---------|
| ch00 | **講座のゴール — 「困りごと」をこう解決します** | 導入 | 自分の困りごとが講座で解決されると確信できる |
| ch01 | **プロンプトを資産にする — /command 化** | L1 | 1 つの /command を作って動かせる |
| ch02 | **よくある失敗 3 パターンの診断** | L1 | 自分のプロンプトを 10 項目で診断できる |
| ch03 | **長い context は読まれない** | L2 | Lost in the Middle を理解し、配置技術を使える |
| ch04 | **必要なときに必要なものを思い出させる** | L2 | claude-mem や handoff で過去を引き出せる |
| ch05 | **役割別ファイルで AI を分業させる** | L3 | CLAUDE.md / instructions / task の 3 層を理解 |
| ch06 | **第三者 AI に見直してもらう (/advisor)** | L3 | /advisor を 1 回呼べる |
| ch07 | **自動で動かす — 4 つのフック** | L3 | hook を 1 つ作って動かせる |
| ch08 | **失敗を見逃さない仕組み** | L3 | silent fail と phase gate を実装できる |
| ch09 | **自分の業務に組み込む — 営業/PM/データ分析** | 応用 | 自分の業務に当てはめた構想ができる |
| ch10 | **困った時の逆引き辞典** | 逆引き | 詰まったときに何を見るか即判断できる |
| ch11 | **全部使ってミニ自動化を作る** | 演習 | 1 つの仕事を完遂できる |

## 5. L1/L2/L3 階層マッピング

```
ch00 [導入] 困りごとフック + 全体地図

ch01 [L1] プロンプトを資産にする — /command
ch02 [L1] よくある失敗 3 パターンの診断

ch03 [L2] 長い context は読まれない (Lost in the Middle 問題提起)
ch04 [L2] 必要なときに必要なものを思い出させる (JIT・semantic search 手動)

ch05 [L3] 役割別ファイルで AI を分業させる
ch06 [L3] 第三者 AI に見直してもらう (/advisor)
ch07 [L3] 自動で動かす — 4 つのフック (semantic search 自動化 = JIT 完成)
ch08 [L3] 失敗を見逃さない仕組み

ch09 [応用] 自分の業務に組み込む
ch10 [逆引き] 困った時の逆引き辞典
ch11 [演習] 全部使ってミニ自動化
```

## 6. 各章で紹介する仕組み (実機検証済のみ)

### ch00 — 講座のゴール
- (仕組みなし・地図のみ)

### ch01 — プロンプトを資産にする
- ① `/command` (`.claude/commands/{name}.md`)
- ② 引数付き呼出 (`/summarize-meeting @file.md`)
- ③ 既存の `/handoff` `/rehydrate` 紹介

### ch02 — よくある失敗 3 パターンの診断
- ④ プロンプト診断チェックリスト 10 項目

### ch03 — 長い context は読まれない
- ⑤ Lost in the Middle 現象解説 (Liu et al. 2023)
- ⑥ TL;DR 配置・重要情報を冒頭/末尾
- ⑦ Prompt Caching (コスト削減・概念のみ)

### ch04 — 必要なときに思い出させる (★ semantic search 初登場)
- ⑧ Claude Code memory file (永続記憶)
- ⑨ `/handoff` `/rehydrate` (セッション切替)
- ⑩ `claude-mem mem-search` / `smart_search`
- ⑪ `claude-mem timeline` (時系列振り返り)
- ⑫ 自前ドメイン semantic 検索の実例 (`scene_search_v2.py`)

### ch05 — 役割別ファイルで AI を分業させる
- ⑬ `CLAUDE.md` (常駐ルール)
- ⑭ `instructions/*.md` (役割別)
- ⑮ task YAML (個別指示)
- ⑯ `subagent` / `Task tool` (専門エージェント呼出)

### ch06 — 第三者 AI に見直してもらう
- ⑰ `/advisor` (Claude 内蔵レビュー)
- ⑱ `acceptance_criteria` (完了条件の構造化)

### ch07 — 自動で動かす — 4 つのフック (★ semantic search 自動化)
- ⑲ `SessionStart` hook
- ⑳ `PreToolUse` hook (+ 関連 doc 自動 grep = ch04 の検索を自動発動)
- ㉑ `PostToolUse` hook
- ㉒ `PreCompact` hook
- ㉓ `UserPromptSubmit` hook (本講座でも稼働中)

### ch08 — 失敗を見逃さない仕組み
- ㉔ `silent_fail watcher` (cron で異常検知)
- ㉕ phase gate (段階確認)
- ㉖ `--dry-run` / `--no-confirm` flag 運用
- ㉗ 禁止操作リスト (D001-D008 等)

### ch09 — 自分の業務に組み込む
- (既出技術の組合せ・営業/PM/データ分析の応用例)

### ch10 — 困った時の逆引き辞典
- (症状 → 該当章の照会表 + 復習)

### ch11 — 全部使ってミニ自動化
- (全 27 仕組みのうち 5-7 個を組み合わせる演習)

## 7. セマンティック検索の二重登場 (中級編の哲学的核心)

> **「同じ技術を、人間が呼ぶか機械が呼ぶかで、生産性が桁違いに変わる」**

| 層 | 章 | 形 | 機能例 |
|----|----|---|------|
| **L2** | ch04 | **手動 trigger** | mem-search / timeline / 自前 semantic 検索 |
| **L3** | ch07 | **hook 自動 trigger** | UserPromptSubmit hook + 関連 doc 自動 grep |

**ch04 章末の橋渡し**:
> 「これ、毎回手動で叩くのは現実的じゃない。次の章で『hook で自動発動』を学びます」

**ch07 章冒頭の前章回収**:
> 「ch04 で学んだ検索を、人間が叩かなくても勝手に動く仕組み — それが hook」

→ **ch04 → ch07 で同じ技術が手動から自動へ昇華する物語**を作る。

## 8. NG ワードリスト (執筆ルール)

専門用語・固有記法は禁止。受講者ペルソナ (社会人 2-3 年目) に届かない:

| NG | 言い換え |
|----|---------|
| 経済 / economics | 容量・予算・読まれる量 |
| 階層 / hierarchical | 役割別 / 3 段重ね |
| 工程検問 / phase gate | チェックポイント / 段階確認 |
| サイレントフェイル | 見逃される失敗 / 黙って失敗 |
| ハーネスエンジニアリング | 自動化の仕組み |
| compaction / persistent | 圧縮・保存 |
| L1 / L2 / L3 | 武器①②③ (本文では使う・章名には出さない) |
| queue/tasks/ / shogun / karo / ashigaru / gunshi / multi-agent-shogun | 完全削除 (cmd_1634 で撲滅済) |
| **JIT / Just-In-Time** (製造業/コンパイラ流用・LLM 未確立) | **必要時取得 (Selective Retrieval)**・関連: RAG |
| **Lazy Load** (Web/JS 流用・LLM 文脈で曖昧) | **必要時読込 (On-Demand Loading)** |

## 9. 章タイトル原則

- 専門用語不使用・受講者の困りごと直結
- 「**章タイトルだけ読んで講座の物語が成立する**」が基準
- 殿が「経済」「移動」と疑問を呈した教訓を反映

## 10. 各章の事前 4 項目 (執筆前必須)

各章で執筆者 (足軽) が**最初に固める 4 項目**を殿確認 → OK 後に本文執筆 (= 二段階執筆):

1. **対象問題** — この章で解決する困りごとは何か (ch00 フックリストと紐付け)
2. **持ち帰り** — 受講者が章末で言える 1 文 / できる 1 動作
3. **ストーリー** — 困った状態 → 学習 → 解決 の物語線
4. **実例** — 受講者の現場 (営業/PM/データ分析) に置換可能な具体例

## 11. v4 流用方針 — 完全ゼロベース

**v5 = ゼロベース執筆** が前提。v4 は参考資料・例示やコード片のみ流用可。文章のコピペは禁止。

| v5 章 | v4 参考元 | 流用度 |
|-------|----------|------|
| ch00 | v4 ch00 | 概念のみ・全面書き直し |
| ch01 | v4 ch01 (関数概念) | 概念のみ・/command 化を核心に |
| ch02 | v4 ch02 (10 項目) | 例示参考・全面書き直し |
| ch03 | v4 ch05/08 | 概念のみ |
| ch04 | v4 ch06/07/09 + 新規 | claude-mem 主役で新規執筆 |
| ch05 | v4 ch03 | L3 文脈で**全面再構成** (殿指摘「移動レベルじゃない」) |
| ch06 | v4 ch04 | L3 文脈で**全面再構成** |
| ch07 | v4 ch10/15 + 新規 | hook + semantic search 自動化で**新規執筆** |
| ch08 | v4 ch11/12/13 | 統合書き直し |
| ch09 | (v4 にない) | **完全新規** |
| ch10 | v4 appendix_c | 構造のみ参考・**完全新規** |
| ch11 | v4 ch17/18 | 演習設計のみ参考・**新規執筆** |

## 12. 物理分離

v5 執筆中は v4 ファイルに触らない・並行存在:

```
projects/udemy_course/drafts/lectures/intermediate_v4_ch00_intro.md  ← v4 (アーカイブ予定)
projects/udemy_course/drafts/lectures/intermediate_v5_ch00_intro.md  ← v5 (新規執筆)
```

v5 完成後に v4 を `archive/v4_20260505/` へ退避。

## 13. 品質保証

### udemy-checker (v2・cmd_1635 で観点 E 追加済)
- A. わからない箇所
- B. 論理破綻・飛躍
- C. ペルソナとして詰まる箇所
- D. 良かった箇所
- **E. 商品汎用性チェック** (固有記法・暗黙前提・読み替え不能箇所を検出)

### gunshi QC
各章執筆完了後、軍師が以下を確認:
- 事前 4 項目との整合性
- セマンティック検索の二重登場が ch04 ↔ ch07 で繋がっているか
- 全 11 困りごとが解決章にマッピングされているか
- NG ワードリスト全件 grep で 0 件
- 持ち帰りが各章で明確か

## 14. 動作実演方針

紹介する全 27 仕組みは**実機で動かして見せる**。動かない機能は載せない:

- claude-mem は systemd PATH 修正 (本日 cmd 内で実施) で動作可能化済
- /advisor は cmd_1635 で実演済
- hooks は本講座の制作環境で常時稼働中 (受講者にも見せられる)
- /command は本プロジェクトの 20+ コマンドが実例

## 15. 実行計画

### Phase 0: 設計確定 (本書)
✅ 完了 (2026-05-05)

### Phase 1: 章別事前 4 項目作成
- 11 章 × 4 項目 = 44 項目を ash 4 名並列で起こす
- 殿レビュー → 修正 → OK でフェーズ完了
- 推定: 1-2 日

### Phase 2: 章別本文執筆
- 11 章 × .md + .html を ash 並列で執筆
- udemy-checker (v2) で各章 🟢 まで反復
- gunshi QC で全体整合性確認
- 推定: 3-5 日

### Phase 3: 完成・公開
- HTML 統合・スタイル統一
- 殿最終レビュー
- Udemy 出品準備

cmd_1637 (Phase 1 起票) は本設計書承認後・cmd_1636 (動画 STT) と並走で発令予定。
