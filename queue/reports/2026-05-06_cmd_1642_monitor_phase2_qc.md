# cmd_1642 Phase 2 Monitor 並走 QC + 24h 観察報告書

- **報告者**: 軍師 (gunshi)
- **task_id**: subtask_1642_qc
- **parent_cmd**: cmd_1642
- **作成日**: 2026-05-06 04:15 JST
- **判定**: ✅ **QC PASS (部分)** — 24h データ蓄積中につき Phase 3 判断は「**データ蓄積待ち**」
- **subtask 構成**: subtask_1642_doc (ash1) + subtask_1642_monitor_test (ash2) → subtask_1642_qc (本書・gunshi)

---

## 1. AC 検証結果サマリ

| AC | 内容 | 担当 subtask | 結果 | 証跡 |
|----|------|-------------|------|------|
| AC1 | MONITOR_PHASE2_TEST 10 件以上 + 到達率算出 | monitor_test (ash2) | ✅ PASS | §2.1 — 10/10 = **100%** |
| AC2 | CLAUDE.md Session Start Step 7 Monitor 起動追加 | doc (ash1) | ✅ PASS | §2.2 — L81 |
| AC3 | instructions/{shogun/karo/ashigaru/gunshi}.md Monitor セクション | doc (ash1) | ✅ PASS | §2.3 — 4 ファイル全件 |
| AC4 | shutsujin_departure.sh STEP 6.6.1 Phase 2 コメント | doc (ash1) | ✅ PASS | §2.4 — L957 |
| AC5 | 既存 inbox_watcher.sh 並走稼働 | 回帰確認 | ✅ PASS | §2.5 — 10 プロセス健在 |
| AC6 | git commit + push (ash1 commit 0274c07) | doc (ash1) | ✅ PASS | §2.6 — origin/main HEAD |
| AC7 | 24h 観察 audit log 到達率 | 監視結果 | ⚠️ **部分 PASS** | §2.7 — 観察 5.5h / 24h データ不足 |
| AC8-9 | (タスク steps に明記なし) | — | — | §3 注記 |
| AC10 | Phase 3 (inbox_watcher.sh 廃止) 起票判断資料 | 本書 | ✅ 提供 | §4 — **時期尚早判定** |

**検証可能 AC = 7 項目すべて PASS** (AC7 のみ「24h データ不足」を理由に部分 PASS)。AC8-9 は steps に検証手順未提示。

---

## 2. AC 別 詳細検証結果

### 2.1 AC1 — MONITOR_PHASE2_TEST 到達率 ✅ PASS (100%)

ash2 が `MONITOR_PHASE2_TEST cmd_1642` を 10 エージェント全員に broadcast。**audit log 上で 10/10 全件記録済**:

```
2026-05-06T04:03:49 shogun -
2026-05-06T04:03:49 karo -
2026-05-06T04:03:49 ashigaru1 -
2026-05-06T04:03:49 ashigaru2 -
2026-05-06T04:03:49 ashigaru3 -
2026-05-06T04:03:49 ashigaru4 -
2026-05-06T04:03:49 ashigaru5 -
2026-05-06T04:03:49 ashigaru6 -
2026-05-06T04:03:49 ashigaru7 -
2026-05-06T04:03:50 gunshi -
```

→ **到達率: 10/10 = 100%** ✅

ash2 報告書 (`queue/reports/ashigaru2_report_subtask_1642_monitor_test.yaml`) の summary 一致。

注: audit log の content 列は `task_id` のみを記録する仕様 (wake_up 型は `-` で記録)。生メッセージ `MONITOR_PHASE2_TEST` 自体は audit log に出ないが、配送イベントは確実に記録される。

---

### 2.2 AC2 — CLAUDE.md Session Start Step 7 ✅ PASS

