# cmd_1442 Phase1: failure_clusters.md

軍師策定の失敗パターン 5 クラスタ化。cmd_1442 ハーネス設計の Phase1 成果物。

- **作成**: 2026-04-24 / gunshi (subtask_1442a)
- **情報源**: (A) claude-mem mem-search (12K obs 走査・cmem_search.sh 7キーワード) / (B) memory/feedback_*.md 60件走査・8件直読 / (C) memory/MEMORY.md Shogun Core Rules 鉄則集 / (D) queue/handoff/ 301件のうち代表事例 (E) cmd_1441 Phase A 成果物 (ashigaru1-7 + gunshi_j) の hotfix/lessons learned

### mem-search 走査結果 (cmem_search.sh 実行ログ)

| キーワード | hit数 | 内訳 (obs/sessions/prompts) | 代表 hit ID (抜粋) |
|----------|------|----------------------------|------------------|
| `完了後` | 11 | 5/1/5 | #9797 (Apr 19) 実行権限・#P系 Apr 22 yaml |
| `殿激怒` | 10 | 5/0/5 | #7211 (Apr 12) マルチエージェント漫画パネル・crowdworks納品 |
| `silent fail` | 10 | 5/5/0 | #5600 (Apr 9) speechbrain Model Fetch Exception Conversion Workaround |
| `hotfix` | 5 | 0/0/5 | #P5703 (Apr 12) inbox2・#P5644 omatase v5 |
| `mem-search` | 14 | 5/5/4 | #12351 (Apr 24) cmd_1442正式発令・キューイング・通知フロー完了 |
| `dashboard残骸` | 5 | 0/0/5 | #P8892/P8885/P8884/P8880 (Apr 23) 夜のgacha修正系 |
| `curl確認` | 8 | 3/0/5 | #7211 マルチエージェント漫画・Apr 22 yaml |
| **合計** | **63** | — | (cmem=12,154 obs / 487K tokens 蓄積中の上位ヒット) |

※ dateRange filter bug (claude-mem v10.6.3) のため dateStart/End 指定せず・keyword 単独で取得。検索母集団は **claude-mem 12,154 obs / 1,757 sessions / 8,038 summaries**。
- **除外対象**: 動画コンテンツ生成 workflow の出来栄え問題 (cmd_1441 方針継続)・動画制作系の hotfix は **仕組み改善視点で含める**

---

## クラスタ (a) 完了後未確認・即ユーザー発覚

**症状**: cmd 完了判定が機械的チェック (grep/count/exit code) のみに依存し、**実ファイル目視・curl動作確認・ブラウザ確認**を省略。殿が手動確認して初めて障害発覚。cmd_XXX 完了報告後、数分〜数時間で殿激怒する構造。

### 代表事例

1. **cmd_1434 OGP機能 import漏れ + サーバーブロック** (2026-03-30, MEMORY.md Karo Task Assignment Checklist)
   - 症状: 実装直後の curl/ブラウザ確認なしで本番投入→ NameError で機能全停
   - 影響: 本番障害、殿が発見するまで修復遅延
2. **cmd_257 grep結果だけ PASS 報告** (2026-03-06, feedback MEMORY.md)
   - 症状: 将軍が grep カウント結果だけ見て「PASS」と報告、実ファイルを読まず殿指摘まで放置
3. **API endpoint 変更後 curl 未実施** (2026-04-23 殿激怒, MEMORY.md)
   - 症状: py_compile 通過だけで done 判定・実エンドポイント叩くまで NameError 等判明せず
4. **pane 確認 tail -3 誤報告** (2026-03-30, feedback_pane_check_100lines_enforced)
   - 症状: 足軽1号が DL 実行中なのに「全員アイドル」と誤報告・数十回指摘されて依然再発

### 根本原因
- 完了判定に「curl/ブラウザ/実ファイル目視」が **必須手順として強制されていない**
- 機械チェック通過 = done と短絡・殿の手動確認が最後のゲートになる

---

## クラスタ (b) dashboard 残骸滞留・ライフサイクル断裂

**症状**: 殿の判断 (済み/いらん/見た/修正cmd発令) 後に dashboard 🚨要対応 または shogun_to_karo.yaml status が自動同期されず、**残骸が 1日〜数週間滞留**。次 cmd 発令時に dashboard がノイズで判断材料として機能しない。

### 代表事例

1. **cmd_1393/1412/1417/1420/1424 5件 status done化漏れ** (2026-04-24, cmd_1441 Phase A ashigaru2_b.md 発見)
   - 症状: dashboard archive で ✅完了と書きつつ shogun_to_karo.yaml status=in_progress/pending/on_hold のまま。6 cmd 中 5 件乖離
2. **20件以上 pending 放置** (2026-04-09, feedback_shogun_to_karo_status_update)
   - 症状: MCP ダッシュボードに進行中 cmd 20件以上溜まる・dashboard 更新と yaml status 更新が別手順
3. **殿の「済み」発言が残骸化** (cmd_1441 Phase A 内で 1 件違反, feedback_dashboard_immediate_cleanup)
   - 症状: 殿レビュー待ち項目に修正 cmd 発令 = レビュー済みなのに🚨残存

### 根本原因
- 完了イベントの単一真正源 (source of truth) がない: dashboard / yaml / ntfy / handoff がバラバラ
- 人力の「後でまとめて掃除」が破綻

---

## クラスタ (c) silent fail / fallback 検知不能

**症状**: エラー・障害・fallback が発生しても **警告レベルで標準出力に流すのみ**・ログ監視不在で気付かれず、後続工程に誤ったデータが流れる。

### 代表事例

