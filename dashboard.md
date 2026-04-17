# 📊 戦況報告
最終更新: 2026-04-17 09:16

## 💰 DingTalk音声QC（9万円案件）
🟢 稼働中 | 処理済み: **228件** / 10,000件 | 報酬見込み: **¥2,052**
| 指標 | 値 |
|------|-----|
| 確認済み | 220件 |
| スキップ（類似度低） | 7件 |
| エラー（無効音声） | 1件 |
| 平均類似度 | 90.4% |
| 最低類似度 | 32.9% |
| 平均音量 | -23.3 dB |

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### 🔴 夜間監査 nightly_audit_20260417_video — CRITICAL×1 HIGH×1 MEDIUM×2（動画制作）
詳細: `queue/reports/gunshi_report_nightly_audit_20260417_video.yaml`

**CRITICAL**:
- `projects/dozle_kirinuki/scripts/main.py` L1156: **logger変数が未定義** — `logger.warning(...)` があるが `import logging` / `logger = ...` が存在しない。タイトルカードあり+clip数とscene数不一致時にNameErrorで即死。推奨: `print(f"[main] WARNING: ...")` に置換

**HIGH**:
- `projects/dozle_kirinuki/scripts/vertical_convert.py` L174: **tempfile.mkstemp()で/tmp使用** — CLAUDE.mdルール違反。`work_dir`配下に変更推奨

**MEDIUM×2**: `generate_shorts_bg.py` L69 フォントフォールバックのサイレント飲み込み / `shorts_qc.py` L45 ffmpegエラーハンドリングなし

### 🔴 cmd_1400 — レールガン再編集版YouTube非公開アップ完了 → 殿確認待ち
- URL: https://www.youtube.com/watch?v=EXv3iJ9nLDc（再編集版・最新）
- **判断**: 確認後、公開OKなら公開指示を

### 🔴 cmd_1399 — Opus4.7 vs GLM+Advisor比較レポート完成 → 殿レビュー待ち
- ファイル: work/cmd_1399/opus47_vs_glm_advisor.md
- ✅ Q3固定版（cmd_1380〜1389）差し替え完了。評価スコア欄はTBD（将軍記入待ち）
- ⚠️ 軍師所見: cmd_1384のOK/NGワード混入事故の具体はYAML範囲内から裏付け不可（メモリ由来の可能性。将軍の最終精査要）
- ⚠️ pretool_check.shのwork/cmd_*ブロック問題は別cmdで対処推奨（足軽1号hotfix_notes参照）
- **判断**: Q3_fixed版完成後にレポートを確認・評価スコア記入を

### 🔴 cmd_1396 — お題06 panels JSON再生成完了 → 殿レビュー待ち
- panels_odai_06.json生成済み（**14パネル**・scene=odai_06）
- **レビューURL**: http://100.66.15.93:8770/work/20260406_仲間の気持ちがわかればチートになる世界でエンドラ討伐！【マイクラ】/output/manga_odai/panel_review.html
- **判断**: OKワード/NGワードを選定してパネル構成を確定せよ

### 🔴 cmd_1394 — note記事「Claude AdvisorでGLMの品質を96%引き上げた話」殿レビュー待ち
- 下書きURL: https://note.com/n/n0044698193bd
- カバー画像・挿絵2枚（advisor_simple_gemini.jpg + advisor_metaphor.jpg）・キャプション全設定済み
- **判断**: 内容・表示確認後、公開OKなら公開指示を

### ✅ cmd_1392/1393 — 将軍の指示拡大解釈防止策 実装完了
詳細: `queue/reports/gunshi_report_cmd1392.yaml`

**根本原因**: cmd の `command:` フィールドに殿の原文が残らない。家老以下は将軍の解釈しか見えないため検出不能。

**軍師提案4案（推奨: 案1+案3）**:

| 案 | 概要 | 実装難易度 | 効果 |
|----|------|-----------|------|
| **案1★** | PreToolUseフックで `lord_original:` フィールドを必須化。なければcmd書き込みBLOCKED | 低（1-2h） | 殿の原文を強制記録 |
| 案2 | PostToolUseで `lord_original` と `command` の動詞差分をWARNING | 中（3-4h） | 偽陽性リスク高 |
| **案3★** | instructions/karo.mdにlord_originalとcommandの比較チェックリスト追加 | 極低（15分） | 案1のデータを家老が検証 |
| 案4 | UserPromptSubmitフックで殿の発言を自動キャプチャ | 高（1日+） | 最も正確だが複雑 |