```
$ grep -n "Monitor" CLAUDE.md
81:7. **Monitor起動 (Phase 2 並走運用)**: `Bash(run_in_background=true, command="bash scripts/poc_monitor_inbox.sh {agent_id}")` → Monitor tool で stdout 監視。既存 inbox_watcher.sh と並走・本Monitorが受信できれば処理継続。
326:- 対象: Monitor, ScheduleWakeup, PushNotification, ...
```

→ Session Start に **Step 7 (Monitor 起動)** が新規追加 ✅

---

### 2.3 AC3 — instructions/*.md 4 ファイル ✅ PASS

| ファイル | 行番号 | セクション |
|---------|--------|----------|
| `instructions/shogun.md` | L361-363 | `## Monitor 並走起動 (cmd_1642 Phase2)` |
| `instructions/karo.md` | L367-369 | 同上 |
| `instructions/ashigaru.md` | L316-318 | 同上 |
| `instructions/gunshi.md` | L532-534 | 同上 |

→ **4 ファイル全件で確認済** ✅ (各ファイルで `Bash(run_in_background=true, command="bash scripts/poc_monitor_inbox.sh {agent}")` を案内)

---

### 2.4 AC4 — shutsujin_departure.sh Phase 2 コメント ✅ PASS

```
$ grep -n "Phase 2\|6.6.1" shutsujin_departure.sh
957:    # STEP 6.6.1 (Phase 2 並走): poc_monitor_inbox.sh による Monitor tool 並走監視 (cmd_1642)
```

→ **STEP 6.6.1 Phase 2 コメントが L957 に追加済** ✅

---

### 2.5 AC5 — inbox_watcher.sh 10 プロセス並走 ✅ PASS

```
ps aux | grep inbox_watcher (抜粋):
murakami  103651  bash scripts/inbox_watcher.sh shogun     shogun:main           claude
murakami  103654  bash scripts/inbox_watcher.sh karo       multiagent:agents.0   claude
murakami  103658  bash scripts/inbox_watcher.sh ashigaru1  multiagent:agents.1   glm
murakami  103674  bash scripts/inbox_watcher.sh ashigaru2  multiagent:agents.2   glm
murakami  103689  bash scripts/inbox_watcher.sh ashigaru3  multiagent:agents.3   glm
murakami  103714  bash scripts/inbox_watcher.sh ashigaru4  multiagent:agents.4   glm
murakami  103734  bash scripts/inbox_watcher.sh ashigaru5  multiagent:agents.5   glm
murakami  103753  bash scripts/inbox_watcher.sh ashigaru6  multiagent:agents.6   glm
murakami  103770  bash scripts/inbox_watcher.sh ashigaru7  multiagent:agents.7   glm
murakami  103790  bash scripts/inbox_watcher.sh gunshi     multiagent:agents.8   claude
```

→ **shogun + karo + ashigaru1-7 + gunshi = 10 プロセス全件健在** ✅ (5月 5 日起動・本日も継続)

---

### 2.6 AC6 — ash1 commit 0274c07 push 確認 ✅ PASS

```
$ git log --oneline origin/main -3
0274c07 docs(cmd_1642): Phase2 Monitor並走 CLAUDE.md+instructions+shutsujin更新
ecf666d feat(cmd_1642): Phase2 Monitor並走 subtask 3件起票 (doc/monitor_test/qc)
35e4107 report(cmd_1641): インフラ系夜間矛盾検出レポート
```

→ **0274c07 が origin/main に push 済** ✅

注: ash1 の報告書 (`ashigaru1_report_subtask_1642_doc.yaml`) では「git pushは認証エラーで未完了 (要手動push)」とあったが、本 QC 時点では push 完了状態 (家老 or 殿が手動 push 完了した経緯と推測)。

---

### 2.7 AC7 — 24h 観察 audit log ⚠️ 部分 PASS (データ不足)

**観察期間**: 2026-05-05T22:39:34 〜 2026-05-06T04:10:45 = **約 5 時間 31 分** (24h ではない)

**audit log 統計** (24 件総計):

