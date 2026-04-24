# 足軽3号アイデア出し（ファイル蓄積整理 / c カテゴリ）

cmd_1441 Phase A 足軽3号担当分。queue/handoff・queue/precompact・work/cmd_*・exports・YAML肥大 の蓄積整理。
作成: 2026-04-24 13:05 / ashigaru3

---

## 現状（計測値・事実ベース）

| 対象 | 規模 | 備考 |
|------|------|------|
| `queue/handoff/*.md` | 300 files, 3月6日〜4月14日 | 発行元: karo=129, shogun=112, gunshi=29, ashigaru計=31。単一最大 842KB。archive 無し |
| `queue/handoff/transcripts/*.jsonl` | 246 files, **1.8GB** | 最大 73MB (karo_20260316-0857.jsonl)、precompact_hook.sh が書き込むのみ・読み手不在 |
| `queue/precompact/*.yaml` | 8 files, **44KB** | 8エージェント分の状態スナップショット。問題なし |
| `queue/reports/` top-level | 425 files, 38MB (主にYAML) | archive/ は 34 件（ほぼPNG）でYAMLアーカイブルール未整備 |
| `queue/reports/archive/` | 34 files | PNG・txt中心。YAMLローテーション未実施 |
| `queue/tasks/*.yaml` | gunshi=2917行 / ashigaru1=2310行 / ashigaru2=1796行 / ashigaru3=1053行 | CLAUDE.md記載「100件超で archive退避（手動）」だが手動退避実績ゼロ |
| `queue/inbox/` | 0 バイト | tmpfs想定？空。問題なし |
| `work/cmd_1424/` | **9.4GB**（work全体の94%） | segBossAB.mp4=9.3GB + segMeeting.mp4=136MB。cmd_1424 は done 確定・YouTube upload完了 |
| `work/cmd_*` 総計 | 28ディレクトリ (1049〜1441) | 4/9〜4/24に分散。ほぼ小容量だが retention ポリシー無し |
| `work/sasuu_articles/` | 292MB, 137ファイル | note記事関連のPDF群。用途不明瞭・既読? |
| `work/dingtalk_qc/` | 29MB | DingTalk QC案件中間生成物 |
| `work/` 直下散乱 | URL2.txt, URL3.txt, cmd1243_images.json, api_gen_p*_* 等 | 一時ファイルがroot直下放置 |
| `exports/` | 0 バイト | 未使用 |
| `dashboard_archive/` | 2 files, 最終 2026-03-05 | **50日間更新停止** → `dashboard_rotate.sh` 実行されず |
| `queue/cmd_archive/` | 2 files, 最終 2026-03-05 | **50日間更新停止** → `cmd_rotate.sh` 実行されず |
| `scripts/archive/` | 空ディレクトリ | 2026-04-04 作成・未使用 |
| ディスク全体 | 961G中796G使用=**88%** | 残 116G。shogun_horizontal.md 3-A でも「緊急高」指定 |

**既存ローテスクリプト**:
- `scripts/cmd_rotate.sh` — shogun_to_karo.yaml用（500行/30KB閾値）/ 実行停止中
- `scripts/dashboard_rotate.sh` — dashboard.md用（200行/10KB閾値）/ 実行停止中
- `scripts/slim_yaml.sh` + `slim_yaml.py` — タスクYAML読込前圧縮（退避ではない）
- crontab には genai_daily_report / semantic_update のみ・ローテ系なし

## やれてないこと（gap）