**軍師推奨**: 案1+案3の組み合わせ。「データを仕組みで強制し、そのデータでルールを実行可能にする」
- 案1でlord_originalフィールドをcmdに必須化（pretool_check.shに~30行追加）
- 案3でKaro受領時に lord_original vs command を比較チェック（karo.md追記のみ）

→ ✅ **cmd_1393で実装完了**（commit 6b33bcb・push済み）


### ✅ 夜間監査 cmd_1333 — 全CRITICAL/HIGH修正完了（2026-04-12）
- **CRITICAL/HIGH 10件を3並列で修正完了** (subtask_1333a/b/c)
- **1333a (ashigaru1)**: OAuth 4スコープ統一・privacy引数反映・delete確認追加・CLIパスshutil.which化
- **1333b (ashigaru2)**: LLMスキーマバリデ追加・clip_timestamps_raw境界チェック・h264_nvencハードコード除去
- **1333c (ashigaru3)**: IDLE_FLAG_DIR→queue/.flags/・awk→mawk化・generate_illustration.py Part.from_bytesフォールバック除去
- ⚠️ **未着手(MEDIUM)**: note_visual_qc.py Part.from_bytes / Playwrightプロファイル不一致 / download.sh yt-dlp不整合等（スコープ外）

### 🔧 夜間監査 2026-04-09 — STTパイプライン修正状況
- ~~CRITICAL/HIGH3件~~ → ✅ 全修正済み（subtask_1272a + 0ef982a3）
- MEDIUM: --gemini廃止コード残存 他 → 優先度低・未着手
- ⚠️ **xlDFsyNm_eE STT再実行の要否**: subtask_1272aでCRITICAL修正後に全尺完走済み（00:35:45・6名実名確認）。再実行不要であれば作業継続。再実行が必要な場合はご指示を。

### 🔧 技術的残項目（優先度低）
- 漫画フォント30書体ギャラリー未選定: http://100.66.15.93:8783/work/font_comparison/
- **⚠️ dozle_kirinukiサブモジュール push不可**: d4baa9c5でgcloud SDK（194MB）がコミット済み→GitHub 100MB制限でreject。scripts/の変更はローカルのみ保存中。git-lfs移行 or 履歴書換が必要

## 🚨 要対応

### 🔴 cmd_1404 — --max-tokens棚卸し調査完了 → 修正cmd発令の判断を
詳細: `queue/reports/gunshi_report_qc_1404a.yaml`
- **高リスク1**: `projects/dozle_kirinuki/context/remotion_llm_style_design.md:227` — `call_claude_cli` 関数内で `claude -p --max-tokens` 使用 → silent fail中の可能性
- **高リスク2**: `work/cmd_1393/design.md:169` — `timeout 30 claude -p --max-tokens 100` (設計書内・実スクリプトではないが参照リスクあり)
- **副産物**: `pretool_check.sh L78` の `status: assigned` 限定バグ発覚（status:in_progress移行後にtarget_path検証が機能しない）
- **判断**: 高リスク2件の修正cmd・pretool_check.shバグ修正cmdを発令するか？

### 🔴 cmd_1402 — 再現性検証レポート完成 → **殿がスコア記入待ち**
- ファイル: `work/cmd_1402/opus47_vs_glm_advisor_retest.md`（commit 54e366c）
- **主要観察**: (1)時間捏造+91%がモデル共通定常傾向と確定 (2)Q2条件Bで結論反転（統合しない→3層統合する） (3)pretool_check.sh L78-79バグ独立クロス確認
- **判断**: 評価スコア（正確性/深さ/実用性）を記入してください

### 🔴 夜間監査 nightly_audit_20260416_stt — HIGH×1（STTパイプライン）
詳細: `queue/reports/gunshi_report_nightly_audit_20260416_stt.yaml`

**HIGH**:
- `compare_speaker_srt.py` L18 ほか4ファイル: **MEMBERSハードコード（nekooji欠落）** — `["dozle","bon","qnly","orafu","oo_men"]` のみ。ネコおじ発話がunknown扱いになる。compare_speaker_srt.py（実運用影響あり）優先で `load_members_from_yaml()` に置換必要

**MEDIUM×1**: skills/transcribe.py L158: gemini_transcribe.py への参照がsymlink経由でarchive/整理時にリンク切れリスク

