# cmd_1442 Phase3: harness_proposal.md

軍師策定のハーネス提案 15 件。将軍 H1-H9 + 軍師独自 H10-H15。各ハーネスを 4 軸評価 (防げる失敗 / 実装コスト / 効果 / リスク) し、優先度と実装アプローチを明示。

- **作成**: 2026-04-24 / gunshi (subtask_1442a)
- **先行**: Phase1 failure_clusters.md (5 クラスタ) + Phase2 existing_harness.md (穴 G1-G10)
- **制約**: 新規 .py 禁止 (CLAUDE.md) / shell/hook/既存 skill 拡張を基本
- **除外**: 動画コンテンツ生成 workflow (cmd_1441 方針継続)
- **殿指示原文 (2026-04-24 16:00)**: 『過去失敗から新しいハーネス考えろ・他にもあるかも含めて』
- **番号系統**: 本 md の H1-H15 は **cmd_1442 新規提案ハーネス**。existing_harness.md (Phase2) の既存 H1-H17 とは**別系統**。混同回避のため、以降の本文では必要時に「新 H{N}」「既存 H{N} (Phase2)」と区別する。

---

## 1. 評価軸 (4 軸)

| 軸 | 説明 | 重み |
|----|------|------|
| 防げる失敗 | failure_clusters.md 5 クラスタのどれを何割カバーするか | 最重要 |
| 実装コスト | LOW (<1h) / MED (1-4h) / HIGH (半日+) | 優先順決定材料 |
| 効果 | 失敗抑制 / 運用効率 / 知見蓄積 / 殿負担軽減 | 北極星寄与 |
| リスク | 誤検知疲れ / 偽陰性 / 運用増 / 副作用 | 実装決定の歯止め |

---

## 2. H1〜H15 ハーネス評価マトリクス

| # | ハーネス | 対応クラスタ | 防げる失敗 (事例) | コスト | 効果 | リスク | 優先度 |
|---|---------|-------------|-------------------|--------|------|--------|--------|
| **H1** | 完了後curl/ブラウザ自動 | (a) | cmd_1434 OGP機能 import漏れ / API endpoint変更後NameError / cmd_257 grepのみPASS | MED (2-3h) | **高**(殿激怒即解消) | 誤検知疲れ(静的サイトの curl 200 でも内部壊滅の可能性→検証対象明示要) | **A** |
| **H2** | dashboard残骸 lifecycle hook | (b) | 5件 cmd done化漏れ / 20件 pending 放置 / 🚨残骸1週間滞留 | MED (2-3h) | **高**(運用効率) | 自動削除の取り消し手順必要 | **A** |
| **H3** | cmd起票時 mem-search 自動 | (e) | cmd_834 14本スクリプト乱立 / cmd_1050 ワンライナー再現不能 / 類似cmd発令 | LOW (1h) | **中**(探索促進) | hit時も無視されるリスク→表示義務化要 | **A** |
| **H4** | silent fail log watcher → ntfy | (c) | フォールバック発生見逃し / YouTube VTT fallback / stt_merge混入 / dingtalk「エラーあり」 | MED (2-3h) | **高**(金銭損失リスク対策) | 誤検知疲れ (ログノイズ過多) → level フィルタ要 | **A** |
| **H5** | cmd YAML lint (PreToolUse) | (b)(d) | cmd_1348/1393 重複 status キー / command ヒアドキュメント内 status 混入 | LOW (30min) | **中**(YAML健全性) | 既存 YAML 全件 pass 確認要 (退行防止) | **B** |
| ~~**H6**~~ | ~~LLM選定ガイド (文書化のみ)~~ → **格下げ**: 既存 `memory/feedback_llm_selection_rule.md` + cmd_1441 execution_plan_v2 のモデル指定列 (GLM/Sonnet/Opus[1m]) の2資産で既充足・新規ハーネス化不要 | メタ | (既存活用で対応) | — | — | — | **除外** |
| **H7** | hotfix 3回→skill提案 cron | (d) | pretool_check 4人独立発明 / cmd_1209 8回リトライ | MED (2-3h) | **高**(学習機会化) | 偽陽性 (hotfix_notes 表記揺れ) → 正規化必要 | **A** |
| **H8** | mem-search hit0 警告 | (e) | cmd発令前に類似検索 0 件で新規実装 | LOW (30min・H3 と同時実装可) | **中** | H3 と同源 | **A** (H3 と同バンドル) |
| **H9** | Phase間殿ゲート必須化 | メタ | cmd_1434 Phase3 殿確認スキップ / 3D円グラフ NG 未反映で進行 | LOW (1h) | **高**(殿介在確保) | Phase 間待ち時間増 → バッチ化判断要 | **B** |
| **H10** | advisor 呼出率メトリクス | 全般 | advisor before/after 漏れ / task YAML 要件未履行 | LOW (1h) | **中**(軍師 QC 省力化) | 新規ログ収集のみ・低リスク | **B** |
| **H11** | 殿激怒 → memory 自動追加 slash | 全般 | 殿指摘の精神論が feedback_*.md に反映されない | LOW (1h) | **中** | 自動追加は誤解釈リスク有→下書きレビュー方式推奨 | **B** |
| **H12** | cron インベントリ統合 (gunshi_j テーマ3) | メタ | kill_orphan_chrome 毎分過剰 / 失敗 silent fail | LOW (1h) | **中** | shared_context/cron_inventory.md 文書化 + quarterly レビュー | **C** |
| **H13** | 月次 feedback レビュー cron (gunshi_j テーマ4) | (e) | feedback 死文化 60件の形骸化 | LOW (30min) | **中** | 点検結果を殿確認必要 | **C** |
| **H14** | log warn 自動 ntfy (H4 と合流案) | (c) | H4 と同じ事例 | H4 に統合 | H4 に統合 | H4 に統合 | **H4 に合流・独立不要** |
| **H15** | hotfix_notes 横断集計 cron (H7 と合流案) | (d) | H7 と同じ事例 | H7 に統合 | H7 に統合 | H7 に統合 | **H7 に合流・独立不要** |

