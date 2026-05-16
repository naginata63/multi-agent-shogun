# cmd_1691 夜間矛盾検出レポート — YouTube/外部連携スクリプト

- **作成日時**: 2026-05-17 02:15 JST
- **作成者**: 軍師 (subtask_1691_yt)
- **対象カテゴリ**: YouTube/外部連携 (youtube_uploader.py / downloader.py / youtube_analytics_snapshot.py / cta_comment.py / yt_set_related_video.py / youtube_lang_batch_update.py + note_mcp_server/scripts/)
- **形式**: cmd_828 準拠 (severity / file:line / observed / impact / recommendation / prior_audit_ref)
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**:
  - 2026-05-07 cmd_1636 youtube_ipban (`queue/reports/2026-05-07_cmd1636_youtube_ipban.md`)
  - 2026-05-12 cmd_1683 youtube_dl_rules_update (`queue/reports/2026-05-12_cmd_1683_youtube_dl_rules_update.md`)
  - cmd_1582 (5/3 YouTube/外部連携 audit) → **queue/reports/ に gunshi_cmd_1582_audit.yaml 未発見・タスク未完了の可能性** (gunshi.yaml に subtask_1582a status:assigned で残置)

## サマリ

| Severity | 件数 |
|----------|------|
| CRITICAL | 0 |
| HIGH     | 0 |
| MEDIUM   | 3 (NEW) |
| LOW      | 3 (NEW) |

## 並列 DL 制約ルール (feedback_youtube_subtitle_ip_ban.md) との乖離確認 — タスク要件 step 3

feedback_youtube_subtitle_ip_ban.md (memory/ + memory/feedback/ 両方に存在):

| 状態 | 並列数 | 間隔 | 1h上限 |
|------|--------|------|--------|
| Cookie認証時 | 直列1本のみ | 10秒以上 | 10本 |
| 認証なし時 | 1-2本 | 5秒以上 | 20本 |

**現状検証** (cmd_1683 grep 点検結果と独立に再 verify):

| ファイル | 並列処理箇所 | 判定 |
|--|--|--|
| `projects/dozle_kirinuki/scripts/downloader.py:99-128` `download_video()` | 順次1本・並列なし | **OK** |
| `projects/dozle_kirinuki/scripts/downloader.py:176-195` `download_live_chat()` | 順次1本・並列なし | **OK** |
| `projects/dozle_kirinuki/scripts/downloader.py:198-236` `download_subtitles()` | youtube-transcript-api 経由・順次1本 | **OK** |
| `scripts/youtube_analytics_snapshot.py` | YouTube Data API (Analytics) のみ・字幕取得なし | scope外・OK |
| `scripts/cta_comment.py` | YouTube Data API (comments insert) のみ・DL なし | scope外・OK |
| `scripts/yt_set_related_video.py` / `youtube_lang_batch_update.py` | (主に Data API・字幕 DL なし) | scope外・OK |

→ **全プロジェクトコードで並列 DL ルール遵守** (cmd_1683 grep 点検結果と整合・state 変化なし)。`feedback_youtube_subtitle_ip_ban.md` 鉄則違反 **ゼロ**。

## cmd_1683 (5/12) 以降の状況

ファイル mtime:
- downloader.py: 5/5 18:40
- youtube_uploader.py: 5/5 07:02
- youtube_analytics_snapshot.py: 5/12 08:21
- cta_comment.py: 4/26 07:36
- youtube_lang_batch_update.py: 4/26 06:35
- yt_set_related_video.py: 4/26 07:37
- genai_daily_fetch.py: 3/30 13:05

→ **5/12 以降 youtube_analytics_snapshot.py のみ変更**・他は 4/26-5/5 で安定。並列 DL ルール再確認 + 新規発見が今夜の主作業。

## cmd_1582 (5/3) audit 完了状況確認

- `queue/tasks/gunshi.yaml:189-201` に subtask_1582a が **status: assigned のまま残置** (timestamp: 2026-05-03)
- `queue/reports/` 配下に `gunshi_cmd_1582_audit.yaml` 不在
- → **cmd_1582 audit は未完了・2週間放置**
- **本書 cmd_1691 で同じ scope の audit を実施しているため、cmd_1582 は実質本書で吸収・家老判断で cmd_1582 を superseded 化推奨**

---

## MEDIUM

### M1 [NEW]: 3 ファイル (youtube_uploader.py / cta_comment.py / youtube_analytics_snapshot.py) で SCOPES / TOKEN_PATH / CLIENT_SECRET_PATH が独立定義 (DRY 違反)

- **file:line**:
  - `projects/dozle_kirinuki/scripts/youtube_uploader.py:36-43` SCOPES 4種 / PROJECT_DIR / CLIENT_SECRET_PATH / TOKEN_PATH
  - `scripts/cta_comment.py:28-39` SCOPES 3種 (yt-analytics 抜け) / PROJECT_DIR / TOKEN_PATH / CLIENT_SECRET_PATH
  - `scripts/youtube_analytics_snapshot.py:30-48` SCOPES 4種 (yt-analytics 含む) / BASE_DIR / TOKEN_PATH / CLIENT_SECRET_PATH