### 🔴 夜間監査 nightly_audit_20260415_infra — HIGH×2（インフラスクリプト）
詳細: `queue/reports/gunshi_report_nightly_audit_20260415_infra.yaml`

**HIGH**:
- `scripts/ntfy_listener.sh` L238: **認証情報ログ漏洩** — `${NTFY_TOKEN:-${NTFY_USER:-none}}` がNTFY_TOKENまたはNTFY_USERの実値をlogs/inbox_watcher_*.logに平文記録
- `scripts/posttool_yaml_check.sh` L3: **PostToolUseフック入力方式不一致** — `CLAUDE_TOOL_INPUT` 環境変数参照だが他フックはstdin方式→FILE_PATHが空→YAMLチェック未機能の可能性

**MEDIUM×3**: userprompt_ntfy_check.sh /tmp使用（CLAUDE.mdルール違反）/ context_watcher.sh PROJECT_DIRハードコード / slim_yaml.py typo（slim_shugun_to_karo）

### 🔴 cmd_1385 P6b 新3枚（OKワード修正済み）— 殿の選択待ち
- cmd_1384（OKワード混入版）を**正規スクリプトで再生成完了**。軍師QC PASS。
- **v1 / v2 / v3** の3枚（全てOKワード/NGワードテキストなし確認済み）
- ギャラリー: http://100.66.15.93:8770/work/20240113_いろんな時代の人になってエンドラ討伐！【マイクラ】/manga_railgun/out/gallery_p6b_gacha.html
- お題05 v3（全8枚）: http://100.66.15.93:8770/work/20260406_仲間の気持ちがわかればチートになる世界でエンドラ討伐！【マイクラ】/output/manga_odai/manga_odai_05/v3/gallery.html
- **判断**: P6b v1/v2/v3のどれを採用するか？お題05 v3は問題なければそのまま採用。

### 🔴 夜間監査 nightly_audit_20260413_stt — CRITICAL×2（STTパイプライン）
詳細: `queue/reports/gunshi_report_nightly_audit_20260413_stt.yaml`

**CRITICAL**:
- `skills/gemini-video-transcribe/transcribe.py` L167-178: **廃止済み** `gemini_speaker_pipeline.py` をsubprocess呼び出し→話者分離ありモードが実行時クラッシュ
- `projects/dozle_kirinuki/context/hl_sh_workflow.md` L87: **廃止済み** `gemini_speaker_pipeline.py` をStep2手順として記載→足軽が参照すると必ず失敗

**HIGH×4**: PROJECT_DIR算出脆弱・ECAPA-TDNN関数コード重複(~140行)・モンキーパッチ散在・stt_merge subprocess stderr未キャプチャ

**MEDIUM×5**: --geminiオプション残存・speakers_expected=6ハードコード・nekooji欠落（compare_speaker_srt.py）・タイムスタンプ境界値問題・「ぺけたん」ハードコード

→ ✅ cmd_1374完了（廃止参照3箇所除去・軍師PASS・commit 7386a3c・git push済み）

### 🔴 夜間監査 nightly_audit_20260414_video — HIGH×2（動画制作パイプライン）
詳細: `queue/reports/gunshi_report_nightly_audit_20260414_video.yaml`

**HIGH**:
- `projects/dozle_kirinuki/scripts/main.py` L333: `generate_thumbnail`内`esc()`エスケープ順序バグ → バックスラッシュ置換が最後（二重エスケープ）。正しい順序は`make_expression_shorts.py`・`vertical_convert.py`で実装済み
- `projects/dozle_kirinuki/scripts/make_expression_shorts.py` L295: **ffmpeg -ss が -i の前** → CLAUDE.mdルール違反。音ズレリスク。`vertical_convert.py`では正しく -i 後に配置済み

**MEDIUM×2**: generate_manga_short.py BASE_DIRハードコード / main.py selected_check_hook.sh絶対パス
**CLEAN**: NVENC全スクリプト適用済み / GCS URI方式準拠 / 廃止スクリプト参照なし


## 🔄 進行中（実行中のタスク）