1. **フォールバック発生見逃し** (2026-03-15, MEMORY.md 鉄則 feedback_fallback_is_abnormal)
   - 症状: ログに warn/fallback が 1件でも出ているのに PASS 判定・fallback = 異常のルールが形骸化
2. **YouTube VTT fallback** (feedback_youtube_vtt_fallback)
   - 症状: 自動 VTT fallback で wrong transcription source が混入・silent
3. **stt_merge に誤って YouTube 字幕混入** (feedback_stt_merge_includes_youtube)
   - 症状: AssemblyAI STT と YouTube auto-caption が混ざり納品 → silent fail
4. **cmd_1348 dingtalk_qc_loop「エラーあり」承認フロー** (2026-04-24, cmd_1441 Phase A)
   - 症状: .gitignore で scripts/dingtalk_qc_loop.py が untracked → commit されず cmd 完了判定不能・silent

### 根本原因
- warn 系ログの**自動検知→通知**機構が未実装
- ログ出力先が散在 (logs/ / projects/dozle_kirinuki/logs/ / analytics/) ・監視対象を一覧していない

---

## クラスタ (d) hotfix 独立発明・知見共有欠落

**症状**: 同一問題で複数足軽が**独立に同じ回避策を発明**し、実装の重複と学習機会喪失が発生。恒久修正化されず再発ループ。

### 代表事例

1. **pretool_check target_path 欠落 Phase A 4人独立発明** (2026-04-24, cmd_1441 Phase A)
   - 症状: 足軽 2/3/4/5 号が subtask_1441 で独立に target_path を付与する workaround を発見・hotfix_notes に記録するが全員別々に書いた
2. **cmd_1209 note記事投入崩壊 8回リトライ無駄** (2026-03-XX, feedback_ashigaru_retry_useless)
   - 症状: subtask_1209b〜1209h まで 8回足軽に再振り・根本原因 (Ctrl+K カーソル位置バグ) は将軍が30分で特定
3. **gitignore whitelist 新規 skill 作成毎手動追加** (2026-04-24 cmd_1439 hotfix)
   - 症状: yt-dlp-js-runtimes-fix skill 化時に whitelist 欠落で SKILL.md 非追跡・同じパターンが再発確実

### 根本原因
- hotfix_notes は報告YAMLに記載されるが**横断集計・通知機構なし**
- 「2回以上同じ hotfix」検知が人力 (軍師が気付くまで)・自動化未

---

## クラスタ (e) 既存資産活用漏れ (車輪の再発明)

**症状**: 既存の skill / script / feedback_*.md / MCP entity / claude-mem 観察に**答えが既にあるのに探さず**、新規実装または同じ設計議論を繰り返す。

### 代表事例

1. **cmd_834 /manga-short スキル不使用 14 本乱立** (2026-03-XX, feedback_use_existing_skills)
   - 症状: 将軍がスキル存在を忘れ、足軽に make_834a-n 14 本スクリプト作成を振った
2. **cmd_1050 python3 -c ワンライナー 再現不能** (2026-04-XX, feedback_no_new_scripts)
   - 症状: 使い捨てワンライナーで再実行不能・殿「同じことができない」と指摘
3. **mem-search hit0 無しで新規実装** (cmd_1441 integrity_audit)
   - 症状: 類似 cmd を過去発令したか未確認で cmd 起票・発令後に過去類似が発覚するパターン (将軍 H8 起点)
4. **feedback_*.md 60 件の quarterly レビュー未実施** (gunshi_j テーマ4)
   - 症状: 陳腐化した rule と現役 rule が混在・どれが生きているか不明

### 根本原因
- cmd 発令前の「類似探索」が**任意 (nice-to-have)** に留まる
- MCP 3D entity 化石化 (cmd_1441 D7 訂正A で解消) と同根・蓄積が能動活用に繋がらない

---

## クラスタ横断の観察

- **最頻度 = (a) + (b)** → これらはシステム内で日次発生・優先度 A のハーネス対象
- **最深刻 = (c)** → 障害潜伏が長く金銭的損失リスク大 (e.g. Gemini 22,000円課金・feedback_gemini_cost_control はまさにこの系統)
- **最学習機会 = (d)** → 4 人同じ hotfix 発見は**無駄だが知見の濃度は高い**・skill 化ファクトリの好機
- **最 ROI = (e)** → mem-search 1 回で救える工数が膨大・ほぼゼロコストで実装可能

---

## 対応 ハーネス マッピング (Phase3 へ)

| クラスタ | 将軍 H1-H9 対応 | 軍師独自追加案候補 |
|---------|----------------|------------------|
| (a) 完了後未確認 | **H1** 完了後curl自動 + **H4** silent fail検知 | H10 advisor呼出率メトリクス |
| (b) dashboard残骸 | **H2** dashboard残骸clean + **H5** cmd YAML lint (重複status検知) | H11 殿激怒→memory自動追加 |
| (c) silent fail | **H4** silent fail検知 | H14 log warn 自動 ntfy (新規) |
| (d) hotfix 独立発明 | **H7** hotfix 3回→skill提案 + **H5** YAML lint | H15 hotfix_notes 横断集計 cron (新規) |
| (e) 既存資産活用漏れ | **H3** mem-search 自動 + **H8** mem-search hit0 警告 | H13 月次 feedback レビュー cron |
| 全般メタ | **H6** LLM選定 + **H9** Phase間殿ゲート | H12 cron インベントリ統合 (gunshi_j 由来) |

---

以上、5 クラスタ × 代表事例 3-4 件 × 根本原因の整理を完了。Phase2 (existing_harness.md) で既存ハーネスのカバー範囲を棚卸しし、Phase3 (harness_proposal.md) で評価・新提案する。