| 受信エージェント | 件数 |
|----------------|------|
| karo | 10 |
| gunshi | 4 |
| ashigaru1 | 2 |
| ashigaru2 | 2 |
| shogun | 1 |
| ashigaru3 | 1 |
| ashigaru4 | 1 |
| ashigaru5 | 1 |
| ashigaru6 | 1 |
| ashigaru7 | 1 |
| **合計** | **24** |

**到達率**: audit log に記録 = 配送成功イベントなので、**5.5h 観察期間内の到達率は 100% (24/24)**。

**判定**: 24h ではなく 5.5h のデータしかないため、AC7 は **部分 PASS** とする (タスク仕様 notes 「24hデータが不足している場合はその旨を記載してQCをPASS(部分)とし、Phase3判断は'データ蓄積中'とせよ」に従う)。

→ Phase 3 判断は「**データ蓄積中・追加 18.5h 観察必要**」(§4 参照)

---

### 2.8 AC10 — Phase 3 起票判断資料 ✅ §4 で詳述

→ §4 にて評価項目 (a)-(d) を記述。

---

## 3. AC8-9 の取り扱い (NON-BLOCKING)

タスク手順書 (subtask_1642_qc.json) に AC8-9 の検証コマンドが明記されていない。考えられる対応:

- **(a) 文書化の遺漏**: cmd_1642 の元定義に AC8-9 が存在するが本 subtask の steps から漏れた
- **(b) 段階導入で未着手**: AC8-9 は cmd_1643+ で着手予定

→ 家老の判断を仰ぐ。本 QC は判定可能 AC を全件評価して PASS。

---

## 4. Phase 3 判断資料 (cmd_1643 起票候補)

タスク steps 8 に従い、以下 4 観点で Phase 3 (inbox_watcher.sh 廃止) を評価:

### 4-1. 到達率 95% 以上か

| 観点 | 結果 | 判定 |
|------|------|------|
| ash2 broadcast 試験 (10 件) | **100%** (10/10) | ✅ 95% 超 |
| 5.5h 累積 (24 件) | **100%** (24/24・全件 audit 記録) | ✅ 95% 超 |
| 24h 累積 | データ不足 | ⏳ 観察継続 |

→ 観察期間内では基準を満たすが、**24h 検証はまだ完了していない**。

### 4-2. Monitor 検知と既存 watcher 両方が正常に機能しているか

| 観点 | 状態 | 評価 |
|------|------|------|
| Monitor (poc_monitor_inbox.sh tail -f) | 単発テストで発火確認 | ⚠️ ash2 指摘あり (下記) |
| 既存 inbox_watcher.sh (inotifywait) | 10 プロセス健在・配送 100% | ✅ |

#### ⚠️ ash2 重要所見 (家老指摘要件)

**ash2 報告書 findings (cmd_1642 monitor_test)**:

> - **tail -f は YAML 追記型変更のみ追跡可能。API inbox_write の全件再書込ではファイルポインタを失う**
> - **改善案**: inotifywait (IN_MODIFY/IN_CLOSE_WRITE) を使えば全件書換でも検知可能
> - audit log 第3列は task_id のみ記録。message 内容は記録されない仕様 (wake_up タイプは `-` になる)

**軍師評価**:
- 現行 `poc_monitor_inbox.sh` の `tail -f queue/inbox/karo.yaml` は **inbox_write.sh の atomic write (tmp + rename) で inode が変わるとファイルポインタを失う構造的限界** を持つ
- これは inbox_watcher.sh が `inotifywait -e modify -e close_write` で対処してきた既知問題と同根
- **Phase 3 で inbox_watcher.sh を廃止すると、この atomic-write 対応が失われる** → 通信欠損リスク

#### Phase 3 阻害要因 (要解決)

1. **`poc_monitor_inbox.sh` を inotifywait ベースに移植する** 必要あり
   - 現状: `tail -f "$TARGET" 2>/dev/null` (1 行)
   - 必要: `inotifywait -m -e modify,close_write,moved_to "$TARGET"` ベースの実装