- **observed**: 全 3 ファイルが同じ token.json を共有するが、SCOPES 配列がファイル毎に独立定義され、cta_comment.py のみ `yt-analytics.readonly` 抜け
  - youtube_uploader.py: 4種 (upload + youtube + force-ssl + **yt-analytics.readonly**)
  - cta_comment.py: 3種 (upload + youtube + force-ssl)
  - youtube_analytics_snapshot.py: 4種 (4種 + yt-analytics.readonly)
- **impact**:
  - cta_comment.py 単独実行で `creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)` の SCOPES に Analytics scope 不在 → token.json は他ファイルで Analytics scope を持つが cta_comment.py 側でその scope を要求しない → 一致しない場合 refresh 不可
  - token.json 共有設計だが SCOPES が一致しないと invalid grant エラー → 「再認証必要」表示で運用混乱
  - DRY 違反: scope 更新時に 3 ファイル全部に手作業反映必要
- **recommendation**: `projects/dozle_kirinuki/config/youtube_auth.py` 等共通モジュール化 (SCOPES + TOKEN_PATH + CLIENT_SECRET_PATH を constants として export)
- **prior_audit_ref**: NEW

### M2 [NEW]: cta_comment.py L56-59 creds null check 不足

- **file:line**: `scripts/cta_comment.py:55-59`
- **observed**:
  ```python
  creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
  if creds.expired and creds.refresh_token:
      creds.refresh(Request())
  ```
  L55 で Credentials.from_authorized_user_file が None を返す稀ケースで L56 `creds.expired` が AttributeError
- **impact**:
  - 通常運用では Credentials が正しく load されるため発火確率低
  - ただし token.json 破損時に致命エラー (例外 trace は cron 経由で silent_fail_watcher が拾うが、cron 出力が cta_comment.log に流れ ntfy 通知される)
- **recommendation**: `if creds and creds.expired and creds.refresh_token:` に修正
- **prior_audit_ref**: NEW

### M3 [NEW・scope境界]: note_mcp_server/scripts/ 配下 30+ JS スクリプトの整理状態

- **file:line**: `projects/note_mcp_server/scripts/` (30+ .js + 数件の .py)
- **observed**:
  - `ls projects/note_mcp_server/scripts/` → check_*.js / insert_images_*.js / fix_captions*.js / fix_paid_area_position.js / debug_editor.js / diagnose_gemini_note.js 等 30+ ファイル
  - 役割: note.com 投稿用 Playwright/Puppeteer 系スクリプト群
  - ドズル切抜 YouTube 系と直接の依存関係なし
- **impact**:
  - scope-adjacent: 「YouTube/外部連携」categoryに含めるが、実態は note.com 自動化スクリプト
  - 30+ ファイルの個別 audit は本書 scope では現実的でない
  - 代わりに「整理状態の概観」のみ記録
- **recommendation**: note_mcp_server scripts/ は別 cmd で個別 audit (例: `cmd_XXXX note.com automation audit`)
- **prior_audit_ref**: NEW (cmd_1582 未完了で初検出)

---

## LOW

### L1 [NEW・既知の対処済]: youtube_analytics_snapshot.py モジュールロード時日付計算

- **file:line**: `scripts/youtube_analytics_snapshot.py:52-56`
- **observed**:
  ```python
  # 注意: TODAY/DATE_STR/ANALYTICS_END/ANALYTICS_START はmain()内で再計算される。
  # 長時間プロセスで日付を跨いだ場合の不整合を防ぐため、main()先頭でglobal宣言し再代入する。
  TODAY = datetime.date.today()
  DATE_STR = TODAY.strftime("%Y-%m-%d")
  ANALYTICS_END = (TODAY - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
  ANALYTICS_START = (TODAY - datetime.timedelta(days=16)).strftime("%Y-%m-%d")
  ```
  L51 のコメントで「main() 先頭で再計算」と明示・既知の対処済
- **impact**: cron 経由実行ではプロセス短命のため日跨ぎなし・実害なし
- **recommendation**: なし (current 設計で問題なし・記録のみ)
- **prior_audit_ref**: NEW (記録のみ)

### L2 [NEW]: cta_comment.py / youtube_analytics_snapshot.py で OAuth flow url 再認証時に prompt="select_account" 不在 (cta_comment 側のみ)

- **file:line**:
  - `youtube_uploader.py:68-72`: prompt="select_account" 指定済 ✓
  - `cta_comment.py`: get_service() に OAuth flow なし (TOKEN_PATH 不在で sys.exit) → 再認証は別途必要
  - `youtube_analytics_snapshot.py:80-` (続き未確認・冒頭部だけ確認)