**H14/H15 は H4/H7 に合流** → 実質 13 ハーネス (H1-H13)

---

## 3. 実装アプローチ (事例→ハーネス→効果 3点セット)

### H1 完了後 curl/ブラウザ自動
- **事例**: cmd_1434 OGP NameError (3/30)・API endpoint 変更後 (4/23 殿激怒)・cmd_257 grep のみ PASS (3/6)
- **実装**: 既存 skill/shogun-screenshot を **cmd完了 hook** で強制起動。Karo Task Assignment Checklist にある「テスト手順明記」を強制化する PostToolUse hook。task YAML に `verify:` 欄追加、done 宣言前に verify コマンド実行 → log 保存義務。
- **効果**: 殿激怒事象 90% 削減見込 (Phase A の事例頻度 5+ 件/月 → 0.5 件/月)
- **リスク緩和**: verify コマンド失敗時は `done` 宣言を**機械的に阻止** (posttool_cmd_check 拡張)

### H2 dashboard 残骸 lifecycle hook
- **事例**: cmd_1393/1412/1417/1420/1424 5件 done化漏れ・20件以上 pending 放置・🚨 残骸 1週間
- **実装**: dashboard.md 🚨セクションに `cmd_id:` フィールド必須化 + shogun_to_karo.yaml status との nightly 突合 (既存 H16 nightly_audit 拡張) + ntfy 通知 (H4 合流)
- **効果**: 残骸滞留 ≤ 1日に短縮・cmd done化漏れ自動検知

### H3 + H8 cmd 起票時 mem-search 自動 (バンドル)
- **事例**: cmd_834 /manga-short 未使用で 14 本乱立・cmd_1050 ワンライナー再現不能・mem-search hit0 放置
- **実装**: shogun_to_karo.yaml PreToolUse hook で cmd 内容の主要キーワードを抽出 → `cmem_search.sh $keyword` を自動実行 → 結果を cmd 内コメントに挿入 (5 件 hit なら ID 列挙・0 件なら警告)
- **効果**: 類似 cmd 発見率 10% → 70% 想定・重複実装 70% 削減

### H4 silent fail log watcher → ntfy (+ H14 合流)
- **事例**: フォールバック見逃し (3/15)・YouTube VTT fallback・stt_merge 混入・dingtalk 「エラーあり」
- **実装**: `logs/`, `projects/dozle_kirinuki/logs/`, `projects/dozle_kirinuki/analytics/` 3 ディレクトリを `tail -F` する shell daemon (既存 inbox_watcher.sh と同パターン) + grep `WARN|ERROR|fallback|silent` で hit → `ntfy_send.sh "warn:silent_fail:{path}:{line}"` (H4 wrapper 流用)
- **効果**: silent 潜伏時間 数時間→数分に短縮・Gemini 22K円課金タイプの事故 予防
- **リスク緩和**: level=WARN は `logs/warn_digest.log` 集約・level=ERROR のみ即 ntfy (ノイズ抑制)