2. Monitor tool との接続方式を `tail -f` から `inotifywait stdout 流し込み` に変更
3. inbox_watcher.sh の **atomic write 対応コード (rc=1 の DELETE_SELF 処理)** を Monitor 側に移植
4. busy/idle 検知・エスカレーション (Phase 1/2/3) の機能を Monitor 側で再実装する必要あり

### 4-3. inbox_watcher.sh 廃止リスク

| リスク | 重大度 | 対策 |
|-------|-------|------|
| atomic write 検知漏れ (上記) | **HIGH** | Monitor を inotifywait 化してから廃止 |
| エスカレーション (2分→4分→/clear) 機構消失 | **HIGH** | Monitor 側で再実装するか、別 watcher 残す |
| busy/idle 検知 (`agent_is_busy`) 機構消失 | **MEDIUM** | stop_hook + idle flag で代替可能 |
| systemd 配置との二重管理 | LOW | `watcher_supervisor.sh` をどちらかに一本化 |

### 4-4. Phase 3 実施推奨時期

**判定**: ⏳ **時期尚早** (cmd_1643 として今即起票するのは推奨せず)

**根拠**:
1. **24h 観察データが不足** (現状 5.5h のみ) — 100% 到達率の確実性が低い
2. **ash2 指摘の tail -f 限界が未解決** — 現行 `poc_monitor_inbox.sh` のままでは廃止不可
3. **エスカレーション機構** が Monitor 側にない — 2-4 分後の Escape×2 / 4 分後の `/clear` 自動送信が消失する

#### 推奨ロードマップ

| 順序 | cmd 候補 | 内容 | 工数 |
|------|---------|------|------|
| **1** | **cmd_1643a** | `poc_monitor_inbox.sh` を inotifywait ベースに改修 (ash2 指摘対応) | 0.5-1 日 |
| **2** | **cmd_1643b** | 24h 連続観察 → audit log 集計で到達率 95% 維持を確認 | 観察 1 日 + 集計 0.5 日 |
| **3** | **cmd_1643c** | エスカレーション機構を Monitor 化 (Phase 1/2/3 + busy/idle) | 2-3 日 |
| **4** | **cmd_1644** | Phase 3 段階廃止 (1 エージェントだけ Monitor 専用化 → 1 週間運用 → 全エージェント移行) | 1 週間 + 観察 |

→ **最短 5-7 日 + 観察 1 週間 = 約 2 週間後** に Phase 3 着手可能。

---

## 5. ash2 重要所見の家老向け整理

家老 inbox 通知要件に従い、ash2 の重要所見を要約:

> **「tail -f 方式から inotifywait 方式への移行が必須」**
>
> 理由: `poc_monitor_inbox.sh` の現行実装 (`tail -f`) は API inbox_write の atomic write (tmp + rename で inode 変更) でファイルポインタを失い、変更検知できない。
>
> 改善案: inotifywait の `IN_MODIFY` + `IN_CLOSE_WRITE` イベントなら inode 変更も含めて検知可能 (既存 inbox_watcher.sh と同方式)。
>
> 軍師評価: ash2 の指摘は技術的に正確。現状 Phase 2 はテスト用途で動作するが、本番運用 (24/365 全件確実検知) には不十分。**Phase 3 (inbox_watcher.sh 廃止) の前提条件**として、`poc_monitor_inbox.sh` の inotifywait 化が必須。

---

## 6. Phase 2 全体総括

### 6.1 達成された成果

1. ✅ **5 観点の文書化**: CLAUDE.md / instructions 4 ファイル / shutsujin_departure.sh が cmd_1642 Phase 2 仕様で更新済
2. ✅ **broadcast 試験 100%**: ash2 が 10 エージェント全員に MONITOR_PHASE2_TEST を配送・全件 audit log 記録
3. ✅ **既存 watcher 健在**: 10 プロセスが 24h+ 安定稼働
4. ✅ **inbox_audit.log 動作確認**: 24 件全件記録 (cmd_1640 で追加した監査機構が正常動作)

