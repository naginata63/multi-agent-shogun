# cmd_1644 inbox 通知機構 A/B/C 3 案 技術 QC レビュー報告書

- **報告者**: 軍師 (gunshi)
- **task_id**: subtask_1644_inbox_design_qc
- **parent_cmd**: cmd_1644
- **作成日**: 2026-05-06 04:50 JST
- **判定**: ✅ **完了** — 5 軸評価 / 比較 matrix / 推奨案 / ロードマップ / 殿判断材料を提示
- **中立性宣言**: 将軍 A 案推しの経緯 (cmd_1643 取消) を踏まえ、**技術的根拠のみ** で判断する。盲目的な追従なし。

---

## 0. エグゼクティブサマリ

| 案 | 概要 | 5 軸合計 | 軍師推奨度 |
|----|------|---------|-----------|
| **A 案 (SSE direct stream)** | server.py に `/api/inbox_stream` 追加・Monitor + curl SSE で受信 | **17/25** | △ |
| **B 案 (inotifywait 改善)** | `poc_monitor_inbox.sh` を inotifywait ベースに改修 | **18/25** | ◎ **推奨** |
| **C 案 (現状維持)** | cmd_1642 Phase 2 (tail -f + watcher 並走) を継続 | **17/25** | ○ |

**推奨**: **B 案** (僅差トップ・cmd_1642 ash2 指摘の直接解決・rollback 容易)。但し 3 案いずれも合理的な技術的根拠を持つため、**最終判断は殿の北極星 (純正度 vs 安定 vs 工数)** で決定すべき。

---

## 1. 評価対象 3 案の定義

### 1.1 A 案 — SSE direct stream

**実装内容**:
1. `scripts/dashboard/server.py` に `/api/inbox_stream` エンドポイント追加 (text/event-stream レスポンス)
2. inbox にメッセージ追加時に Server-Sent Event 配信
3. 各エージェントの Monitor tool が `curl -N http://192.168.2.4:8770/api/inbox_stream?agent={id}` を起動
4. SSE 行 = 1 イベント = Monitor tool 通知

**現状**: `server.py` (3389 行) 内に SSE 関連実装は **0 件** (grep で確認済)。**完全新規実装**。
**経緯**: cmd_1643 で起票されたが、殿未承認のため即時取消 (2026-05-06 10:35)。

### 1.2 B 案 — inotifywait 改善

**実装内容**:
1. `scripts/poc_monitor_inbox.sh` の `tail -f "$TARGET"` を `inotifywait -m -e modify,close_write,moved_to "$TARGET"` ベースに置換
2. 既存 `inbox_watcher.sh` の atomic write 対応コード (rc=1 DELETE_SELF 処理) を移植
3. inbox YAML 変更を確実に Monitor tool に流す

**現状**: `inbox_watcher.sh` (1290 行) で inotifywait は本番運用中 ✅。`poc_monitor_inbox.sh` は現在 `tail -f` で 24 行。
**根拠**: cmd_1642 ash2 報告書の改善案として明示的に推奨済 (`tail -f は API inbox_write の全件再書込でファイルポインタを失う・inotifywait なら全件書換でも検知可能`)。

### 1.3 C 案 — 現状維持

**実装内容**:
1. 何もしない
2. cmd_1642 Phase 2 (inbox_watcher.sh + poc_monitor_inbox.sh `tail -f` 並走) のまま継続
3. cmd_1642 で確認された **5.5h 観察 100% 到達率** を信頼

**現状**: ✅ 既に稼働中 (cmd_1642 で QC 済)。
**経緯**: cmd_1642 で軍師が Phase 3 を「時期尚早」と判定済。現状維持の暫定推奨は cmd_1642 §4-4 に記載済。

---

## 2. 5 軸評価 (1-5 点・中立判定)

### 軸 1: YAML 脱却度 (YAML 仲介をどれだけ排除できるか)

| 案 | 点数 | 根拠 |
|----|------|------|
| A 案 | **5** | SSE は server.py 内部キューから直接配信。YAML を読まない経路を新設 |
| B 案 | **1** | inbox YAML を inotifywait で監視し続ける → YAML 仲介は完全継続 |
| C 案 | **1** | YAML 仲介継続 (B と同じ) |

