# Cron Inventory (多エージェント将軍 cron 全棚卸し)

**最終更新**: 2026-04-24 / ashigaru5 (cmd_1443_p10 H13 C13 追加)
**前身**: work/cmd_1442/execution_plan_v3.md §3 Δ5
**採用根拠**: 殿判断 H12 (2026-04-24 18:36) 「いま初めて知った」問題の透明性対策

---

## 0. 本ドキュメントの目的

殿・家老・軍師・足軽の誰もが「どの cron が何をしているか」即座に把握できるようにする単一情報源。
`crontab -l` だけでは目的・所管・停止影響が分からず、運用事故（停止忘れ・死文化放置・ログ不在など）の温床となる。

**原則**: 新規 cron 追加時・停止時・スケジュール変更時は **必ず本 md を同時更新**。スナップショット (`shared_context/crontab.snapshot.txt`) も同時に更新すること。

**整合性検証**: `scripts/nightly_audit.sh` が毎晩 crontab ↔ inventory の drift を検知し、drift 発見時は ntfy 通知する。

---

## 1. 各 entry 必須フィールド

| フィールド | 意味 |
|-----------|------|
| **ID** | `C{NN}` 形式の識別子 (例: C01) |
| **スケジュール** | cron 式 (例: `0 7 * * *`) |
| **コマンド** | 実行コマンドの要約 (スクリプトパス) |
| **目的** | 何のためにあるか (停止判断の根拠) |
| **所管** | 担当エージェント / 変更権限者 |
| **停止影響** | 停止したら何が壊れるか |
| **ログ** | stdout/stderr リダイレクト先 |
| **状態** | `active` / `disabled` (コメントアウト) |
| **備考** | 補足 (依存・リスク・過去事故) |

---

## 2. Active cron 一覧 (crontab -l・有効行のみ)

### C01 — 生成AI技術トレンド日報

| 項目 | 値 |
|------|-----|
| スケジュール | `0 7 * * *` (毎朝 7:00 JST) |
| コマンド | `cd /home/murakami/multi-agent-shogun && bash scripts/genai_daily_report.sh` |
| 目的 | 生成AI技術トレンド日報を自動生成し、殿のスマホに ntfy 通知 |
| 所管 | 家老 (運用) / 将軍 (レビュー) |
| 停止影響 | 日報が届かなくなる。生成AI業界動向の把握遅延。YouTube/ショート制作ネタ源枯渇。 |
| ログ | `logs/genai_daily.log` |
| 状態 | active |
| 備考 | cmd_1162 で Gemini フォールバック削除済 (Claude CLI 単独和訳)。 |

### C02 — Embedding semantic index auto-update

| 項目 | 値 |
|------|-----|
| スケジュール | `0 * * * *` (毎時) |
| コマンド | `python3 scripts/semantic_search.py update` |
| 目的 | `scripts/semantic_search.py` の Gemini Embedding index を git commit 差分に合わせて更新 |
| 所管 | 軍師 (運用) / 足軽全員 (利用者) |
| 停止影響 | semantic_search の検索精度が劣化 (stale index)。新規ファイル/変更が検索ヒットしなくなる。 |
| ログ | `logs/semantic_update.log` |
| 状態 | active |
| 備考 | 失敗は通知されないので `cron_health_check.sh` (C11) が異常検知する。 |

### C03 — dedup_check

| 項目 | 値 |
|------|-----|
| スケジュール | `*/15 * * * *` (15分毎) |
| コマンド | `bash scripts/automation/dedup_check.sh` |
| 目的 | ドズル社切り抜き動画の重複 ID 検知・auto_fetch 同期精度監視 |
| 所管 | 家老 (運用) / 足軽 (対応) |
| 停止影響 | 重複動画の混入に気付かなくなる。YouTube 非公開アップで同一素材を二重アップする恐れ。 |
| ログ | `logs/dedup.log` |
| 状態 | active |
| 備考 | auto_fetch.py (C-disabled-1/2) が手動運用中のため dedup だけ常時稼働。 |

### C04 — YouTube Analytics snapshot