| cmd | 内容 |
|-----|------|
| cmd_1401 | ✅ Q3固定版差し替え完了（commit afc56ed）→ opus47_vs_glm_advisor.md Q3はcmd_1380〜1389で確定 |
| cmd_1399 | ✅ 統合レポート完成（opus47_vs_glm_advisor.md）→ Q3_fixedで更新中（cmd_1401） |
| cmd_1397 | ✅ レールガン縦型クロップ+YouTube非公開アップ完了（h264_nvenc 1080x1920）→ https://www.youtube.com/watch?v=IpB4U4AmqS0 |
| cmd_1395 | ✅ 全チェックBashバイパス修正完了（軍師PASS・commit 7ec2df8・git push済み）|
| cmd_1394 | ✅ note下書き挿絵2枚挿入+キャプション完了 → 🚨殿レビュー待ち https://note.com/n/n0044698193bd |
| cmd_1393 | ✅ 将軍指示拡大解釈防止フック実装完了（軍師PASS・commit 6b33bcb・git push済み）|
| cmd_1392 | ✅ 将軍指示拡大解釈防止策 軍師分析完了（4案提案・推奨: 案1+案3）→ ✅ cmd_1393で実装決定 |
| cmd_1391 | ✅ GLM+Advisor難問テスト再実行 4.7/5.0（v1と同一・安定確認）commit cd53729・push済み |
| cmd_1390 | ✅ pretool_check.sh バグ2件修正完了（軍師PASS・commit b2b08db・git push済み）|
| cmd_1389 | ✅ GLM+Advisor難問テスト 4.7/5.0（GLM単体+0.4、Sonnet超え、Opus比-0.2）commit fb8119d・push済み |
| cmd_1388 | ✅ pretool_check.sh blacklist+WARNING+候補表示 二段構え完了（軍師PASS・commit a4c18f6・git push済み）|
| cmd_1387 | ✅ HIGH×2+MEDIUM×2修正完了（軍師PASS・commit 10005027・push不可）|
| cmd_1386 | ✅ HIGH×2+MEDIUM×3修正完了（軍師PASS・commit f526239+da6e8e5・git push済み）|
| cmd_1385 | ✅ P6b×3ガチャ＋お題05v3全8枚再生成完了（OKワード修正済み・軍師PASS）→ 🚨殿選択待ち |
| cmd_1373 | おらふくん未来人v4（スカウターレンズ青白発光・ホログラムなし）1枚完了（軍師PASS・commit aeb8684・git push済み）✅ 殿レビュー待ち |
| cmd_1375 | おらふくん未来人v5（v1ベース+SFハンドガン持ち）1枚完了（軍師PASS・commit 39eceb2・git push済み）✅ 殿レビュー待ち |

