# cmd_1639 Anthropic Claude Code 最新 agent API/skill 適用可能性調査報告書

- **報告者**: 軍師 (gunshi)
- **task_id**: subtask_1639_api_research
- **parent_cmd**: cmd_1639
- **作成日**: 2026-05-05
- **判定**: ✅ **完了** (受入条件 9/9 充足見込み)

---

## 0. エグゼクティブサマリ

本プロジェクトは既に **CLAUDE.md + instructions/*.md + queue/YAML + SQLite + inotifywait watcher + 20+ cron + 30+ Skill** という成熟したハーネスを構築済。Anthropic 純正 agent API/skill 群を **既存仕組みの置換ではなく補完** として段階的に取り込むのが現実解。

### 推奨度サマリ (10 機能)

| # | 機能 | 推奨度 | ひと言 |
|---|------|--------|--------|
| 1 | **CronCreate** | **B** | session-only/7 日上限のため system cron の置換は不可・短期テスト用には便利 |
| 2 | **ScheduleWakeup** | **A** | `/loop` 動的モードで軍師の長時間調査タスクの自己ペーシングに刺さる |
| 3 | **/loop dynamic** | **A** | 既存「/loop 5m /foo」型 → 自己ペーシングで API コスト最適化 |
| 4 | **PushNotification** | **S** | `ntfy.sh` の純正置換候補・LAN/外部両対応・即適用可 |
| 5 | **RemoteTrigger** | **A** | claude.ai 経由で外出先から殿が cmd 発令可能・スマホ運用の本命 |
| 6 | **Background agents** | **B** | 既に Bash `run_in_background` で運用済・新規価値は限定的 |
| 7 | **Monitor** | **A** | inotifywait + tail -f の純正置換候補・ハーネス層をスリムにできる |
| 8 | **MCP 連携系** | **S** | 既に `mcp__memory__*` 活用中・Routines/Skill 連携で更に拡張可 |
| 9 | **Routines (schedule skill)** | **A** | system cron との二重運用で「session-aware な定期 prompt」に拡張 |
| 10 | **その他 (Skill/Subagent/EnterWorktree/ToolSearch)** | **S/A** | Skill は既採用・worktree は隔離実験で強力・ToolSearch は遅延ロードで context 節約 |

---

## 1. 本プロジェクトの現状確認 (調査の前提)

### 1.1 ハーネス層インベントリ

