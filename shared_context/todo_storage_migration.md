# TODO B: 読込API化 + ストレージ移行計画

**起票**: 2026-04-25 / **起票者**: 将軍 (殿命) / **対象**: 中期施策（HIGH 3件 cmd_1477 完遂後）

---

## 殿の問題提起（出発点）

> 「わしはread側もget実装すべきだとおもう　いまだにテキストファイルを全読み込みしているんだろ　それってコンテキスト消費毎ターンしてるんだろ」
> 「ｓｑｌがいいだろ　検索するなら」
> 「textかもやめたいんだが」

殿の指摘は**context経済性**の観点。将軍も軍師(cmd_1475)も見落としていた論点。

## 現状の数値（軍師 cmd_1476 実測値）

| 項目 | 値 |
|---|---|
| shogun_to_karo.yaml | 1675行・約20,000 tokens |
| 1cmd平均行数 | 約93行（command にヒアドキュメント含むため） |
| 家老の毎ターン Read | 全文読込み = 毎回20,000 tokens 消費 |
| 推定削減効果（GET API化） | 約200倍（20,000 → 100 tokens） |

## 軍師cmd_1476 の判定

- **読込API/SQLite化は HIGH に発掘されず**
- shogun_to_karo growth は MEDIUM (atomic write のみ要対応)
- **「全面API化のような抜本改修は不要」** と独立判断

→ 軍師の中立評価と殿の判断が**異なる**ため、**殿命優先**で本TODOに記録

## 段階移行計画

### 段階1: GET API 3本追加 (server.py)
- [ ] `GET /api/cmd_pending?limit=N` (家老向け・status:pending+in_progressのみ)
- [ ] `GET /api/inbox?agent={name}&unread_only=true` (各agent向け・未読のみ)
- [ ] `GET /api/task?agent={name}&active_only=true` (足軽/軍師向け・末尾assignedのみ)
- 規模: server.py +60〜80行
- 工数: 半日（テスト含む）
- 互換性: 既存Read方式と並存（dual-path期間）

### 段階2: agent行動切替 (instructions/*.md 改訂)
- [ ] instructions/karo.md: shogun_to_karo.yaml Read → curl GET /api/cmd_pending
- [ ] instructions/ashigaru.md: queue/tasks/{agent}.yaml Read → curl GET /api/task
- [ ] instructions/gunshi.md: 同様
- [ ] CLAUDE.md inbox処理: queue/inbox/*.yaml Read → curl GET /api/inbox
- 規模: 9エージェント分の手順改訂
- 工数: 1日
- リスク: dual-path 期間の不整合・既読 marking のAPI化要検討

### 段階3: ストレージ JSON Lines化（中規模改修）
- [ ] queue/shogun_to_karo.yaml → queue/shogun_to_karo.jsonl
- [ ] 1cmd = 1行（multiline command は \n エスケープ）
- [ ] append-only運用に最適化（echo >> で 1行追加）
- [ ] migration script: yaml→jsonl 変換
- [ ] server.py を jsonl 読み書きに対応
- [ ] pretool_check.sh / dashboard_lifecycle.sh 等 hooks 改修
- 規模: 大
- 工数: 2-3日
- リスク: hooks/scripts総改修・移行期間の dual-path

### 段階4: SQLite化（殿提案）
- [ ] queue/cmds.db (SQLite WAL mode)
- [ ] commands / inbox_messages / tasks / reports テーブル
- [ ] server.py が SQL queryで動く
- [ ] backup: Litestream + 日次 .sql dump (git管理)
- [ ] dashboard は SELECT で動的生成
- 規模: 超大
- 工数: 1週間
- リスク: バイナリゆえ git管理難・人間直接編集不可・debug難易度上昇

### 段階5: 旧 Read方式の廃止
- [ ] 全agent が curl GET / curl POST のみ使う状態に
- [ ] queue/*.yaml は backward compat のために `GET /api/cmd?format=yaml` で生成
- [ ] dashboard.md 等の人間向けtext表示も HTML+APIに統一
- 規模: クリーンアップ
- 工数: 半日

## リスクと対処

| リスク | 対処 |
|---|---|
| dual-path期間の不整合 | API側を権威ソースに・YAML側はread-only mirror |
| migration中の hooks破壊 | 段階1完了後に1週間 soak / pretool_check の dry-run mode |
| バイナリDB(SQLite)で git diff 不能 | schema migration ファイルを git管理・/cmds dashboard で常時可視化 |
| 殿/家老が直接 cat したい | sqlite3 client alias `dbcat` 等で 1コマンド表示・GET API でJSON取得 |
| 軍師判定との乖離 | 軍師は「現状で問題なし」判定だが、殿の context経済性指摘が決定打 |

## 実施タイミング

- **cmd_1477 (HIGH 3件) 完遂後**に着手
- 段階1のみ短期（GET API追加）→ 動作確認→ 段階2-5は順次
- 全体で 1〜2週間の中期施策

## 関連

- 並行 cmd: cmd_1477 (軍師HIGH 3件: advisor_proxy / inbox_write / logrotate)
- 軍師レポート: queue/reports/gunshi_design_review_1476.yaml
- 殿の context消費指摘: 2026-04-25 18:18 (本会話)

## 次の cmd 発令タイミング

cmd_1477 (A) が**全完遂・dashboard クリア**確認後、将軍が直接 cmd_1480系で段階1開始の cmd を発令。

---

**注**: この TODO は **将軍の備忘録**であり、軍師の独立判断（cmd_1476）とは異なる。殿の判断に基づく中期施策ゆえ、**殿が方針を変えた場合は破棄**してよい。