1. **handoff/transcripts の retention ルール皆無** — `precompact_hook.sh` が 1セッション分の jsonl を丸ごとコピーするのみで消される日が来ない。1.8GB中 3月分が 214/300 と古い
2. **queue/reports/ YAML の自動アーカイブ** — 425件のうち cmd_300番台以前（3月）の report も top-level に残存
3. **work/cmd_* の cmd完了後クリーンアップ** — .gitignore で動画本体は追跡外だが、ローカルに無限蓄積。9.3GB の segBossAB.mp4 はcmd完了後も残存（disk 88% の直接原因）
4. **queue/tasks/*.yaml 手動archive の実施未実施** — 手動ルールだけ存在し誰も運用していない。gunshi 2917行は読み込み毎に token 膨張
5. **既存 cmd_rotate/dashboard_rotate が呼ばれていない** — スクリプトはあるが trigger（cron/hook）未接続。50日停止は運用バグ
6. **scripts/archive/ 空ディレクトリの意図不明** — 4/4 作成後未使用
7. **disk 使用量 watchdog 不在** — 88%到達まで気付かれなかった（cmd_1441発令で初めて明示）
8. **handoff .md の誰が何件ルール不在** — karo 129件・shogun 112件は compaction 回数そのもの。最終7日ぶんだけ残せば十分でも運用ルール無し

## アイデア（提案）

### C-1. `scripts/handoff_transcripts_prune.sh` 新規 — 最大レバー候補（1.8GB削減）

- **対象**: `queue/handoff/transcripts/*.jsonl`（246 files / 1.8GB）
- **方針**: 14日超の .jsonl を gzip→ 30日超を削除。.md は /rehydrate が読むので別系統
- **実装**: 1スクリプト + crontab 週1回 実行
- **根拠**: rehydrate コマンド（`.claude/commands/rehydrate.md`）と handoff.md を grep しても jsonl を読み出す consumer は不在。書き捨てログなので圧縮・削除安全
- **リスク**: 本タスクで `grep -rln "handoff/transcripts" ~/.claude-mem/` 実施 → ヒットは claude-mem がログ収集した自発話のみで、jsonl を直接 open/parse する処理は無し。cmd_1440 Phase1 着地直後にも依存なし確認済
- **前提**: 削除前 1 世代は gzip 保持（念のため30日）
- **なぜ今**: disk 88%・最大単ファイル 73MB、3月分 214件が古い

### C-2. `scripts/work_cmd_cleanup.sh` 新規 — cmd_1424 の 9.3GB 即回収

- **対象**: `work/cmd_1424/segBossAB.mp4`(9.3GB) + `segMeeting.mp4`(136MB)。完了済cmd全般に一般化
- **方針**: `queue/shogun_to_karo.yaml` の status:done かつ 14日経過の cmd_NNNN について、work/cmd_NNNN/ 配下の動画/音声系(>100MB)をリストアップ → 殿確認 → 削除
- **実装**: ffprobe で動画判定 → du -sh で上位ピックアップ → 削除候補YAMLを `work/cmd_1441/cleanup_candidates.yaml` に出力
- **根拠**: cmd_1424 の report（`queue/reports/ashigaru1_report_subtask_1424a2.yaml` / `gunshi_report_qc_1424a2.yaml`）ともに status:done + YouTube upload完了。中間成果物は .gitignore 対象と cmd 定義に明記（queue/shogun_to_karo.yaml line 4057-4058）
- **リスク**: 再編集時に再 DL が必要（原稿動画を残すなら intermediate のみ削除）
- **前提**: 「完了cmdの中間動画削除ポリシー」を殿合意。cmd_1424 は特に単独で 9.3GB 解放・disk 88→79% 想定
- **なぜ今**: disk 88% の直接原因。Day6 4視点MIX 控えで更に200GB+必要

### C-3. `scripts/handoff_md_rotate.sh` 新規 — 古い handoff .md を月別アーカイブ

- **対象**: `queue/handoff/*.md`（300 files）
- **方針**: 30日超の .md を `queue/handoff/archive/YYYY-MM/` へ `git mv` し gzip 化。最新30日は即アクセス可
- **実装**: `scripts/dashboard_rotate.sh` を雛形。閾値=100 file or 30 日
- **根拠**: /rehydrate は「sort | tail -1」で最新のみ読む（`.claude/commands/rehydrate.md` step 2）。古い .md はgzipでも動作不変
- **リスク**: ashigaru/gunshi の古い handoff を読み返す場面は現状皆無。削減可
- **前提**: archive 下は git lfs 化 or ignore（3月分 214 files × 平均40KB = 8.5MB程度なので git直置き可）
- **なぜ今**: karo 129件 / shogun 112件は compaction 履歴そのもの・不要不急

### C-4. `scripts/reports_yaml_rotate.sh` 新規 — 完了 cmd の YAML を月別アーカイブ

- **対象**: `queue/reports/*_report_*.yaml`（425件）
- **方針**: 親 cmd が status:done かつ 14日経過した report を `queue/reports/archive/YYYY-MM/` へ移動
- **実装**: ファイル名から parent_cmd を抽出 → shogun_to_karo.yaml 参照 → done確認 → 退避
- **根拠**: 家老・軍師の retrospective 参照は直近（qc_template 参照）。3月分 200件余は実運用読み込みゼロ想定
- **リスク**: acceptance_criteria 逆引きで archive 参照が必要 → archive/ は git追跡継続すれば find で見つかる
- **前提**: 現行 `queue/reports/archive/` (34 files, PNG中心) は互換維持のためサブディレクトリ下に再編
- **なぜ今**: top-level 425件はエージェント glob 探索時のノイズ源

### C-5. `scripts/tasks_yaml_archive.sh` 新規 — CLAUDE.md記載の手動ルール自動化

- **対象**: `queue/tasks/{agent}.yaml`（gunshi=2917行・ashigaru1=2310行 等）
- **方針**: リスト要素数 > 100 のファイルは、古い status:done タスクを `queue/tasks/archive/{agent}_{YYYY-MM}.yaml` へ切り出し
- **実装**: Python/PyYAML で `tasks:` リストを分割、親ファイルには最新 50 タスク + status:assigned を残す
- **根拠**: CLAUDE.md「100件超えたら queue/tasks/archive/ に古いタスクを退避（手動）」が全員未実施
- **リスク**: 履歴参照時は archive/ を grep 追加必要（slim_yaml の読取先に archive を含めるなら影響ゼロ）
- **前提**: slim_yaml.sh の読取範囲ルール更新（optional）
- **なぜ今**: タスクYAML読込毎に 2917行 / ~35KB を消費 → token 節約（ashigaru.md step 1.5 が slim_yaml を呼ぶ根拠）

### C-6. `scripts/disk_watchdog.sh` 新規 + crontab接続

- **対象**: ルートFS（現状 88% / 116G残）
- **方針**: df 閾値超過（80%=warning / 90%=critical）で ntfy通知 + shogun_to_karo.yaml に自動起票
- **実装**: 10分ごと df → 閾値超なら `bash scripts/ntfy.sh` + dashboard.md 🚨要対応 追記（家老権限）
- **根拠**: 今回 88% まで気付かず cmd_1441 で初明示。passive 観測のみでは再発
- **リスク**: 偽陽性で通知疲れ → 閾値を段階制にすれば緩和
- **前提**: 殿通知は家老経由（家老が dashboard 追記 → ntfy）
- **なぜ今**: Day6 4視点MIX で数十〜200GB+ 追加必要見込み

### C-7. 既存 `cmd_rotate.sh` / `dashboard_rotate.sh` を precompact_hook で自動起動

- **対象**: shogun_to_karo.yaml / dashboard.md
- **方針**: `scripts/precompact_hook.sh` 末尾で閾値チェック → 閾値超なら `cmd_rotate.sh` / `dashboard_rotate.sh` 呼び出し
- **実装**: shogun/karo のcompaction時（precompact event）にのみ実行（他エージェントは呼ばない）
- **根拠**: スクリプト実装済みだが 50日間 trigger 未接続。dashboard_archive/ 最終 3/5, cmd_archive/ 最終 3/5
- **リスク**: compaction中に重い処理を追加 → rotate は軽量（既に閾値チェック済）
- **前提**: precompact_hook.sh の失敗は silent（`|| true`）で安全
- **なぜ今**: 既存資産の死蔵解消・実装コスト低

### C-8. `scripts/archive/` 空ディレクトリの用途明示 or 削除

- **対象**: `scripts/archive/`（空・2026-04-04 作成）
- **方針**: README.md 配置 or `.gitkeep` + 用途定義（例: 退役したスクリプトの退避先） or 削除
- **根拠**: 意図不明のディレクトリは「新規スクリプトを置くな」判断を誤らせる
- **リスク**: ほぼなし
- **前提**: git log で作成意図確認
- **なぜ今**: 軽微だが整理対象の棚卸し一環

### C-9. `work/` 直下散乱ファイルの `work/_tmp/` 集約ルール

- **対象**: `work/URL2.txt`, `URL3.txt`, `cmd1243_images.json`, `api_gen_p5_*`, `api_gen_p7_*` など top-level のオーファン
- **方針**: cmd関連は `work/cmd_NNNN/` へ・一時は `work/_tmp/` へ必ず収容するルール明文化（CLAUDE.md "ファイル配置ルール" 表に追記）
- **実装**: ルール追加のみ。既存散乱は棚卸しで個別判断
- **根拠**: 将来のフリーズ防止。disk watchdog（C-6）とセット運用で発見遅延ゼロ化
- **リスク**: なし（ルールのみ）
- **前提**: 殿承認
- **なぜ今**: 整理の一般ルール不在で再発不可避

### C-10. 統合運用ドキュメント `shared_context/disk_retention_policy.md`

- **対象**: 上記 C-1〜C-9 を一枚に集約
- **方針**: どのディレクトリがどの age で何処へ動くかの retention 表。今後の agent が glob 探索時に迷わないこと
- **実装**: テーブル1枚 + 各スクリプトへのリンク
- **根拠**: 個別script実装でも全体像不明では「走ってるのか」判定不能（現行 rotate 2系統が停止した原因と同じ）
- **リスク**: 陳腐化 → rotate スクリプト側にコメントで同期必須を明記
- **前提**: C-1〜C-7 スクリプト雛形決定後
- **なぜ今**: Phase B統合で軍師が横断アイデア集約する際のベース資料

---

## 優先度サマリ（Phase B軍師統合用ヒント）

| 順位 | 提案 | 期待削減 / 効果 | 実装工数 | 先行依存 |
|------|------|-----------------|----------|----------|
| 1位 | **C-2 work/cmd_1424 回収** | **9.3GB / disk 88→79%** 即時 | 30分 | 殿削除承認のみ |
| 2位 | **C-1 transcripts prune** | **1.8GB** | 1-2h | claude-mem 非依存確認 |
| 3位 | **C-6 disk watchdog** | 再発防止 | 1h | ntfy.sh 既存利用 |
| 4位 | C-7 既存rotate trigger接続 | token節約 + 既存資産活用 | 30分 | precompact_hook 変更 |
| 5位 | C-5 tasks_yaml_archive | slim_yaml コスト低減 | 2h | CLAUDE.md更新 |
| 6位 | C-4 reports_yaml_rotate | glob ノイズ削減 | 2h | - |
| 7位 | C-3 handoff_md_rotate | handoff/ 簡素化 | 1.5h | - |
| 8-10位 | C-8 / C-9 / C-10 | 運用品質 | 合計2h | 上記完了後 |

---

## 実行スコープ自省（本タスクの成果）

本タスクは **アイデア出し**（task_id: subtask_1441c, Phase A）。削除・実装は行わない。acceptance_criteria は md作成 + git commit のみ。
C-2（cmd_1424 9.3GB回収）は効果特大だが、Phase B統合 → 殿承認 → 実行タスク発令 のフローで処理すべき。本 md は提案の根拠と優先度付けに留める。