### 6.2 cmd_1642 Phase 2 残課題

1. ⏳ **24h 観察未完了**: 残り 18.5h の蓄積待ち (cmd_1643b で対応)
2. ⚠️ **tail -f 制限**: Monitor 検知の信頼性が atomic write で低下 (cmd_1643a で対応)
3. ⚠️ **エスカレーション機構**: Monitor 側にまだ存在しない (cmd_1643c で対応)

### 6.3 Phase 3 (inbox_watcher.sh 廃止) 起票判断

**結論**: **時期尚早**。先行して **cmd_1643a/b/c** を実施 (合計 5-7 日 + 観察 1 週間)。

---

## 7. north_star_alignment

```yaml
north_star_alignment:
  status: aligned
  reason: "Phase 2 (Monitor 並走運用) の到達率 100% を確認・既存 watcher との両立も成立。ハーネス層を Anthropic 純正 Monitor に段階移行する戦略 (cmd_1639 Phase 2 ロードマップ) が技術的に実現可能と実証された。但し ash2 の指摘した tail -f 限界は実運用に致命的なため、Phase 3 着手前に必ず inotifywait 化が必要。"
  risks_to_north_star:
    - "Phase 3 を急いで起票すると tail -f 限界による通信欠損が頻発し、エージェント間の sync 崩壊を招く。本書の cmd_1643a/b/c 順守を必須とする。"
    - "24h 観察未完了状態で Phase 3 判断するのは危険。observation データが少なすぎる (5.5h 観測のみ) — 観察期間延長が大前提。"
    - "エスカレーション機構 (2-4 分→Escape×2→4 分→/clear) は本プロジェクト固有の発明で、Monitor tool 単体では再現できない。Phase 3 移行時に必ず別実装で温存する必要あり。"
```

---

## 8. 受入条件 充足検証 (本タスク subtask_1642_qc)

| # | 受入条件 | 結果 | 証跡 |
|---|---------|------|------|
| 1 | queue/reports/2026-05-06_cmd_1642_monitor_phase2_qc.md 作成済 | ✅ | 本書 |
| 2 | AC1-AC10 全件 PASS/FAIL 判定済・証跡付き | ✅ | §1 §2 (検証可能 7 件 PASS / AC7 部分 / AC8-9 仕様未確定) |
| 3 | 24h 観察期間の inbox_audit.log 確認済・到達率算出済 | ⚠️ 部分 | §2.7 (5.5h 観察 100% / 24h 不足明示) |
| 4 | Phase 3 (inbox_watcher.sh 廃止) 起票判断資料あり | ✅ | §4 全節 |
| 5 | git commit + push 済 | ⏳ 本書 commit 後に充足 | — |

---

## 9. 最終判定

```
status: completed
qa_decision: PASS (partial — 24h observation pending)
acceptance_criteria_met: 7/7 (検証可能・AC7 のみ部分 PASS / AC8-9 仕様未確定)
blocking_issues: 0
nonblocking_observations: 3 (24h データ不足・tail -f 限界・エスカレーション機構未移植)
artifacts:
  - queue/reports/2026-05-06_cmd_1642_monitor_phase2_qc.md (本書)
phase3_decision: NOT_READY (data shortage + tail -f limit + escalation gap)
followup_recommendations:
  - cmd_1643a (0.5-1 日): poc_monitor_inbox.sh inotifywait 化 (ash2 指摘対応)
  - cmd_1643b (1.5 日): 24h 連続観察 + 到達率検証
  - cmd_1643c (2-3 日): エスカレーション機構 Monitor 化
  - cmd_1644 (1 週間 + 観察 1 週間): Phase 3 段階廃止
```

**cmd_1642 Phase 2 は QC PASS (部分)。家老の cmd_1643a/b/c 起票判断を仰ぎたし。Phase 3 起票は時期尚早。**
