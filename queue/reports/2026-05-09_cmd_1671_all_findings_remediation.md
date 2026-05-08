# cmd_1671 全 findings 対処結果レポート

**作成者**: karo  
**作成日時**: 2026-05-09 JST  
**親cmd**: cmd_1671  
**ステータス**: 🔄 作業中 (サブタスク進行中)  

---

## サマリ

| 処理区分 | 件数 |
|---------|------|
| (a) 即修復 (subtask 割当済) | 29 |
| (b) 別cmd 起票 (1671完了後) | 3 |
| (c) defer 判断 (設計上意図的・低優先) | 12 |
| (d) 殿許諾待ち | 5 |
| **合計** | **49** |

---

## 全 findings 処理結果表

### インフラ系 (cmd_1668) — 19件

| ID | Severity | 概要 | 処理 | 担当 | 理由/備考 |
|----|----------|------|------|------|-----------|
| C1 | CRITICAL | SQLite inbox_messages.type CHECK 制約に error_report/nightly_audit/ntfy_received 欠落 | (a) | ashigaru4 | init_schema() DDL修正 → server.py restart必要 |
| C2 | CRITICAL | precompact_hook.sh の dashboard.md パスが queue/ 配下で存在しない | (a) | ashigaru2 | DASHBOARD_FILE を project root に修正 |
| C3 | CRITICAL | inbox_watcher.sh SQLite-only mark-read による YAML 残置 | (a) | ashigaru1 | SQLite UPDATE後にYAML同時更新追加 |
| C4 | CRITICAL | inbox_watcher.sh normal_count SQLite/YAML 経路で非対称 | (a) | ashigaru1 | C3と同ファイル・同タスクで修正 |
| H1 | HIGH | cron_health_check.sh TARGETS に C12/C13/C15 が未登録 | (a) | ashigaru2 | TARGETS配列に3件追加 |
| H2 | HIGH | ntfy.sh IP 置換 2行重複 | (a) | ashigaru2 | 重複行削除 (192.168.2.7 置換必要性は別途コメントで確認) |
| H3 | HIGH | stop_hook_inbox.sh STOP_HOOK_ACTIVE=True 経路で LAST_MSG 完了通知が二重発火 | (a) | ashigaru2 | unread>0 の fall-through に LAST_MSG 解析skip ガード追加 |
| H4 | HIGH | stop_hook と inbox_watcher mark-read 経路の乖離 | (c) | — | C3/C4 修正で根本原因解消。独立修正不要 |
| H5 | HIGH | fix_panes.sh フォールバックモデルが settings.yaml と乖離 | (a) | ashigaru2 | フォールバック分岐を settings.yaml 準拠に修正 |
| M1 | MEDIUM | ntfy.sh `_update_cmd_done` が blocked/assigned 状態を強制 done 化 | (a) | ashigaru2 | トリガー条件をAPI経由 cmd 完了通知限定に厳格化 |
| M2 | MEDIUM | ntfy.sh `_archive_old_done_cmds` が毎呼出で実行される | (b) | — | 性能最適化 cmd として1671完了後起票予定 |
| M3 | MEDIUM | dashboard_lifecycle.sh コメントと実コードの乖離 | (a) | ashigaru2 | コメントを実コード (生存中) に合わせ修正 |
| M4 | MEDIUM | monitor.sh / context_watcher.sh の起動が手動のみ | (b) | — | cron/supervisor 登録 cmd として1671完了後起票予定 |
| M5 | MEDIUM | inbox_write.sh `_update_task_done` fallback grep で別タスクを done 化する可能性 | (a) | ashigaru7 | fallback grep を削除し cmd_id 必須化 |
| M6 | MEDIUM | ntfy_listener.sh emoji 集合が閉集合 (将来の絵文字変更で沈黙リスク) | (c) | — | 殿の emoji 管理方針が未確定。別途 emoji 一元管理 cmd として整理 |
| L1 | LOW | inbox_watcher.sh Phase flag 群 (ASW_DISABLE_ESCALATION 等) が未参照 | (a) | ashigaru1 | 未参照フラグ削除 (C3/C4 同タスク内で対処) |
| L2 | LOW | inbox_watcher.sh Codex 起動時 idle flag 未作成 | (a) | ashigaru1 | Claude と同等の idle flag 作成ロジック追加 |
| L3 | LOW | ntfy_listener.sh `SINCE_TS` 再接続ごとリセットで切断中メッセージを取りこぼす | (a) | ashigaru7 | 再接続前の SINCE_TS を保持する修正 |
| L4 | LOW | start_ashigaru_glm.sh の advisor_proxy 依存が暗黙 | (c) | — | GLM は現在休眠中。復活時に proxy ヘルスチェック追加 cmd 起票 |