## ✅ 本日の完了
| cmd | 内容 |
|-----|------|
| cmd_1405 | 🔄 ✅Opus4.6[1m]完了(4b2827d) 🔄Sonnet4.6実行中(ashigaru3) → 完了後軍師がマトリクス統合 |
| cmd_1402 | ✅ 再現性検証レポート完成（commit 54e366c）→ 🚨殿スコア記入待ち |
| cmd_1404 | ✅ --max-tokens棚卸し調査完了（足軽2号・軍師PASS）高リスク2件発覚→🚨要対応参照 |
| cmd_1384 | ✅ railgun P6bガチャ3回（v1/v2/v3）生成完了（軍師CONDITIONAL PASS・v2推奨）→ 🚨殿選択待ち |
| cmd_1378 | ✅ panels_railgun P6b_orafu_revive_and_die API再生成完了（空吹き出しなし・軍師PASS） |
| cmd_1383 | ✅ お題05 v2ギャラリーHTML作成完了（全8パネル・ダークテーマ・セリフ表示・軍師PASS） |
| cmd_1381 | ✅ panels_odai_05_edited.json全8枚漫画パネルAPI生成（v2）完了（P3豚顔は殿OKの上採用・軍師PASS） |
| cmd_1382 | ✅ お題04早く寝なさいtono_edit.mkv縦型クロップ+YouTube非公開アップ完了（h264_nvenc 1080x1920）→ https://www.youtube.com/watch?v=zUOfksVGAV0 |
| cmd_1380 | ✅ おまたせしましたtono_edit.mkv縦型クロップ+YouTube非公開アップ完了（h264_nvenc 1080x1920・28.7秒）→ https://www.youtube.com/watch?v=MtT856uoUUM |
| cmd_1379 | ✅ 争わないでtono_edit.mkv縦型クロップ+YouTube非公開アップ完了（h264_nvenc 1080x1920・19.5秒）→ https://www.youtube.com/watch?v=Hx2QqTAesLo |
| cmd_1377 | ✅ panels_railgun.json P6b吹き出し禁止強化完了（2箇所追記・軍師PASS）|
| cmd_1376 | ✅ panels_odai_05_edited.json全8パネル背景バラエティ演出差し替え完了（マイクラ参照0件・軍師PASS）|
| nightly_audit_20260414_video | ✅ 動画制作パイプライン矛盾検出完了（CRITICAL=0 HIGH=2 MEDIUM=2）→ 🚨要対応参照 |
| cmd_1375 | ✅ おらふくん未来人v5（SFハンドガン持ち）1枚（軍師PASS・commit 39eceb2・git push済み）殿レビュー待ち |
| cmd_1374 | ✅ 夜間監査CRITICAL×2修正完了（gemini_speaker_pipeline.py廃止参照3箇所除去・軍師PASS・commit 7386a3c・git push済み）|
| cmd_1372 | ✅ おらふくん未来人v3（スカウターフレーム残し・ホログラムオフ）1枚（軍師PASS・commit a22e623・git push済み）|
| cmd_1371 | ✅ おらふくん未来人v2（スカウターなし）5枚（軍師PASS・commit 6f4e704・git push済み）ギャラリー: http://192.168.2.7:8770/work/orafu_futuristic/v2/gallery_v2.html |
| cmd_1370 | ✅ おらふくん未来人v1 5枚生成（orafu_futuristic_01〜05.png）殿レビュー待ち |
| cmd_1346 | ✅ お題4「早く寝なさい」v1全7枚生成（MENゴーグルOK・⚠️P7武器混入→🚨要対応参照）|
| cmd_1345 | ✅ お待たせしましたv5完成（P1/P6新規生成+P2-P5/P7はv4コピー）殿レビュー待ち |
| cmd_1344 | ✅ panels_check.html JSON選択UI追加完了（/api/list_panels_json+ドロップダウン・再起動済み）|
| cmd_1343 | ✅ お待たせしましたパネルv4全7枚（MENゴーグル全P確認）殿レビュー待ち |
| cmd_1342 | ✅ お待たせしましたパネルv3全7枚（7/7・ガチャ1回）殿レビュー待ち |
| cmd_1369 | ✅ queue/定期バックアップ完成（backup_queue.sh・rsync+tar.gz・7日保持・軍師PASS・commit 8cc6581・⚠️cron登録は別途必要）|
| cmd_1368 | ✅ config秘密鍵GPG暗号化バックアップ完成（backup_secrets.sh+restore_secrets.sh・AES256・往復テストPASS・軍師PASS・commit a91d9b2）|
| cmd_1367 | ✅ バックアップ完全性監査完了（HIGH×4・MEDIUM×6・LOW×4特定・backup_audit_report.md作成・commit 4b572b4）|
| cmd_1366 | ✅ MCPダッシュボードにAdvisor Proxyパネル追加完了（_get_advisor_proxy_stats()・HTMLパネル・commit 9fee1a1・git push済み・⚠️サーバー再起動必要）|
| cmd_1365 | ✅ localhost:8080 AIコメント復旧完了（原因: cron PATH不足でClaude CLI見つからず→フォールバックパス追加・4/13再分析済み・軍師PASS・commit c2cc6be）|
| cmd_1364 | ✅ DingTalk QC複数ログ集約完了（qc_log*.jsonl全合算・sources内訳追加・軍師PASS・commit 41922f9・git push済み・⚠️サーバー再起動必要）|
| cmd_1363 | ✅ advisor_proxy.py リトライ・CircuitBreaker・Metrics実装完了（commit 2ed77ee・git push済み・⚠️プロキシ再起動必要）|
| cmd_1362 | ✅ advisor_proxy.py handle_requestにrequest_idログ追加完了（import uuid・5箇所修正・commit cabf17c・git push済み）|
| cmd_1361 | ✅ advisor_proxy.py /health に uptime_seconds 追加完了（import time・_START_TIME・commit eeebd54・git push済み）|
| cmd_1360 | ✅ /api/agent_healthエンドポイント追加完了（全9エージェント死活監視・graceful degradation・軍師PASS）|
| cmd_1356 | ✅ panel_review.html保存ボタン実装完了（_edited.json中間保存・読み込み優先順）|
| cmd_1357 | ✅ advisor稼働テスト完了（足軽2号・advisor呼び出し2回確認済み）|
| cmd_1358 | ✅ advisor必須ルール検証完了（足軽1/2/3全員advisor2回確認。※YAMLにadvisor指示混入→自発性は不完全）|
| cmd_1359 | ✅ dingtalk_qc_loop.py --help追加完了（--help動作確認済み。gitignore対象のためcommit不可は設計上の仕様）|
| nightly_audit_20260413_stt | STTパイプライン矛盾検出完了（CRITICAL=2 HIGH=4 MEDIUM=5）|
| cmd_1355 | showStatus自動消去削除+CSSスピナー追加・characters空補完+プロンプト強化完了 |
| cmd_1354 | panel_review.html「パネル候補生成」Claude Opus 4.6組み込み完了（/api/generate_panels_llm・ref_images存在チェック・GEMINI_CONTEXT埋め込み）|
| cmd_1353 | ボタン名「パネル候補生成」変更＋parse_raw_to_rows()+save_raw_json_from_gemini()追加完了 |
| cmd_1352 | panel_review.html データ保全バグ修正完了（PANELS_DATA保持・director_notes等保護・grep確認22件）|
| cmd_1351 | panel_review.htmlファイル選択DD追加完了（_raw.json/panels JSON両対応・panelsToRows変換・スマホ対応）commit 17aaa10 |
| cmd_1350 | panel_review.html完成（DnD並替・話者DD・行追加削除・JSON生成・スマホタッチ対応）+ _raw.json出力 + /api/load_raw_candidates |
| cmd_1349 | panels_check.html話者変更機能追加完了（ドロップダウン・ref_images連動・スマホ対応）commit 3cbda815 |
| cmd_1347 | generate_panel_candidates.py完成（本番テスト・--odaiフラグ実装済み・git commit済み）動画→panels JSON全自動生成 |
| cmd_1341 | お待たせしましたパネルv2全7枚生成完了（7/7・ガチャ2回・P2 499リトライ）→ manga_odai_03_omataseshimashita_v2/ 殿レビュー待ち |
| cmd_1340 | お待たせしましたパネルv1全7枚生成完了（7/7・ガチャ1回）→ manga_odai_03_omataseshimashita/ |
| cmd_1339 | KOMAWARI_DESC全35エントリ修正完了（S2/T1-T6/D4-D8等）commit 1ce0aeb7 |
| cmd_1338 | panels_check.html shot_type表示・編集・保存先連動バグ修正完了 commit 49e87d27 |
| cmd_1337 | 争わないでパネルv2全6枚生成完了（6/6成功・768x1376px）殿レビュー待ち |
| cmd_1336 | panels_check.html JSON読み込み機能追加完了（パス入力欄+/api/load_panels_json動的再描画）|
| cmd_1335 | panels_check.html生成完了（45KB・6パネル）http://192.168.2.7:8770/work/output/manga_odai/panels_check.html |
| cmd_1333 | 夜間監査CRITICAL/HIGH 10件修正完了（3並列 1333a/b/c）|
| cmd_1332 | FINAL_COMPOSED.mp4 YouTube非公開アップ完了 → https://www.youtube.com/watch?v=XXVzw0tBBi4 |
| cmd_1331 | 英語学習動画 自動カット編集テスト YouTube非公開アップ完了 → https://www.youtube.com/watch?v=2f4hLWamREc |
| cmd_1330 | tono_edit.mkv 縦型クロップ+YouTube非公開アップ完了 → https://www.youtube.com/watch?v=0SBiIU74yvc |
| cmd_1329 | AI分析最新化完了 analysis_history:2026-04-11（04-06〜04-11の6日分追加・計20エントリー）|
| cmd_1328 | analytics data.json再構築完了 generated_at:2026-04-11 / dates:03-01〜04-08（39件）|
| cmd_1325 | 参考動画Vision分析完了 reference_vision_analysis.md(70KB/11チャンク) |
| cmd_1305a | CrowdWorks カット編集完了 cut_edited.mp4(529.7s/647MB) |
| cmd_1305b | CrowdWorks テロップASS生成完了 telop.ass(48件) |
| cmd_1305c | CrowdWorks Bロール画像生成完了 5枚(broll_001〜005.png) |
| cmd_1286 | ピンク羊総集編25件連結+YouTube非公開アップ完了（7:46・466s）→ https://www.youtube.com/watch?v=bqSQQcN1izM |
| cmd_1304 | ピンク羊完全版25件完了（13:36・clip_22復活）→ https://www.youtube.com/watch?v=_FsFx67be24 |
| cmd_1303 | ピンク羊25件STTカット再設計完了（24件変更・clip_22元範囲維持・clips_redesigned.json） |
| cmd_1293 | ピンク羊サムネ5人版完了（thumbnail_energetic_1.png既存・完成確認） |
| cmd_1302 | ピンク羊拡張版完了（13:17・24件・xfade・⚠️clip_22破損除外）→ https://www.youtube.com/watch?v=IQ5nRJVrsmg |
| cmd_1301 | 原始人漫画P1/P6/P7再生成完了（吹き出し禁止強化版・v5） |
| cmd_1300 | 原始人漫画P1/P6再生成完了（ナレーション枠+縦書き筆文字版・v4） |
| cmd_1299 | 原始人漫画7パネル再生成完了（ドズル豹柄ワンショルダー+ぼん紫束帯・v3） |
| cmd_1298 | 原始人ドズル立ち絵v3生成完了（ワンショルダー豹柄+金髪ポニーテール・1202KB） |
| cmd_1317 | fix_panes.sh + shutsujin_departure.sh に /advisor opus 自動送信追加完了（git 01c3c48）|
| cmd_1314 | panels_check_gen.py 複数表情プルダウン実装完了（同一キャラ複数ref→上段/下段個別選択）git 3e852da2 |
| cmd_1312 | panels_check_gen.py dozleプルダウンバグ修正完了（絶対パス含むdirname誤マッチ修正）git commit済み |
| cmd_1311 | panels_check_gen.py修正完了（絶対パス+director_notes追従・git 8f5b4e37）⚠️push不可（gcloud SDK 194MB問題） |
| cmd_1310 | panels_check_gen.py インタラクティブエディター完成（git 34c13c1） |
| cmd_1320 Phase2 | ⚠️ libx264違反→緊急停止指示済み。h264_nvencに切り替えて再実行中 | 足軽1対処中 |
| cmd_1322d | ⛔ P2〜P7生成中止（殿指示・再開なし） | 足軽2停止 |
| cmd_1322a | P1初回生成完了→ 殿JSON更新のため再生成へ |
| cmd_1324 | generate_manga_short.py GCS URI全面統一+デフォルト軽量モード完了 git 93427ca3 ✅ | 足軽3完了 |
| cmd_1321 | LLMプロンプト提案機能実装完了（POST /api/suggest_director_notes）server.py再起動待ち ✅ |
| cmd_1319 | panels_check.html fetch方式化完了（GET /api/load_panels_json追加）git commit済み ✅ |
| cmd_1318 | Geminiデバッグ完了 モデル正常/finish_reason=STOP ⚠️解像度768x1376px（品質原因か）| 完了 ✅ |
| cmd_1316a | おんりー合流漫画P1生成完了（殿確定JSON版）→ cmd_1318でデバッグ調査中 |
| cmd_1313a | CrowdWorksカット編集やり直し完了 cut_edited_v3.mp4（381.5s/462MB）品質修正中 |
| cmd_1309a | おんりー合流漫画P1生成完了 → 殿確認待ち（P2〜P7は確認後） |
| cmd_1308 | tono_edit3.mp4 YouTube非公開アップ完了 → https://www.youtube.com/watch?v=n9I1xCOWCKo |
| cmd_1307 | 原始人漫画P7再生成完了（吹き出しあり・セリフ正常・ぼん絶望ポーズ・director_notes修復済み） |
| cmd_1306 | 原始人漫画P7再生成（吹き出しなし版・将軍ミスのため cmd_1307 で是正済み） |
| cmd_1294/1297 | 原始人ドズル漫画7パネル再生成完了（全7枚・P6ドズル追加版） |
| cmd_1296 | ぼん平安貴族立ち絵v1生成完了（smug_r2ベース紫束帯・1635KB・843x1264px） |
| cmd_1295 | 原始人ドズル立ち絵v2生成完了（smile_r2ベース腰巻き変換・1400KB・843x1264px） |
| cmd_1288 | 原始人ドズル立ち絵リファレンス生成完了（ref_dozle_genshijin_illust.png・1049KB） |
| cmd_1287 | ピンク羊サムネ3パターン生成完了（pink_sheep_clips/thumbnail_energetic*.png） |
| cmd_1285 | 原始人ドズル漫画「仲直りの歌」7パネル生成完了 → http://192.168.2.7:8785/gallery_cmd1285.html |
| cmd_1284 | bon_trick動画化+YouTube非公開アップ完了（72秒・7パネル）→ https://www.youtube.com/watch?v=CPpwjO2BuyA |
| cmd_1283 | bon_trick P3/P5再生成完了（smile_r2適用・MEN吹き出し修正・R4版） |
| cmd_1282 | お題1 P6再生成完了（NGワード「かしこまりました」誤描画修正・1枚） |
| cmd_1281 | MENゴーグル目装着版4枚v9方式生成完了（成功4/0・commits: 417992c4+afadcdeb） |
| cmd_1279 | MENゴーグル目装着版ref_image生成完了（842x1264px・1発成功） |
| cmd_1278 | ショート全リスト4月分作成完了（13件・shorts_full_list_202604.md） |
| cmd_1277 | speaker_id_srt_based.py HIGH修正完了（MEMBERSハードコード→動的ロード） |
| cmd_1276 | お題1「あちらのお客様」動画やり直し完了（音声同期版47秒） |
| cmd_1275 | bon_trick P3/P4/P5再生成完了（R3版） |
| cmd_1274 | お題2「私のために争わないで」6枚再生成完了（ゴーグル目装着+NGワード修正版） |
| cmd_1273 | お題1「あちらのお客様からです」初回動画（40秒・旧版） |
| cmd_1272 | xlDFsyNm_eE STT全尺やり直し完了（PROJECT_DIRバグ修正込み・00:35:45） |
| cmd_1271 | srt_hotspot.py新規作成 + integrate_replay_hotspot.py Layer4統合完了 |
| cmd_1270 | お題2「私のために争わないで」6枚新規生成完了 |
| cmd_1269 | 夜間監査修正: pretool_check.shパス修正/inbox_write dead code削除 |
| cmd_1268 | ピンク羊追加候補10件発掘（合計25件・7分55秒） |
| cmd_1267 | qnly_death漫画ショートv4 YouTube非公開アップ |
| cmd_1266_b | お題1「あちらのお客様」6枚再生成完了（OK/NGテロップ修正版） |
| cmd_1265 | 3総集編クリップ→YouTube非公開アップ |
| cmd_1264_b | xlDFsyNm_eE 36分版merged SRT完成（523ブロック） |
| cmd_1263 | qnly_death+bon_trick 漫画パネル14枚生成 |
| cmd_1280 | MENゴーグル目装着版4枚 v9方式（白黒差分→RG | 4/9 |
| cmd_1201 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1204 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1209 | お題2「私のために争わないで」6枚再生成（� | 4/9 |
| cmd_1212 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1218 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1221 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1222 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1232 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1233 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1255 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| nightly_audit | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| shogun_direct | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1289 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/9 |
| cmd_1290 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/9 |
| cmd_1291 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/9 |
| cmd_1294 | お題2「私のために争わないで」6枚再生成（� | 4/10 |
| cmd_1297 | お題2「私のために争わないで」6枚再生成（� | 4/10 |
| cmd_1292 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/10 |
| cmd_1316 | お題2「私のために争わないで」6枚再生成（� | 4/11 |
| cmd_1317 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/11 |
| gacha45_shogun | お題2「私のために争わないで」6枚再生成（� | 4/11 |
| cmd_1330 | お題2「私のために争わないで」6枚再生成（� | 4/11 |
| nightly_audit_auto | ...\n    files: [...]
    detail: |
      ...
    recom | 4/12 |