### H5 cmd YAML lint (PreToolUse)
- **事例**: cmd_1348/1393 重複 status キー・command ヒアドキュメント内 status 混入
- **実装**: H3 posttool_yaml_check.sh 拡張。shogun_to_karo.yaml 編集時に `yq` で `status:` 重複検知 + `grep -E "^  status: "` で heredoc 内混入疑い警告
- **効果**: YAML データ整合性 100%保証・ashigaru2 b カテゴリ発見の再発防止

### H6 LLM選定ガイド → **除外 (重複資産あり)**
- **除外理由**: `memory/feedback_llm_selection_rule.md` + cmd_1441 execution_plan_v2 のモデル指定列 (GLM/Sonnet/Opus[1m]) で既に同等機能を担保。新規ハーネス化は重複。既存資産を参照運用で十分。
- **代替アクション**: execution_plan_v2 のモデル指定パターンを全 cmd task YAML テンプレートへ波及させる運用習慣化 (家老 Task Assignment Checklist に組込提案) のみ

### H7 hotfix 3回→skill提案 cron (+ H15 合流)
- **事例**: pretool_check 4人独立発明・gitignore whitelist 再発・cmd_1209 無駄リトライ
- **実装**: weekly cron で `grep -rA5 "^hotfix_notes:" queue/reports/ | hash-unique` → 同主題 hotfix 3 件以上 hit で dashboard🚨「skill化候補」に自動追加 + ntfy
- **効果**: hotfix 独立発明 ROI 突出の自動検知・skill サージ自動起動

### H9 Phase間殿ゲート必須化
- **事例**: cmd_1434 Phase3 殿確認スキップ (3D円グラフ NG を足軽判断で 2D 化) / cmd_1441 Phase A→B 殿判断ゲート D1-D9
- **実装**: shogun_to_karo.yaml の cmd entry に `lord_preconditions: [...]` 欄必須化 (ngushi_j テーマ6)。Phase N→N+1 時に家老が殿確認を ntfy 強制送信
- **効果**: Phase 境界での殿介在確保・設計逸脱防止

### H10 advisor 呼出率メトリクス
- **事例**: subtask_1441 数十件で advisor 呼出履行率が人力 QC のみ
- **実装**: advisor 呼出ログ `logs/advisor_calls.log` 自動収集 (既存 advisor_proxy 拡張) → 軍師 QC 時に subtask の advisor 呼出回数を機械検証
- **効果**: task YAML 要件遵守率 100% 保証

### H11 殿激怒 → memory 自動追加 slash
- **実装**: `/lord-feedback` slash 新設。殿激怒発言をキャプチャして草案 md を memory/feedback_{slug}.md に書く (将軍がレビュー後 commit)
- **効果**: 殿激怒の教訓化効率 3倍

### H12 cron インベントリ統合
- **事例**: kill_orphan_chrome 毎分過剰 (gunshi_j テーマ3)・cron 失敗の silent fail
- **実装**: `shared_context/cron_inventory.md` 新設 + quarterly レビュー義務化 + `scripts/cron_health_check.sh` 時間 check → ERROR/FAIL 発見で ntfy
- **効果**: cron 失敗 silent fail ゼロ化

### H13 月次 feedback レビュー cron
- **事例**: feedback_*.md 60件 quarterly レビュー未実施・形骸化
- **実装**: 月次 cron で `grep -L '2026-0[M-9]' memory/feedback_*.md` → 3ヶ月参照なし抽出 → dashboard 🚨 に形骸化候補として提示
- **効果**: feedback 健全性維持・使用中 rule と死文化 rule の弁別

---

## 4. 優先度サマリ (A/B/C)

| 優先度 | ハーネス群 | 総コスト | 防止事例種類 |
|--------|-----------|---------|-------------|
| **A (今週着手)** | H1 / H2 / H3+H8バンドル / H4 / H7 | MED*4 + LOW*1 = ~12-15h | 5クラスタ全網羅 |
| **B (2週内)** | H5 / H9 / H10 / H11 | LOW*4 = ~4h | メタ・補完 (H6は除外・既存資産活用に格下げ) |
| **C (来月)** | H12 / H13 | LOW*2 = ~1.5h | 形骸化防止 |