### 動画系 (cmd_1667) — 30件

| ID | Severity | 概要 | 処理 | 担当 | 理由/備考 |
|----|----------|------|------|------|-----------|
| C001 | CRITICAL | WhisperX 残存 (main.py --diarize/argparse/経路) | (a) | ashigaru3 | STT=AssemblyAI 鉄則違反・3次連続検出。argparse+経路を完全削除 |
| C002 | CRITICAL | vertical_convert.py argparse 4引数欠落 (secondary_speaker等) | (a) | ashigaru5→3 | vertical_convert.py argparse 追加 (ashigaru5) + main.py 呼出箇所 (ashigaru3, blocked_by ashigaru5) |
| H001 | HIGH | vertical_convert.py atempo 範囲外 (speed 0.3/2.5 で ffmpeg エラー) | (a) | ashigaru5 | argparse type=float に range validator 追加 |
| H002 | HIGH | main.py 1080p 再DL 閾値が 480p を毎回再DL | (a) | ashigaru3 | 閾値を 360 以下に修正 (コメントと整合) |
| H003 | HIGH | Root.tsx FULL_SEC=4795 等 1動画専用ハードコード | (d) | — | remotion-project/は殿の personal workspace。設計変更は殿判断が必要 |
| H004 | HIGH | shorts mode vertical_convert 呼出で 4 override 引数未渡し | (a) | ashigaru3 | main.py:1366-1381 に 4引数追加 (blocked_by ashigaru5 C002完了) |
| H005 | HIGH | main.py importlib 多用 (動的ロード地獄) | (b) | — | 大規模リファクタ。1671完了後に別 cmd 起票予定 |
| H006 | HIGH | make_expression_shorts.py duration int 化でフレーム精度0.03sずれ | (a) | ashigaru6 | int() → float() に修正 |
| V_H007 | HIGH | remotion-project/public/bg_full.mp4 不在 → DozFull render 不能 | (d) | — | remotion-project/は殿の personal workspace。bg_full.mp4 配置は殿判断 |
| V_H007b | HIGH | remotion-project/ 運用ドキュメント不在 | (d) | — | 殿の personal workspace。ドキュメント追記は殿 + 家老で対応可だが殿確認先行 |
| M001 | MEDIUM | shorts mode 2段階シーク (意図的設計だがMEMORY未追記) | (c) | — | 意図的設計。MEMORY ffmpeg_ss_after_i.md に例外追記のみ (家老が非実装で対処可) |
| M002 | MEDIUM | DozSubtitles COLORS が DoZ コラボ専用 6名で不一致 | (c) | — | 別チャンネルコラボ用の意図的設計。対応コスト>効果 |
| M003 | MEDIUM | OdinCountdown isUrgent=10秒固定 (30分タイマーに短すぎ) | (c) | — | 演出設計は殿の判断域。新 OdinCountdown 使用時に再検討 |
| M004 | MEDIUM | shorts -cq 28 低品質 (フォールバック clip が最終品質に影響) | (c) | — | 現状の品質で殿 OK。品質要件変更時に対応 |
| M005 | MEDIUM | vertical_convert.py ASS焼込み 2パス NVENC | (c) | — | 意図的 2段階設計 (字幕焼込み精度確保のため)。最適化は別 cmd |
| M006 | MEDIUM | vertical_convert.py tachie_displayed フラグで secondary 漏れ | (a) | ashigaru5 | secondary_speaker 経路で tachie_displayed 更新追加 |
| V_M007 | MEDIUM | get_duration() が pipeline_utils.py と vertical_convert.py で重複定義 | (a) | ashigaru5 | vertical_convert.py の get_duration() 削除 → pipeline_utils からimport |
| V_M008 | MEDIUM | Root.tsx OrarishTelop durationInFrames=8792 ハードコード | (d) | — | remotion-project/ personal workspace。殿判断 |
| V_M009 | MEDIUM | Root.tsx OrarishTelop text ハードコード | (d) | — | remotion-project/ personal workspace。殿判断 |
| V_M010 | MEDIUM | main.py main_speaker default が "dozle_club" vs "unknown" の 2系統 | (a) | ashigaru3 | L1322 を "dozle_club" に統一 (1行修正) |
| L001 | LOW | main.py 起動時 Remotion CLI チェック欠落 | (a) | ashigaru3 | ffmpeg/ffprobe/yt-dlp と同等の Remotion CLI チェック追加 |
| L002 | LOW | vertical_convert.py channel_logo フォールバック (MEMORY「フォールバック=異常」違反) | (a) | ashigaru5 | フォールバック削除 → ロゴ不在は例外 raise に変更 |
| L003 | LOW | main.py channel_icon dead variable | (a) | ashigaru3 | L1213-1214 の未使用 logo_path 変数を削除 |
| L005 | LOW | Root.tsx PREVIEW_SEC=60 マジックナンバー | (c) | — | remotion-project/ gitignored 個人作業域。殿が直接管理 |
| L006 | LOW | vertical_convert.py wrap_hook_text base_fontsize=120 ハードコード | (a) | ashigaru5 | MODULE_LEVEL 定数 DEFAULT_HOOK_FONTSIZE=120 として定数化 |
| L007 | LOW | main.py single モード dead code | (a) | ashigaru3 | --mode highlight が唯一の本番モード。single モード除去 |
| L008 | LOW | DozSubtitles unknown 灰色 (#808080) | (c) | — | 殿 design decision。displayUnknown Props 化は設計変更 |
| V_L009 | LOW | OrarishTelop.tsx WebkitTextStrokeColor #54C3F1 ハードコード | (d) | — | remotion-project/ personal workspace。殿判断 |
| V_L010 | LOW | main.py render_with_remotion timeout=300 マジックナンバー | (a) | ashigaru3 | REMOTION_RENDER_TIMEOUT_SEC = 300 定数化 |
| V_L011 | LOW | main.py finally の os.unlink 多重 try/except | (a) | ashigaru3 | `_safe_unlink()` ヘルパ化で 3行に短縮 |

---

## タスク起票一覧

| subtask_id | 担当 | 対象ファイル | 含む findings |
|-----------|------|------------|--------------|
| subtask_1671_a1 | ashigaru1 | inbox_watcher.sh | C3, C4, L1, L2 |
| subtask_1671_a2 | ashigaru2 | precompact_hook.sh, cron_health_check.sh, ntfy.sh, stop_hook_inbox.sh, fix_panes.sh, dashboard_lifecycle.sh | C2, H1, H2, H3, H5, M1, M3 |
| subtask_1671_a3a | ashigaru3 | main.py (wave1) | C001, H002, V_M010, L001, L003, L007, V_L010, V_L011 |
| subtask_1671_a3b | ashigaru3 | main.py (wave2, blocked_by a3a+a5) | C002 call site, H004 |
| subtask_1671_a4 | ashigaru4 | scripts/dashboard/server.py | C1 |
| subtask_1671_a5 | ashigaru5 | vertical_convert.py | C002 argparse, H001, M006, V_M007, L002, L006 |
| subtask_1671_a6 | ashigaru6 | make_expression_shorts.py | H006 |
| subtask_1671_a7 | ashigaru7 | inbox_write.sh, ntfy_listener.sh | M5, L3 |

---

## (b) 後続cmd 一覧

| 予定cmd | 内容 |
|--------|------|
| cmd_167x | ntfy.sh `_archive_old_done_cmds` 毎呼出実行の性能最適化 (M2) |
| cmd_167x | monitor.sh / context_watcher.sh を watcher_supervisor.sh / cron に登録 (M4) |
| cmd_167x | main.py importlib 多用リファクタ → 標準 import 化 (H005) |

---

## (d) 殿許諾確認事項

remotion-project/ は殿の personal workspace (.gitignore で除外)。以下は殿の判断が必要:
1. **H003** Root.tsx hardcode (FULL_SEC=4795) → defaultProps + CLI 引数動的化するか否か
2. **V_H007** bg_full.mp4 不在 → public/ に配置するか DozFull コンポジション削除か
3. **V_H007b** remotion-project/ 運用ドキュメント → context/ に1ページ追記するか (推奨) / 不要とするか
4. **V_M008/V_M009** OrarishTelop duration + text hardcode → defaultProps + CLI 引数化するか否か

---

## git commit 記録 (タスク完了後更新)

| subtask | commit hash | 完了時刻 |
|---------|------------|---------|
| subtask_1671_a1 | 1782c7e ✅ | 2026-05-09 07:34 |
| subtask_1671_a2 | 747ed42 ✅ | 2026-05-09 07:18 |
| subtask_1671_a3a | cee9da1 ✅ (dozle_kirinuki) | 2026-05-09 07:24 |
| subtask_1671_a3b | f034009 ✅ (dozle_kirinuki) | 2026-05-09 07:35 |
| subtask_1671_a4 | 8c30452 ✅ | 2026-05-09 07:12 |
| subtask_1671_a5 | f6f52df ✅ (dozle_kirinuki) | 2026-05-09 07:12 |
| subtask_1671_a6 | 9cbf088 ✅ (dozle_kirinuki) | 2026-05-09 07:12 |
| subtask_1671_a7 | b13c825 ✅ | 2026-05-09 07:12 |

**全 8 subtask 完了 (2026-05-09 07:35)**

---

**報告書作成**: 2026-05-09 (家老)  
**完了予定**: 全 subtask 完了後 git push + ntfy 通知