| 項目 | 値 |
|------|-----|
| スケジュール | `57 5 * * *` (毎朝 5:57 JST) |
| コマンド | `venv/bin/python3 scripts/youtube_analytics_snapshot.py` |
| 目的 | YouTube Data+Analytics API から日次スナップショット取得 (登録者/再生時間/トラフィック)・YPP判定用データ収集 |
| 所管 | 軍師 (レポート生成) / 将軍 (殿報告) |
| 停止影響 | チャンネル成長トラッキング停止。YPP達成判定遅延 (登録者2,740/4,786h の進捗が見えなくなる)。 |
| ログ | `projects/dozle_kirinuki/analytics/cron.log` |
| 状態 | active |
| 備考 | 5:57 選定理由は YouTube API quota reset (日本時間 午前) 直後の安定時間帯。 |

### C05 — 夜間矛盾検出 (nightly_audit)

| 項目 | 値 |
|------|-----|
| スケジュール | `2 2 * * *` (毎晩 2:02 JST) |
| コマンド | `bash scripts/nightly_audit.sh` |
| 目的 | カテゴリローテ (STT/動画制作/インフラ/YouTube連携) で軍師に矛盾検出・死文化検知タスクを発令 |
| 所管 | 軍師 (実行) / 家老 (受領・ダッシュボード掲載) |
| 停止影響 | 夜間の自動品質監査が止まる。コード死文化・ドキュメント乖離・cron drift の検知遅延。 |
| ログ | `logs/nightly_audit.log` |
| 状態 | active |
| 備考 | cmd_1443_p09 で crontab ↔ cron_inventory.md 整合チェック前置 (drift→ntfy)。cmd_1443_p02 で `dashboard_lifecycle.sh` (H2 拡張・dashboard 残骸クリーン) を chain 実行。ログは `logs/dashboard_lifecycle.log` に別出力。 |

### C06 — kill_orphan_chrome

| 項目 | 値 |
|------|-----|
| スケジュール | `* * * * *` (毎分) |
| コマンド | `bash scripts/kill_orphan_chrome.sh` |
| 目的 | CDP/Playwright 起動 Chrome の孤児プロセス (親プロセス消失) を自動 kill しメモリリーク防止 |
| 所管 | 家老 (運用) |
| 停止影響 | note-cli / CDP 系タスクの孤児 Chrome がメモリを食い潰し、最終的にマシン不安定化。 |
| ログ | `logs/orphan_chrome_cleanup.log` (スクリプト内ハードコード。cron stdout は discard) |
| 状態 | active |
| 備考 | cron 定義に `>> log 2>&1` なし (スクリプト内で完結)。kill 時のみログ追記されるため、通常は無出力が正常。 |

### C07 — CTA コメント cron

| 項目 | 値 |
|------|-----|
| スケジュール | `5 12 * * *` (毎日 12:05 JST) |
| コマンド | `bash scripts/cta_comment_cron.sh` |
| 目的 | 当日アップロード動画に「チャンネル登録お願いします」系 CTA コメントを自動投稿 |
| 所管 | 家老 (運用) / 将軍 (停止判断) |
| 停止影響 | CTA コメントが自動投稿されなくなる。登録者増加率低下の恐れ。 |
| ログ | `logs/cta_comment.log` |
| 状態 | active |
| 備考 | YouTubeコメント返信禁止ルール (2026-03-31) はアリーリ動画のみ・CTA 自動投稿は対象外。 |

### C08 — MCP experiment

| 項目 | 値 |
|------|-----|
| スケジュール | `0 2 * * *` (毎晩 2:00 JST) |
| コマンド | `bash scripts/mcp_experiment.sh` |
| 目的 | MCP memory server の日次実験・graph growth 計測・claude-mem 同期検証 |
| 所管 | 軍師 (実験監督) / 将軍 (設計変更) |
| 停止影響 | MCP memory の日次検証データが途絶える。memory graph 異常検知の遅延。 |
| ログ | `/tmp/mcp_experiment_cron.log` ⚠️ |
| 状態 | active |
| 備考 | **ログパスが /tmp** で CLAUDE.md「/tmp 禁止」ルール違反。再起動でログ消失。次回メンテ時 `logs/` 配下へ移設推奨 (out of scope for cmd_1443_p09)。 |

### C09 — slim_yaml (全エージェント)

| 項目 | 値 |
|------|-----|
| スケジュール | `0 3 * * *` (毎晩 3:00 JST) |
| コマンド | `bash scripts/slim_yaml.sh {karo,ashigaru1..7,gunshi}` (9 連結) |
| 目的 | 全エージェントの `queue/tasks/{agent}.yaml` を圧縮 (done タスク記録は保持・容量削減) |
| 所管 | 家老 (運用) |
| 停止影響 | task YAML が肥大化し、足軽のコンテキスト消費量が増える。起動時の YAML 読み込みコスト増。 |
| ログ | `logs/slim_yaml_cron.log` |
| 状態 | active |
| 備考 | 9 エージェント分を `&&` 連結。途中 1 件失敗で後続もスキップされる仕様 (drift リスク要観察)。 |