| cmd_1332 | お題2「私のために争わないで」6枚再生成（� | 4/12 |
| cmd_1333 | お題1 P6（p6_achira_clear）のみ再生成（NGワード | 4/12 |
| cmd_1335 | お題2「私のために争わないで」6枚再生成（� | 4/12 |
| cmd_1377 | お題2「私のために争わないで」6枚再生成（� | 4/14 |

## 足軽・軍師 状態

| 足軽 | CLI | 状態 | 現タスク |
|------|-----|------|---------|
| 1号 | GLM | 完了 | subtask_1385a |
| 2号 | GLM | 実行中 | subtask_1388a（pretool_check.sh未登録スクリプト警告）|
| 3号 | GLM | 完了 | subtask_1387a |
| 4号 | GLM | idle | — |
| 5号 | GLM | idle | — |
| 6号 | GLM | idle | — |
| 7号 | GLM | idle | — |
| 軍師 | Opus | 完了 | nightly_audit_20260416_stt |

## APIキー状況
- **Vertex AI ADC**: ✅ 正常
- **GLM**: ✅ 足軽全員GLMで稼働中（advisor proxy + システムプロンプト注入対応済み）

## チャンネル実績（2026-04-01更新）
- 登録者**1,007人** / 視聴回数**98.4万回** / 総再生時間**5,925時間**
- **収益化条件は未達**

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