**観察**: A 案のみ YAML 脱却を達成。但し YAML が悪なのか良なのかは別議論 (永続性・人間可読性など利点もある)。

### 軸 2: 取りこぼし耐性 (atomic write・inode 変更・プロセス死亡)

| 案 | 点数 | 根拠 |
|----|------|------|
| A 案 | **4** | server.py 内部キューが Single Source of Truth。但し SSE 切断時のリトライ実装次第・サーバ死亡時は配送途絶 |
| B 案 | **5** | `inotifywait IN_MODIFY/IN_CLOSE_WRITE` で atomic write の inode 変更も検知可能。既存 watcher で実証済 |
| C 案 | **2** | `tail -f` は atomic write で inode 変更時にファイルポインタ消失 (cmd_1642 ash2 指摘) |

**観察**: B 案が最も取りこぼし耐性高。A 案は理論上良いが SSE 接続管理 (再接続・タイムアウト) の実装次第。

### 軸 3: 実装複雑度 (シンプル=高点・複雑=低点)

| 案 | 点数 | 根拠 |
|----|------|------|
| A 案 | **1** | server.py に SSE endpoint 追加 (Flask SSE 実装・GIL 制約・複数クライアント管理) + 認証 + rollback 機構が必要。新規工数 3-5 日想定 |
| B 案 | **4** | 既存 `inbox_watcher.sh` の inotifywait ロジックを `poc_monitor_inbox.sh` に移植のみ。0.5-1 日 |
| C 案 | **5** | 何もしない。0 工数 |

**観察**: 工数最小は C 案。次いで B 案。A 案は最も大きな工数。

### 軸 4: rollback 可能性 (失敗時に旧状態に戻せるか)

| 案 | 点数 | 根拠 |
|----|------|------|
| A 案 | **2** | server.py 改修箇所が広範。`/api/inbox_stream` を含む追加コード ~100 行を git revert する必要。本番稼働中のサーバを停止/再起動するリスクあり |
| B 案 | **4** | `poc_monitor_inbox.sh` 1 ファイルを `tail -f` に戻すだけ。`git revert` 1 commit で完了 |
| C 案 | **5** | rollback 不要 (現状維持) |

**観察**: A 案は rollback コスト最大。B 案は 1 ファイルなのでロールバック容易。

### 軸 5: Anthropic 純正度 (Claude Code 公式ツールの活用度)

| 案 | 点数 | 根拠 |
|----|------|------|
| A 案 | **5** | Monitor + curl SSE は Anthropic Monitor tool の典型的活用パターン (event stream の理想形) |
| B 案 | **4** | Monitor + inotifywait は本プロジェクト固有の組合せ。但し inotifywait は標準 Linux ツール |
| C 案 | **4** | Monitor + tail -f は本プロジェクト固有の組合せ (cmd_1642 で導入) |

**観察**: A 案が Anthropic 推奨パターンに最も近い。B/C はカスタム実装。

---

## 3. 比較 Matrix (5 軸 × 3 案)

| 軸 | 重み | A 案 (SSE) | B 案 (inotifywait) | C 案 (現状維持) |
|----|------|:---------:|:-----------------:|:--------------:|
| 1. YAML 脱却度 | — | 5 | 1 | 1 |
| 2. 取りこぼし耐性 | — | 4 | **5** | 2 |
| 3. 実装複雑度 | — | 1 | 4 | **5** |
| 4. rollback 可能性 | — | 2 | 4 | **5** |
| 5. Anthropic 純正度 | — | **5** | 4 | 4 |
| **合計 (25 点満点)** | — | **17** | **18** | **17** |
| **順位** | — | 2 位 (同点) | **1 位** | 2 位 (同点) |

**僅差注意**: 1 位 B 案 (18) と 2 位 A/C 案 (17) の差は 1 点のみ。**重み付け次第で結果が変わる** ため、殿の北極星選好で最終決定すべき。

### 3.1 重み付けシナリオ (殿向け参考)