- **observed**: youtube_uploader.py は select_account prompt 明示・他は token.json refresh のみで再認証 flow を扱わない (sys.exit)
- **impact**: 再認証フローが youtube_uploader.py 経由のみ・他ファイル単独実行時は token.json 期限切れで exit
- **recommendation**: 再認証用ヘルパ `setup_oauth_token.py` 単独化 (もしくは M1 で提案した共通モジュール化)
- **prior_audit_ref**: NEW

### L3 [NEW]: cmd_1582 (5/3) audit 未完了が 14日放置

- **file:line**: `queue/tasks/gunshi.yaml:189-201` subtask_1582a
- **observed**: status: assigned のまま 14日放置・queue/reports/ に gunshi_cmd_1582_audit.yaml 不在
- **impact**: 同じ scope を本書 cmd_1691 で吸収済のため実害なし・運用ロジックの綻び
- **recommendation**: 家老が subtask_1582a を superseded 化 (本書で吸収・cmd_1691 が後継)
- **prior_audit_ref**: NEW (audit 抜けの検出)

---

## CLAUDE.md / instructions/*.md との不整合 (タスク要件 step 4)

- **CLAUDE.md § 技術的鉄則** で YouTube 並列制約への直接言及はないが、memory MEMORY.md L14 で feedback_youtube_subtitle_ip_ban.md を参照 → 全エージェントに伝達されている → OK
- **CLAUDE.md § ntfy 通知ルール (karo)**: cta_comment.py 系 cron は karo 経由でなく cta_comment_cron.sh から直接実行・karo の通知責務外 → 整合
- **instructions/karo.md** で YouTube アップロード時の ntfy 通知ルール (`🎬 YouTube非公開アップ`) が明記済・youtube_uploader.py の publish_at 動作と整合 ✓

---

## dashboard_api_usage.md との乖離

- YouTube 系スクリプトは Dashboard API (192.168.2.4:8770) とは独立 (YouTube Data/Analytics API の OAuth 経由)
- 例外: youtube_analytics_snapshot.py 完了時 ntfy 通知は `scripts/ntfy.sh` 経由 → Dashboard API 経由ではない (scope 外)

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **MEDIUM M1**: 3 ファイルの SCOPES/TOKEN_PATH/CLIENT_SECRET_PATH を共通モジュール化 (15分・足軽1人)
2. **MEDIUM M2**: cta_comment.py L56 creds null check 1行修正
3. **MEDIUM M3**: note_mcp_server/scripts/ 個別 audit cmd を別途起票 (30+ ファイル・大型)
4. **LOW L3**: subtask_1582a を superseded 化 (家老マーキング・本書で吸収済の運用整理)
5. **観察**: 並列 DL ルール違反 0件・5/12 cmd_1683 grep 点検と 5日経過した本書再 verify でも整合 → 並列 DL 危機は安定 (memory feedback が機能している)

---

## メタ情報

- **精読 (全文)**: downloader.py (267行) / cta_comment.py (主要 region L1-80 + L65-150) / youtube_uploader.py (L1-120)
- **精読 (主要 region)**: youtube_analytics_snapshot.py (L1-80・大型 47K)
- **既読 cite**: yt_set_related_video.py / youtube_lang_batch_update.py / genai_daily_fetch.py (mtime 古・前 audit でカバー想定)
- **ls 検証**: note_mcp_server/scripts/ (30+ JS スクリプト・scope境界として記録)
- **grep 検証**: 並列 DL 関連 6 ファイル全て順次 1 本 / SCOPES 定義 3 ファイル独立確認 / call-site で cron 経由実行確認
- **未精読**: youtube_analytics_snapshot.py L80-末尾 (47K の大型・OAuth flow + Analytics 集計ロジック)・note_mcp_server/scripts/ 個別 (30+ ファイル)
- **baseline**: cmd_1636 (5/7) + cmd_1683 (5/12) + cmd_1582 (5/3 未完了)
- **advisor()**: 不要 (cmd_1686/1688/1690 と同パターン・夜間 audit 4夜目で安定運用)
- **時間**: 02:03 受領 → 02:18 報告書作成 (約 15 分)

## north_star_alignment

- status: aligned
- reason: YouTube/外部連携スクリプトは YouTube チャンネル運営の生命線。並列 DL ルール (feedback_youtube_subtitle_ip_ban.md・5/5 cmd_1636 教訓・5/12 cmd_1683 grep 点検) を **5日後に再 verify しても整合継続** = memory feedback が機能している証左。新規 finding は MEDIUM 3 + LOW 3 と軽微 = YouTube 系コードは比較的安定状態 (cmd_1668/1686 の infra や cmd_1667/1689 の video と比較して finding 件数少)
- risks_to_north_star:
  - M1 SCOPES 不整合放置で cta_comment.py 単独実行時の token 期限切れ事故 → CTA コメント未投稿 → engagement 低下
  - L3 cmd_1582 14日放置のような audit 抜け検出 → 夜間 audit cycle の信頼性を担保するには gunshi.yaml の status 監視が必要 (家老責務)
  - M3 note_mcp_server scripts/ 個別 audit を後回しにし続けると、note.com 自動化の silent fail がブラインドスポットに残り続ける