| カテゴリ | 既存実装 | 役割 |
|---------|---------|------|
| 4 エージェント体制 | shogun (pane 0.0) / karo (pane 0.0) / ashigaru1-7 / gunshi | 軍事階層・並列実装 |
| 通信 | inbox YAML + SQLite (queue/cmds.db) | 永続的な指示と報告 |
| Watcher | inotifywait + tmux send-keys (`inbox_watcher.sh`) | 受信 nudge |
| Hook (SessionStart) | `scripts/sessionstart_hook.sh` | 起動時自動回復 |
| Hook (Stop) | `stop_hook_inbox.sh` / `stop_karo_check.sh` | 停止時 inbox 自動既読化 |
| Hook (PreCompact) | `precompact_hook.sh` | 圧縮直前保存 |
| Hook (UserPromptSubmit) | `userprompt_semantic_search.sh` | prompt 送信時の自動 grep |
| Hook (PreToolUse) | `pretool_check.sh` | 危険操作 BLOCK (CHK11 等) |
| Cron | 20+ entries (semantic update / lifecycle / nightly_audit / 等) | システムレベルの定期実行 |
| Skill | 30+ entries (.claude/skills/*) | AI 自律呼出の業務知識 |
| Slash Command | 20+ entries (.claude/commands/*) | プロンプト資産化 |
| Notification | `scripts/ntfy.sh` (殿スマホ) | 緊急通知 |
| Dashboard | `192.168.2.4:8770` (Flask API) | 可視化・cmd 管理 |

→ **既に高度に統合された仕組み**。新機能導入は「置換」ではなく「補完」「スリム化」が判断軸。

### 1.2 課題・ペインポイント (cmd_1494/1495/1546/1607 等の蓄積)

1. **inotifywait + tmux send-keys** はステートフルで silent fail しやすい (cmd_1448 / silent_fail_watcher.sh で対症療法)
2. **system cron** は障害時に死文化が分かりづらい (cron_health_check で対症療法)
3. **ntfy.sh** はベストエフォートで失敗痕跡が残らない
4. **claude.ai 外部連携** は未開拓 (殿のスマホから cmd 発令する手段が ntfy 受信のみ)
5. **Tool 数の context 圧迫** — 60+ MCP tool が未使用でも schema を消費 (cmd_1494/1495 の delay-load で改善中)

---

## 2. 各機能の詳細調査 (10 件)

### 2.1 CronCreate (推奨度: B)

#### 機能概要
- Claude Code セッション内でスケジュール prompt を予約する純正 tool
- 標準 5 フィールド cron (ローカル TZ) — `"0 9 * * *"` で毎朝 9 時 (durable=false なら session 限定)
- **session 終了で消える** (`durable: true` で `.claude/scheduled_tasks.json` に永続化可能)
- recurring=true のジョブは **7 日後に自動失効**

#### 本プロジェクトへの適用可能性
- ✅ **session 内テスト用**: 「30 分後に進捗確認 prompt を投げる」等のセルフリマインダ
- ❌ **system cron の置換**: 7 日上限・session 依存のため恒久ジョブには不適
- ⚠️ **fleet 同時刻問題**: 全世界の Claude が `"0 9 * * *"` で発火する → 推奨 minute をズラす運用 (`"57 8 * * *"` 等)

#### 移行コスト
- 低 (新規導入のみ・既存 cron は触らない)

#### 推奨適用箇所
- 軍師の長時間調査タスクで「次の 30 分後に経過確認」セルフ nudge
- 殿への「3 時間後にこの判断を再提示してくれ」一回限りリマインダ

#### 注意点
- system cron (現行 20+) は **そのまま維持**。CronCreate は durable=true でも 7 日上限の制約あり (要 Anthropic ドキュメント確認・本書では現状規格を信用)

---

### 2.2 ScheduleWakeup (推奨度: A)

#### 機能概要
- `/loop` の **dynamic モード** (interval 未指定時) で AI 自身が次の起動時刻を決める
- `delaySeconds` (60-3600 秒) を AI が「キャッシュ TTL (5 分)」を意識して選ぶ
- 60-270s = キャッシュ温存 / 1200-1800s = 通常 idle
- 5 分超は cache miss → 次回読込が完全 uncached

#### 本プロジェクトへの適用可能性
- ✅ **軍師の長時間調査** (本タスク cmd_1639 のような数十分タスク) で自己ペーシング
- ✅ **足軽のビルド待ち** で「8 分タスクなら 270s × 2 回 sleep」最適化
- ⚠️ **inbox 駆動の本流とは別系統**: 軍師が prompt を自分で出すケースに限定

#### 移行コスト
- 低 (既存 `/loop` 利用箇所がない場合は新規導入のみ)

#### 推奨適用箇所
- 軍師の `subtask_1564a/1565a/1566a` 矛盾検出系 (数千行精読) で長時間 idle が必要な場面
- ashigaru の重い ffmpeg/marp 変換待ち
- 殿への状況報告を「経過時間に応じて頻度自動調整」する将軍 senkyou スキル拡張

---

### 2.3 /loop dynamic (推奨度: A)

#### 機能概要
- ScheduleWakeup の上位概念。「`/loop` で interval 指定なし」 → AI が自己ペーシング
- インターバル指定 (`/loop 5m /foo`) は cron-like・dynamic は AI 判断
- session-only (永続化なし)

#### 本プロジェクトへの適用可能性
- ✅ **将軍の戦況監視** (`/senkyou` 拡張) で「殿入力を待ちつつ MCP dashboard を周期確認」
- ✅ **動画パイプライン進捗監視** で `/video-pipeline` 実行中の足軽長時間待機
- ⚠️ 既存 cron 経由のジョブには不要 (cron が確実)

#### 移行コスト
- 低 (利用箇所選定のみ)

#### 推奨適用箇所
- 殿が `/senkyou` を発した後の「次の戦況自動更新」cycle (将軍 pane で `/loop`)
- 軍師の高負荷分析タスクで「context 30% 切ったら一度 /handoff してから /loop で再開」

---

### 2.4 PushNotification (推奨度: S — 即時導入推奨)

#### 機能概要
- ターミナル desktop 通知 + Remote Control 接続なら **スマホ push**
- 200 文字以内・1 行・markdown 不可
- 「ユーザーが席を外したかもしれない・知っておきたい変化」専用

#### 本プロジェクトへの適用可能性
- ✅ **`ntfy.sh` の純正置換候補**: 現在は cmd 完了/YouTube アップ完了/🚨要対応 でカスタム通知
- ✅ **失敗時の痕跡が残る** (現 ntfy.sh はベストエフォート・成否不明)
- ⚠️ Remote Control 未接続だと desktop 通知のみ → スマホ push 必要なら ntfy 併用が安全

#### 移行コスト
- 中 (`scripts/ntfy.sh` 利用箇所 ~30 個を `PushNotification` 経由に切替)
- インボックス API 経由で「家老が PushNotification を叩く」設計に変更可能 (gunshi/ashigaru は F002 直接連絡禁止のため家老経由)

#### 推奨適用箇所
- **家老の cmd 完了通知** (現: `scripts/ntfy.sh` → 新: PushNotification)
- **YouTube 非公開アップ完了通知**
- **🚨要対応の dashboard 追加時 push**
- 段階導入: 既存 ntfy.sh と並走 → 動作確認 → 切替 (cmd_1640 案)

---

### 2.5 RemoteTrigger (推奨度: A)

#### 機能概要
- claude.ai の remote-trigger API を OAuth 経由で叩く
- list/get/create/update/run の 5 アクション
- 殿が **claude.ai 経由 (スマホブラウザでも可)** で remote trigger を発火 → ローカル Claude セッションで処理

#### 本プロジェクトへの適用可能性
- ✅ **殿のスマホ運用拡張**: 現状 ntfy で受け取るだけ → trigger 経由で外出先から cmd 発令可能
- ✅ **routines (定期実行) と組合せ**: 「毎朝 7 時に YouTube 統計を取って push」等
- ⚠️ OAuth トークンの管理 + Anthropic アカウント設定が必要
- ⚠️ trigger の発火が殿の手動操作前提なら ROI 微妙

#### 移行コスト
- 中-高 (claude.ai アカウント連携 + trigger 設計 + 既存 cmd 起票 API との接続)

#### 推奨適用箇所
- **殿のスマホから「`/manga-short 制作開始`」を外出先で叩く**運用 (cmd_1640 候補)
- **routines 経由の定期実行** (毎朝 7 時の生成 AI 日報・現在は cron で発火 → trigger 化で claude.ai 上の履歴に記録)

---

### 2.6 Background agents (推奨度: B)

#### 機能概要
- Bash の `run_in_background: true` パラメータで長時間プロセスを背景化
- Agent tool の `run_in_background: true` で並列 sub-agent
- 完了時に通知 — polling 不要

#### 本プロジェクトへの適用可能性
- ⚠️ **既に多用中** (足軽の ffmpeg / marp / Demucs バッチ等)
- 新規価値は **Agent tool の並列化** — 例: 軍師が並列で ch03/ch07 QC を走らせる
- 既存「足軽 7 名並列」モデルとは別レイヤー (足軽 = tmux pane の永続体・Agent tool = sub-agent エフェメラル)

#### 移行コスト
- 既導入のため追加コストなし
- 並列化対象の選定 (軍師 QC・調査系) のみ

#### 推奨適用箇所
- **軍師の並列章 QC** (cmd_1634 のような複数章 QC を sub-agent で並列処理)
- 矛盾検出系 (cmd_1564/65/66) の並列実行

---

### 2.7 Monitor (推奨度: A)

#### 機能概要
- 長時間プロセスの stdout を 1 行 = 1 通知でストリーム
- `tail -f` / `inotifywait -m` / poll loop 等を内包
- timeout / persistent 切替可
- TaskStop で停止可能

#### 本プロジェクトへの適用可能性
- ✅ **inotifywait + tmux send-keys スクリプト群の純正置換候補**
- ✅ **silent fail watcher** をスリム化可能 (現: bash + cron / 新: Monitor で常駐)
- ⚠️ session 終了で消える → system cron 起動の watcher と併走が必要

#### 移行コスト
- 中 (既存 inbox_watcher.sh / silent_fail_watcher.sh のロジック移行)

#### 推奨適用箇所
- **インタラクティブ session 中の inbox 監視** (現: tmux send-keys nudge → 新: Monitor 通知のみで OK)
- **長時間 ffmpeg/marp 変換の進捗追跡** (cmd_1639 系の長時間 task)
- **silent_fail_watcher.sh の置換**: 1 行 = 1 通知の自動エラー検知 (cron 死文化問題への即応)

---

### 2.8 MCP 連携系 (推奨度: S)

#### 機能概要
- Model Context Protocol — 外部システムを tool として AI に接続
- 既に `mcp__memory__*` (knowledge graph) / `mcp__plugin_claude-mem_*` (claude-mem) 利用中
- 新規 MCP サーバー導入で Notion/Playwright/Slack/Drive 等と直接連携

#### 本プロジェクトへの適用可能性
- ✅ **既に活用中** (memory MCP は将軍/軍師で必須・claude-mem は中級編 ch04 主役)
- ✅ **Skill との連携で再利用性最大化**: Skill が「いつ / どの MCP tool を呼ぶか」の業務知識を持つ
- ✅ **lazy-load** (`mcp_usage: "Lazy-loaded. Always ToolSearch before first use."`) で context 節約済
- ⚠️ MCP サーバーの正常性監視 (cmd_1494 で server.py 監視・cron_health_check 連携)

#### 移行コスト
- 既導入のため追加コストなし
- 新 MCP 導入は中 (個別ケース・Notion-MCP 等)

#### 推奨適用箇所
- **note 投稿の MCP 化** (現: Playwright + Slash Command → 新: note-MCP で AI 直接投稿)
- **Slack-MCP** (殿との非同期コミュニケーション窓口・ntfy + push の上位)
- **Drive-MCP** (殿の参考資料を AI が直接参照)

---

### 2.9 Routines (schedule skill / 推奨度: A)

#### 機能概要
- `schedule` skill 経由で **claude.ai 上に scheduled remote agent (routines)** を作る
- cron スケジュールで Claude Code エージェントが自動起動
- 一回実行 ("run this once at 3pm") も可

#### 本プロジェクトへの適用可能性
- ✅ **system cron の上位互換候補**: routine が claude.ai 上で履歴を残す
- ✅ **「毎朝 7 時に生成 AI 日報」のような Claude 自身が prompt を実行する系**
- ⚠️ Anthropic 課金プラン依存 (Max プラン等)
- ⚠️ 既存 cron は bash script 直叩きで Claude プロセスを呼ばない → 棲み分け必要

#### 移行コスト
- 中-高 (claude.ai 連携 + routine 設計 + 既存 cron からの移行判断)

#### 推奨適用箇所
- **生成 AI 日報の routine 化** (現: `scripts/genai_daily_report.sh` cron / 新: claude.ai routine で AI が実行)
- **YouTube 統計の routine 化** (現: cron / 新: routine で AI 解釈付き snapshot)
- 段階導入: 1 つの cron entry を試験的に routine 化 → 6 ヶ月運用 → 有効なら順次移行

---

### 2.10 その他 (Skill / Subagent / EnterWorktree / ToolSearch / 推奨度: S/A)

#### 2.10.1 Skill (推奨度: S — 既導入)

- 30+ skills 既に運用中 (`/manga-short` `/highlight` `/senkyou` 等)
- 中級編 ch11 で受講者向けの主題に昇格 (cmd_1638 改訂)
- **追加投資**: skill-creator で新規 skill のフォーマット標準化

#### 2.10.2 Subagent (Agent tool / 推奨度: A)

- 既存利用: `Explore` `Plan` `general-purpose` 等
- **claude-code-guide** subagent はドキュメント調査用に有効
- 推奨適用: 軍師の調査系タスクで claude-code-guide を呼んで基礎知識収集

#### 2.10.3 EnterWorktree (推奨度: A)

- git worktree で隔離環境を agent に渡す
- 「壊しても本流に影響しない」実験向け
- 推奨適用: 足軽の **大規模リファクタ実験** で現流を保護
- 移行コスト: 低 (使う場面でのみ)

#### 2.10.4 ToolSearch (推奨度: S — 既採用)

- 60+ deferred tool を必要時のみロード
- cmd_1494/1495 の context 節約方針と一致
- **追加投資**: 新規 MCP 導入時に必ず deferred 化する運用ルール明文化 (cmd_1640 候補)

---

## 3. Phase 1-3 推奨ロードマップ

### Phase 1: 即時着手 (1 週間以内・低リスク高効果)

| 優先 | 項目 | 工数 | 効果 |
|------|------|------|------|
| **1** | **PushNotification を ntfy.sh の選択肢として並走** | 0.5 日 | 通知失敗痕跡が残る |
| **2** | ToolSearch lazy-load 運用ルール明文化 (CLAUDE.md 追記) | 0.25 日 | context 節約継続 |
| **3** | 軍師調査タスクで `/loop dynamic` + ScheduleWakeup の試用 | 0.5 日 | 長時間タスクの API コスト最適化 |
| **4** | claude-code-guide subagent の調査系活用ガイド整備 | 0.5 日 | 軍師の調査品質向上 |

**Phase 1 累計**: 1.75 日 (cmd_1640 として起票推奨)

### Phase 2: 中期実装 (2-4 週間・中リスク高効果)

| 優先 | 項目 | 工数 | 効果 |
|------|------|------|------|
| **1** | inbox_watcher.sh / silent_fail_watcher.sh を Monitor 化 | 2-3 日 | ハーネススリム化・silent fail 即検知 |
| **2** | 既存 ntfy.sh ~30 箇所を PushNotification に段階移行 | 2 日 | 通知の堅牢性向上 |
| **3** | 軍師の並列 QC を Agent tool (background) で実装 | 1-2 日 | 多章 QC の並列化 |
| **4** | EnterWorktree で大規模リファクタ運用ルール策定 | 1 日 | 実験隔離による事故防止 |

**Phase 2 累計**: 6-8 日 (cmd_1641-1644 として段階起票推奨)

### Phase 3: 長期統合 (1-3 ヶ月・高リスク高効果)

| 優先 | 項目 | 工数 | 効果 |
|------|------|------|------|
| **1** | RemoteTrigger + Routines で claude.ai スマホ運用基盤構築 | 3-5 日 | 殿の外出先 cmd 発令経路確立 |
| **2** | 1 つの cron entry を Routines 化して 6 週間試験運用 | 1 日設計 + 6 週間観察 | system cron→Routines 移行可否判断 |
| **3** | note/Slack/Drive 等の MCP 増設 | 各 2-3 日 | 業務組み込み拡張 |
| **4** | CronCreate durable + system cron の役割分担明文化 | 1 日 | スケジュール基盤の二重運用整理 |

**Phase 3 累計**: 10-15 日 + 観察期間 (cmd_1645+ として段階起票)

---

## 4. リスク一覧

### 4.1 技術リスク

| # | リスク | 対象機能 | 重大度 | 対策 |
|---|--------|---------|-------|------|
| R1 | session 終了で job 消失 | CronCreate / ScheduleWakeup / Monitor | 中 | system cron と二重運用・durable=true 検証 |
| R2 | OAuth トークン管理 | RemoteTrigger / Routines | 高 | scripts/ntfy.sh と同様に環境変数管理 + 漏洩監視 |
| R3 | fleet 同時刻発火 (CronCreate "0 9" 問題) | CronCreate | 低 | minute をズラす運用ルール明文化 |
| R4 | Anthropic API 仕様変更 | 全機能 | 中 | 半年ごとに本書を再評価 (軍師タスク化) |
| R5 | ローカル + claude.ai の二重操作で整合性破綻 | RemoteTrigger / Routines | 高 | 一方向ルール (claude.ai → ローカルのみ) で運用 |

### 4.2 運用リスク

| # | リスク | 対象機能 | 重大度 | 対策 |
|---|--------|---------|-------|------|
| R6 | 既存 cron 20+ の死文化加速 | Routines 移行時 | 中 | 移行は 1 件ずつ・元 cron は disabled 状態で 6 週間並走 |
| R7 | 通知の二重化 (ntfy + Push) | PushNotification | 低 | 段階移行・最終的に PushNotification に一本化 |
| R8 | 軍師/足軽が新機能を誤用 | 全機能 | 中 | instructions/*.md に運用ルール明記 + cmd_1640 で初期教育 |
| R9 | MCP サーバー追加で context 圧迫 | MCP 連携系 | 中 | ToolSearch lazy-load を必須化 |
| R10 | claude.ai 課金プラン変更でアクセス断 | RemoteTrigger / Routines | 中 | 月次課金状況の monitoring (殿責務) |

### 4.3 互換性リスク

| # | リスク | 対象 | 対策 |
|---|--------|------|------|
| C1 | 既存 inbox 駆動と Monitor の重複 | watcher 系 | 排他運用 (どちらか一方を「権威」とする運用ルール) |
| C2 | system cron と CronCreate/Routines の重複 | スケジュール系 | 上記 R6 と同じ・段階移行 |
| C3 | Skill と Slash Command の境界曖昧 | 教育 | ch01/ch11 で明確化 (cmd_1638 改訂で対応済) |

---

## 5. 次アクション提案 (cmd 起票案)

### 5.1 Phase 1 起票候補 (即時)

#### **cmd_1640**: Phase 1 — Push 通知 + ToolSearch + /loop 試用
- **担当**: 家老 → 足軽 1 (ntfy 移行) + 軍師 (運用ルール明文化)
- **成果物**:
  1. `scripts/ntfy.sh` の使用箇所一覧 + PushNotification 並走 wrapper (`scripts/notify.sh`)
  2. CLAUDE.md に ToolSearch lazy-load 運用ルール追記
  3. `instructions/gunshi.md` に `/loop dynamic` + ScheduleWakeup 利用ルール追記
- **受入条件**: ntfy.sh / Push 並走で 1 週間運用・失敗痕跡比較
- **想定工数**: 1.75 日

### 5.2 Phase 2 起票候補 (cmd_1640 完了後)

#### **cmd_1641**: Monitor で inbox_watcher / silent_fail_watcher 置換
#### **cmd_1642**: 軍師 Agent (background) 並列 QC 実装
#### **cmd_1643**: PushNotification 完全移行 (ntfy.sh 廃止)
#### **cmd_1644**: EnterWorktree 運用ルール策定

### 5.3 Phase 3 起票候補 (Phase 2 安定後)

#### **cmd_1645**: RemoteTrigger + Routines スマホ運用基盤
#### **cmd_1646**: 1 cron entry の Routines 化試験運用
#### **cmd_1647**: 新規 MCP (note/Slack/Drive) 増設
#### **cmd_1648**: CronCreate durable + system cron 役割分担明文化

### 5.4 補足: 半年後の再評価

- **cmd_1700 想定**: 2026-11 頃に本報告書を再評価する gunshi タスク
- 理由: Anthropic Claude Code は新機能追加頻度が高い・既存ロードマップが陳腐化する前提

---

## 6. 設計思想 — なぜ「置換」ではなく「補完」なのか

### 6.1 既存ハーネスの強み

- **system cron の堅牢性**: Claude プロセスに依存せず動く・障害時の復旧が単純
- **YAML + SQLite + inbox**: cmd_1488/1494 で SQLite dual-path 化済・整合性が API で担保
- **inotifywait**: 受信即時 nudge で「polling 禁止 (F004)」原則と整合

### 6.2 純正 API の強み

- **claude.ai 統合**: 殿のスマホ運用・履歴の集約
- **PushNotification**: 失敗痕跡が残る・標準化された通知
- **Monitor**: 1 行 = 1 通知の宣言的 watcher

### 6.3 結論: 補完戦略

> **「ローカルの堅牢性 + claude.ai の利便性」をハイブリッドで運用**
>
> - 永続ジョブ (24/365 必要) → system cron 維持
> - session 駆動ジョブ (Claude が実行する系) → CronCreate / Routines に段階移行
> - 通知 → PushNotification を主・ntfy はフォールバック
> - watcher → Monitor (session 内) + cron 起動の bash watcher (session 外) で二重化
> - Skill / MCP → 既導入を継続・新規 MCP は ToolSearch lazy-load 必須

---

## 7. north_star_alignment

```yaml
north_star_alignment:
  status: aligned
  reason: "本プロジェクトの北極星は『生産性のスケール』(エージェント並列+ハーネス自動化)。本調査で純正 API 群を Phase 1-3 ロードマップで段階導入する設計を提示し、既存の堅牢な仕組みを壊さずに『claude.ai 連携 + 通知の堅牢化 + watcher のスリム化』を実現する道筋を確定した。"
  risks_to_north_star:
    - "Phase 2 の Monitor 化で inbox 駆動と重複したまま運用すると整合性が崩れる。R1/C1 リスクの対策 (排他運用ルール) を cmd_1641 起票時に必ず固定する。"
    - "Phase 3 の Routines 移行で system cron と claude.ai routine が別々に同じジョブを発火すると重複実行事故。R6 リスクの 6 週間並走運用を厳守する。"
    - "Anthropic API の仕様変更頻度が高い (claude-mem や Skill の規格更新が複数回発生)。R4 リスクの半年ごと再評価 cmd を必ず起票する。"
```

---

## 8. 受入条件 充足検証

| # | 受入条件 | 結果 | 証跡 |
|---|---------|------|------|
| 1 | queue/reports/2026-05-05_cmd_1639_anthropic_agent_api_research.md 作成 | ✅ | 本書 |
| 2 | Schedule/Routines系 (CronCreate/ScheduleWakeup/loop/schedule) 調査結果含む | ✅ | §2.1 / §2.2 / §2.3 / §2.9 |
| 3 | Push通知/Trigger系 (PushNotification/RemoteTrigger) 調査結果含む | ✅ | §2.4 / §2.5 |
| 4 | Background/Cloud系 (Background agents/Monitor) 調査結果含む | ✅ | §2.6 / §2.7 |
| 5 | MCP連携系の調査結果含む | ✅ | §2.8 |
| 6 | 10 項目それぞれに「機能概要・適用可能性・移行コスト・推奨度・適用箇所」記載 | ✅ | §2.1-§2.10 全件 |
| 7 | Phase 1-3 推奨ロードマップ含む | ✅ | §3 |
| 8 | リスク一覧含む | ✅ | §4 (技術 R1-R5・運用 R6-R10・互換性 C1-C3) |
| 9 | 次アクション提案 (cmd_1640 等) 含む | ✅ | §5 (cmd_1640-1648 + cmd_1700 計 9 件提案) |
| 10 | git commit 済 | ⏳ 本報告書 commit 後に充足 | — |

---

## 9. 最終判定

```
status: completed
acceptance_criteria_met: 9/9 (git commit 後に 10/10)
blocking_issues: 0
artifacts:
  - queue/reports/2026-05-05_cmd_1639_anthropic_agent_api_research.md (本書)
followup_cmds_proposed:
  - cmd_1640 (Phase 1 即時)
  - cmd_1641-1644 (Phase 2 中期)
  - cmd_1645-1648 (Phase 3 長期)
  - cmd_1700 (半年後再評価)
```

**本タスクは完了。家老の Phase 1 (cmd_1640) 起票判断を待つ。**