| 殿の北極星優先 | 推奨案 |
|---------------|--------|
| 北極星 = **将来の Anthropic 純正一本化** (軸 5 を 2x) | **A 案** (17 + 5 = 22) > B 案 (18 + 4 = 22) ※同点 → A 案優先 |
| 北極星 = **取りこぼし最小化** (軸 2 を 2x) | **B 案** (18 + 5 = 23) > A 案 (17 + 4 = 21) > C 案 (17 + 2 = 19) |
| 北極星 = **工数最小化** (軸 3 を 2x) | **C 案** (17 + 5 = 22) > B 案 (18 + 4 = 22) ※同点 → C 案優先 |
| 北極星 = **rollback 容易性** (軸 4 を 2x) | **C 案** (17 + 5 = 22) > B 案 (18 + 4 = 22) ※同点 → C 案優先 |
| 北極星 = **YAML 脱却** (軸 1 を 2x) | **A 案** (17 + 5 = 22) > B 案 (18 + 1 = 19) > C 案 |

---

## 4. 軍師推奨案 — B 案 (inotifywait 改善)

### 4.1 推奨根拠 (技術的論拠のみ)

1. **5 軸合計で 1 位** (僅差ながら 18 点)
2. **cmd_1642 ash2 報告書の指摘を直接解決**: tail -f の atomic write 限界 → inotifywait で克服
3. **実装コスト最小** (0.5-1 日・1 ファイル改修)
4. **rollback 容易** (1 commit revert で復元)
5. **既存 watcher と同方式** で実装ノウハウ蓄積済 → 失敗リスク低
6. **段階的廃止戦略 (cmd_1642 で軍師判定済の Phase 3 ロードマップ) と整合**: B 案完了後 24h 観察 → エスカレーション機構移植 → Phase 3 (watcher 廃止) という段階で進められる

### 4.2 推奨**しない**根拠 (反対論として併記・中立性確保)

1. **YAML 仲介を継続するため、将来 Anthropic が SSE-first に進化した場合に再移行コストがかかる**
2. **cmd_1641 H3 (inbox_write.sh の venv yaml 単一障害点) は解消されない** → 別 cmd で対応必要
3. **本プロジェクト固有実装が増える** → 新規参加者の学習負荷増 (但し既存 inbox_watcher.sh を読めば理解可能)

### 4.3 「B 案を推奨しない選択肢」も合理的

- **A 案**: 北極星が「Anthropic 純正一本化」なら A 案の方が長期的に正しい (cmd_1643 取消で技術的に否定されたわけではなく、手続き的問題で取消された経緯)
- **C 案**: 北極星が「動いているものを触るな」なら C 案が最も合理的 (5.5h 観察で 100% 到達率実証済)

→ 殿の判断軸次第で 3 案いずれも採用妥当。

---

## 5. 推奨 B 案 実装ロードマップ (Phase 1-3)

### Phase 1: B 案実装 (0.5-1 日)

**cmd_1645a 起票候補**:
- `scripts/poc_monitor_inbox.sh` を inotifywait ベースに改修
- 既存 `inbox_watcher.sh` の rc=1 DELETE_SELF 処理を移植
- 単発テスト: API inbox_write で atomic write 発生 → Monitor tool が検知することを確認

**成果物**:
- `scripts/poc_monitor_inbox.sh` (改修版)
- `queue/reports/YYYY-MM-DD_cmd_1645a_inotifywait_migration.md`

**ロールバック**: `git revert` 1 commit で完了

### Phase 2: 24h 観察 (cmd_1642 残課題と統合・1.5 日)

**cmd_1645b 起票候補**:
- 改修済 Monitor を 24h 連続稼働
- audit log で到達率 95% 以上を維持確認
- atomic write 発生時の検知率 100% を実測

**成果物**:
- 24h 観察レポート

### Phase 3: エスカレーション機構 Monitor 化 (2-3 日)

**cmd_1645c 起票候補**:
- `inbox_watcher.sh` の Phase 1/2/3 エスカレーション (2 分→Escape×2→4 分→`/clear`) を Monitor 側で再実装
- busy/idle 検知 (`agent_is_busy` 相当) を Monitor + idle flag で代替

**成果物**:
- 拡張 Monitor 実装 + テスト

### Phase 4: 段階廃止 (cmd_1644 とは別 cmd・1 週間 + 観察 1 週間)

- 1 エージェント (例: gunshi) のみ Monitor 専用化 → 1 週間運用
- 異常なければ全エージェントに展開
- inbox_watcher.sh プロセス停止 → systemd unit 削除