### C10 — プロジェクト全体バックアップ

| 項目 | 値 |
|------|-----|
| スケジュール | `0 */6 * * *` (6 時間毎) |
| コマンド | `cd /home/murakami/multi-agent-shogun && bash scripts/backup_full.sh` |
| 目的 | プロジェクトフォルダを別ドライブ (sdc) へ同期バックアップ (projects/ を含む) |
| 所管 | 家老 (運用) / 将軍 (復旧責任者) |
| 停止影響 | 障害時の復旧ポイント喪失。最悪プロジェクト全滅リスク。 |
| ログ | `logs/backup_full.log` |
| 状態 | active |
| 備考 | `projects/` は git-ignored なので cron バックアップが唯一の保全手段。停止させるな。 |

### C11 — cron health check (新設: cmd_1443_p09)

| 項目 | 値 |
|------|-----|
| スケジュール | `30 * * * *` (毎時 30分) |
| コマンド | `bash scripts/cron_health_check.sh` |
| 目的 | 本インベントリ記載の全 cron ログを tail/grep で検査し、`ERROR`/`FAIL`/`Traceback` を検知したら ntfy 通知 |
| 所管 | 軍師 (監視) / 家老 (対応) |
| 停止影響 | cron の silent failure (動いているフリ) が見過ごされる。透明性喪失。 |
| ログ | `logs/cron_health_check.log` (自身のログは scan 対象から除外・再帰 ntfy 防止) |
| 状態 | active |
| 備考 | 1 回の実行で複数 cron のエラーをまとめて 1 ntfy に集約 (rate limit 配慮)。 |

### C12 — hotfix trend detector (cmd_1443_p05 / H7)

| 項目 | 値 |
|------|-----|
| スケジュール | `0 6 * * 1` (毎週月曜 6:00 JST) |
| コマンド | `bash scripts/hotfix_trend_detector.sh` |
| 目的 | 足軽 report YAML の `hotfix_notes` + claude-mem hotfix 観測をクラスタリングし、3 回以上の類似 hotfix を skill 化候補として検知・ダッシュボード掲載 + ntfy |
| 所管 | 軍師 (解析) / 家老 (skill 化判断) / 将軍 (承認) |
| 停止影響 | 同種の場当たり修正が繰り返されても検知されず、skill 化の機会損失・知見の暗黙知化が進行。 |
| ログ | `logs/hotfix_trend.log` + 状態ファイル `logs/hotfix_trend_state.json` |
| 状態 | active |
| 備考 | cmd_1443_p05 で実装。idempotent (状態ファイルで通知済クラスタを記録)。 |

### C13 — monthly feedback review (cmd_1443_p10 / H13)

| 項目 | 値 |
|------|-----|
| スケジュール | `0 4 1 * *` (毎月1日 4:00 JST) |
| コマンド | `cd /home/murakami/multi-agent-shogun && bash scripts/monthly_feedback_review.sh` |
| 目的 | `memory/feedback_*.md` のうち 90日以上参照ゼロ (git log / queue/reports / claude-mem 全て 0 hit) の stale feedback を検知し、dashboard.md 「🔍 feedback レビュー推奨（月次検知）」に追記 + ntfy 通知 |
| 所管 | 軍師 (検知) / 家老 (確認・棚卸し起票) / 将軍 (削除/更新承認) |
| 停止影響 | stale feedback が陳腐化したまま残り、LLM 判断のノイズ源になる。MEMORY.md スリム化サイクルが途絶える (cmd_1441 D6 Option A の恒常化手段)。 |
| ログ | `logs/monthly_feedback_review.log` |
| 状態 | active |
| 備考 | 状態ファイル `logs/monthly_feedback_review_state.json` で同一 slug の再通知を 30日抑止。dashboard は `<!-- monthly-feedback-review: {slug} -->` マーカーで二重追記防止。cmd_1443_p10 で新設。 |

---

## 3. Disabled cron (コメントアウト行)

動画取得系を手動運用に切り替えた痕跡。将来再開する可能性があるので記録保存。