**合計**: 13ハーネス・~18-21h 実装工数・足軽並列可 (1人/1h×3日×3人で完遂)

---

## 5. Wave 配置案 (cmd_1441 Phase C 優先度との整合)

| Wave | ハーネス | cmd_1441 との関係 |
|------|---------|------------------|
| **Wave A (今夜〜今週)** | H1 完了後curl・H3+H8 mem-search 自動・H5 YAML lint | cmd_1441 優先度B の p05-v2 bloom_routing 後に H1/H5 着手可 |
| **Wave B (今週後半)** | H2 dashboard lifecycle・H4 silent fail watcher・H7 hotfix集計 | cmd_1441 優先度C p15-v2 PreCompact 強化 と並行可 |
| **Wave C (来週以降)** | H6/H9/H10/H11/H12/H13 | cmd_1441 完了後 |

---

## 6. 軍師独自追加案 の根拠

将軍 H1-H9 にない観点で拾った 6 件 (H10-H15) のうち 4 件 (H10/H11/H12/H13) を採用:

- **H10 advisor 呼出率メトリクス**: Phase A cmd_1441 で advisor 呼出履行が task YAML 要件なのに人力 QC のみ → 定量化で軍師 QC コスト削減
- **H11 殿激怒→memory 自動**: MEMORY.md の鉄則集が 292 行に肥大・将軍の手動転記に時間かかる → slash command で効率化
- **H12 cron インベントリ**: gunshi_j テーマ3 由来・`kill_orphan_chrome 毎分` 過剰など cron 一元化ゼロ
- **H13 月次 feedback レビュー**: gunshi_j テーマ4 由来・60件形骸化の統制

H14/H15 は H4/H7 に合流 (機能重複回避)。

---

## 7. 期待効果 (数値見込み)

| 指標 | 現状 | ハーネス導入後見込 |
|------|------|------------------|
| 殿激怒事象 (cmd 完了後発覚) | 5+ 件/月 | ≤ 1 件/月 |
| hotfix 独立発明 | 月 3-5 件 | skill化誘導で ≤ 1 件/月 |
| mem-search 活用率 | 週 0-3 回 | cmd 起票毎 (週 10-20 回) |
| dashboard 🚨 残骸滞留時間 | 1-7 日 | ≤ 24h |
| silent fail 発覚遅延 | 数時間〜数日 | ≤ 30分 |
| advisor 呼出履行率 | 目視推定 80% | 計測上 ≥ 98% |

---

## 8. 実装時のリスク管理

- **誤検知疲れ (H1/H4)**: level 分けで MUST/SHOULD を切り分け・INFO は ntfy せず log 集約のみ
- **運用増 (H2/H7/H12/H13)**: cron 起動失敗時の silent fail を H12 自身でカバーする循環参照 → 手動月次確認を最終バックストップに
- **偽陽性 skill化 (H7)**: hotfix_notes 表記揺れ → 正規化 (lowercase + stopword 除去) 前処理必須
- **家老権限侵犯 (H2)**: 🚨自動削除は家老権限・軍師はメタメトリクス提供のみ (F006 遵守)

---

## 9. 北極星アラインメント

- **短期寄与**: 殿激怒減少 (H1) + 既存資産活用 (H3+H8) → 開発速度向上
- **中長期寄与**: hotfix 横断集計 (H7) + feedback 健全性 (H13) → 学習機会の体系化 → Day6 MIX 再開時の迅速性向上 (cmd_1441 方針と整合)
- **リスクへの備え**: silent fail 検知 (H4) で Gemini 22K円課金タイプの金銭損失予防

---

## 10. Phase C 発令形式 (家老向け依頼文)

本提案の受諾後、家老に以下依頼する (軍師は subtask 直接発令禁止・F003):

```yaml
# 家老が起票する subtask 案 (cmd_1442_p01 〜 p13)
cmd_1442_p01:
  seed: H1 完了後curl自動
  priority: A
  model: Sonnet
  assignee_candidate: 足軽3号
  estimated_time: 2-3h
  advisor_required: true
  git_push_owner: 家老
  ...
(以下 H2-H13 同形式・Wave A→B→C 順)
```

具体的な subtask 分解は家老の権限・軍師は提案まで。

---

以上、cmd_1442 ハーネス提案 13 件 (H1-H13・H14/H15 合流) を 4軸評価・優先度付け完了。殿・家老へ提示し Phase C 発令に繋げる。