**最短スケジュール**: 本日着手で **2-3 週間後** に Phase 4 完了。

---

## 6. リスク一覧

### 6.1 技術リスク

| # | リスク | 重大度 | 対策 |
|---|--------|-------|------|
| T1 | inotifywait 移植時の race condition (起動直後のメッセージ取りこぼし) | 中 | 起動時に既存未読 1 回スキャン + その後イベント駆動 |
| T2 | A 案採用時の Flask SSE GIL 制約 (大量同時接続不可) | 高 (A 案のみ) | uvicorn/gunicorn 化 or 別言語 (Go) で実装 |
| T3 | C 案継続時の atomic write 取りこぼし (cmd_1642 で実証された限界) | 中 | inbox_watcher.sh で代替検知 → 限界を黙認・運用 |
| T4 | B 案で venv yaml 依存 (H3) は解消されない | 中 | 別 cmd で API 経由化 (cmd_1494 方針継続) |

### 6.2 運用リスク

| # | リスク | 重大度 | 対策 |
|---|--------|-------|------|
| O1 | A 案採用時の rollback 困難 (server.py 改修範囲広) | 高 (A 案のみ) | 段階導入・1 エンドポイントずつ feature flag で切替 |
| O2 | B 案実装中に既存 watcher が誤動作 (二重発火) | 中 | poc_monitor_inbox.sh 改修中は inbox_watcher.sh のみ稼働継続 |
| O3 | C 案継続のまま放置で技術負債蓄積 | 中 | 半年に 1 度 (cmd_1700 候補) の再評価必須 |

### 6.3 互換性リスク

| # | リスク | 重大度 | 対策 |
|---|--------|-------|------|
| C1 | cmd_1642 で配置済 instructions/CLAUDE.md の変更が必要になる | 中 | 影響箇所を事前 grep・段階対応 |
| C2 | 既存 cron 系 (silent_fail_watcher 等) が新方式と衝突 | 低 | 並走運用で衝突検出 |
| C3 | systemd unit の管理方式変更 | 中 | `watcher_supervisor.sh` への組込判断必要 |

---

## 7. 殿への判断材料 — 採用案ごとの次アクション

### 7.1 採用 A 案 (SSE direct stream) の場合

**北極星**: 将来の Anthropic 純正一本化を最優先

**次アクション**:
1. **cmd_1645 (A1) 起票**: `server.py /api/inbox_stream` SSE 設計書作成 (gunshi 担当・3-5 日)
   - Flask vs FastAPI vs aiohttp 比較
   - 認証・再接続・複数クライアント対応設計
2. **cmd_1645 (A2) 起票**: 上記設計書承認後の実装 (足軽複数名・3-5 日)
3. **cmd_1645 (A3) 起票**: Monitor tool との接続テスト + 24h 観察
4. **cmd_1645 (A4) 起票**: 段階廃止 (1-2 週間)

**総工数**: 約 3-4 週間 + 観察期間

### 7.2 採用 B 案 (inotifywait 改善) の場合 — **軍師推奨**

**北極星**: 取りこぼし最小化 + 実装コスト最小

**次アクション**:
1. **cmd_1645a 起票**: `poc_monitor_inbox.sh` inotifywait 化 (足軽 1 名・0.5-1 日)
2. **cmd_1645b 起票**: 24h 観察 + 到達率検証 (1.5 日)
3. **cmd_1645c 起票**: エスカレーション機構 Monitor 化 (2-3 日)
4. **cmd_1646 起票**: Phase 3 段階廃止 (1 週間 + 観察 1 週間)

**総工数**: 約 2-3 週間

### 7.3 採用 C 案 (現状維持) の場合

**北極星**: 動いているものを触らない・工数 0 を最優先

**次アクション**:
1. **cmd_1645 起票**: 半年後再評価タスク (gunshi・2026-11 頃)
2. cmd_1641 H1/H2/H4/H5 (1 H 修正可能・本案件と独立) のみ着手
3. tail -f atomic write 限界を **既知の運用制約** として `instructions/*.md` に明記

**総工数**: 0 (再評価コストのみ)

---

## 8. 中立性宣言の自己検証

タスク notes に「中立性最重要: 将軍がA案(SSE)を推したが殿未承認で取消された経緯あり」とある。本書の中立性確保:

1. ✅ **A 案を排除していない**: §1.1 で技術仕様明示・§3.1 で「北極星 = Anthropic 純正なら A 案優先」と提示
2. ✅ **B 案推奨の反対論を §4.2 に併記**: 「B 案を推奨しない理由 3 件」
3. ✅ **重み付けシナリオを §3.1 で 5 通り提示**: 北極星次第で結果が変わることを明示
4. ✅ **採用 3 案ごとの次アクションを §7 で対称的に記述**: A/B/C いずれも合理的選択として扱う
5. ✅ **将軍経緯への言及は §0 と §1.1 のみ**: 取消は「手続き問題」であり「技術的否定ではない」と明示

→ 軍師の中立性確保 OK。**最終判断は殿に委ねる**。

---

## 9. north_star_alignment

```yaml
north_star_alignment:
  status: aligned
  reason: "3 案を 5 軸で技術中立に評価し、僅差トップ (18 点) の B 案を技術的根拠で推奨。但し A/C 両案も 17 点で僅差のため、北極星選好次第で結果が変わることを §3.1 で明示し、殿の最終判断を尊重する設計。"
  risks_to_north_star:
    - "B 案推奨が「将軍 A 案を否定」と誤解される可能性 — §4.2 で B 案反対論を併記し、§7.1 で A 案採用ロードマップも対称的に提示することで回避。"
    - "5 軸の重み付けを軍師が固定したと誤解される可能性 — §3.1 で重み付けシナリオを 5 通り提示し、判断軸は殿に委ねていることを明示。"
    - "1 位 B 案と 2 位 A/C 案の差が 1 点と僅差のため、5 軸の数値より定性判断 (殿の運用感覚) が決定的になる可能性 — その場合は殿の判断を最大尊重する。"
```

---

## 10. 受入条件 充足検証

| # | 受入条件 | 結果 | 証跡 |
|---|---------|------|------|
| 1 | queue/reports/2026-05-06_cmd_1644_inbox_design_qc.md 作成済 | ✅ | 本書 |
| 2 | A/B/C 3 案の 5 軸評価 (1-5 点) が全て含まれる | ✅ | §2 (15 セル全て点数付き) |
| 3 | 5 軸 × 3 案の比較 matrix (table 形式) あり | ✅ | §3 |
| 4 | 推奨案と技術的根拠が明記 | ✅ | §4 (B 案・5 つの根拠) |
| 5 | 推奨案の実装ロードマップ Phase 1-3 あり | ✅ | §5 (Phase 1-4) |
| 6 | リスク一覧 (技術/運用/互換性) あり | ✅ | §6 (T1-T4 / O1-O3 / C1-C3 全 10 件) |
| 7 | 殿への判断材料セクション (採用案ごとの次アクション) あり | ✅ | §7 (A/B/C 全 3 ケース) |
| 8 | 中立性厳守 (将軍 A 案を盲目的に推薦していない) | ✅ | §8 中立性宣言の自己検証 |
| 9 | git commit + push 済 | ⏳ 本書 commit 後に充足 | — |

---

## 11. 最終判定

```
status: completed
acceptance_criteria_met: 8/9 (git commit 後に 9/9)
recommendation: B 案 (inotifywait 改善)
recommendation_score: 18/25 (1 位・僅差)
neutrality_check: PASS (§4.2 反対論併記 + §7 対称ロードマップ + §3.1 重み付け 5 シナリオ)
artifacts:
  - queue/reports/2026-05-06_cmd_1644_inbox_design_qc.md (本書)
followup_recommendations_per_case:
  A_adopted:
    - cmd_1645a-d (3-4 週間)
  B_adopted: # 軍師推奨
    - cmd_1645a (poc_monitor inotifywait 化・0.5-1 日)
    - cmd_1645b (24h 観察・1.5 日)
    - cmd_1645c (エスカレーション機構移植・2-3 日)
    - cmd_1646 (Phase 3 段階廃止・2 週間)
  C_adopted:
    - 半年後再評価 cmd (cmd_1700 候補・2026-11)
    - cmd_1641 H1/H2/H4/H5 修正 (1 H・独立)
```

**本書は技術中立 QC レビュー完了。3 案いずれも合理的選択肢。最終判断は殿の北極星選好に委ねる。**