### D01 — auto_fetch (通常実行)

- **元スケジュール**: `15 18 * * *` (毎日 18:15)
- **無効化理由**: 手動 `/video-pipeline` 運用に切替 (殿判断・ドズル社切り抜き素材の質優先のため自動収集を停止)
- **所管**: 家老 (再開判断)
- **再開方法**: crontab 行の `#` を外し、手動運用と併存しないよう調整

### D02 — auto_fetch --chat-retry

- **元スケジュール**: `30 19 * * *`
- **無効化理由**: D01 と同時無効化 (リトライ専用)
- **所管**: 家老

### D03 — scene_search.py build

- **元スケジュール**: `0 19 * * *`
- **無効化理由**: auto_fetch 停止に伴い index 再構築も不要化
- **所管**: 軍師

### D04 — post_fetch_recommend (18:25)

- **元スケジュール**: `25 18 * * *`
- **無効化理由**: auto_fetch 停止と連動
- **所管**: 家老

### D05 — post_fetch_recommend (19:40)

- **元スケジュール**: `40 19 * * *`
- **無効化理由**: D04 と同時無効化
- **所管**: 家老

---

## 4. 対象外 (out of scope)

### OS 所管 systemd user timer

`systemctl --user list-timers` で見える timer のうち、OS/パッケージ管理系は本インベントリの管理対象外。

| Unit | 用途 | 対応 |
|------|------|------|
| `snap.firmware-updater.firmware-notifier.timer` | snap の firmware 更新通知 | 放置 (OS管理) |
| `launchpadlib-cache-clean.timer` | launchpadlib のキャッシュ掃除 | 放置 (Ubuntu 標準) |

### デーモン (cron ではない常駐)

以下は `cron` ではなく tmux/systemd 常駐の daemon。`logs/inbox_watcher_*.log` 等は監視対象外。

- `inbox_watcher_*.sh` (各エージェント 9 本)
- `advisor_proxy` (logs/advisor_proxy.log)
- `context_watcher`
- `genai_viewer`
- `discord_news_bot`
- `ntfy_listener`

**本インベントリは cron 専用。** daemon は別途 `shared_context/daemon_inventory.md` を起票する場合あり (未起票)。

---

## 5. Quarterly Review 義務 (四半期棚卸し)

**軍師** が以下のサイクルで本インベントリを棚卸しする (死文化検知・責任明確化)。

### レビューサイクル

| 実施月 | 対象 | 起票者 |
|--------|------|--------|
| 1月 (Q1) | 全 entry 再確認 + 前期の silent fail 傾向集計 | 軍師 |
| 4月 (Q2) | 〃 | 軍師 |
| 7月 (Q3) | 〃 | 軍師 |
| 10月 (Q4) | 〃 + 年間総括 (削除/統合候補の提言) | 軍師 |

### レビュー手順

1. `crontab -l > /tmp/crontab_current.txt` で現状取得
2. `diff shared_context/crontab.snapshot.txt /tmp/crontab_current.txt` で前回からの差分確認
3. 本インベントリの各 entry について以下を検査:
   - **目的の妥当性**: 今も必要か? 死文化していないか?
   - **所管の最新性**: 担当エージェントが現組織構成と合っているか?
   - **停止影響の正確性**: 停止した場合の実害が記載通りか (実験停止で検証可能なら軍師が確認)?
   - **ログの健全性**: 直近 90 日で `ERROR`/`FAIL` が急増していないか (C11 集計)?
4. Disabled (D01-D05) entry の再開/削除判断を起票
5. スナップショット更新: `crontab -l > shared_context/crontab.snapshot.txt`
6. レビュー結果を `dashboard.md` に掲載 + inbox_write karo で家老に報告
7. 殿に ntfy 送信 (四半期レビュー完了)

### レビュー未実施検知

`nightly_audit.sh` に将来拡張として、本 md の「最終更新」日から 100日以上経過時に warning ntfy を送る機能を追加予定 (future scope)。

---

## 6. 変更履歴

| 日付 | 変更者 | 内容 |
|------|--------|------|
| 2026-04-24 | ashigaru6 (cmd_1443_p09) | 新設。C01-C10 棚卸し + C11 新規 (cron_health_check) + D01-D05 記録 |
| 2026-04-24 | ashigaru5 (cmd_1443_p10) | C13 新規 (monthly feedback review / H13)。crontab snapshot 同時更新。 |
