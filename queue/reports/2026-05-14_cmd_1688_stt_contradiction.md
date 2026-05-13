# cmd_1688 夜間矛盾検出レポート — STT パイプライン

- **作成日時**: 2026-05-14 02:15 JST
- **作成者**: 軍師 (subtask_1688_stt)
- **対象カテゴリ**: STT パイプライン (vocal_stt_pipeline.py / stt_merge.py / speaker_id.py / vocab_helper.py + pipeline_utils.py / auto_fetch.py / assemblyai_stt_clips.py / apply_speaker_mapping_srt.py / batch_speaker_match.py)
- **形式**: cmd_828 準拠 (severity / file:line / observed / impact / recommendation / prior_audit_ref)
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-12 cmd_1680 final QC (`queue/reports/2026-05-12_cmd_1680_final_qc.md`) との差分を flag

## サマリ

| Severity | 件数 |
|----------|------|
| CRITICAL | 0 |
| HIGH     | 1 (NEW) |
| MEDIUM   | 5 (NEW 4 + cmd_1680 継続 1) |
| LOW      | 3 (NEW 2 + cmd_1680 継続 1) |

## cmd_1680 (5/12) からの状況

中核 4 ファイル (vocal_stt_pipeline / speaker_id / stt_merge / vocab_helper) は **mtime 5/11-5/12 で凍結・変更なし**。
よって cmd_1680 final QC で CONDITIONAL_PASS 判定した 8 件 AC は依然 PASS のまま。本書は **cmd_1680 で対象外だった 5 ファイル** (pipeline_utils.py / auto_fetch.py / assemblyai_stt_clips.py / apply_speaker_mapping_srt.py / batch_speaker_match.py) と、cmd_1680 残課題の現状追跡を主眼とする。

---

## HIGH

### H1 [NEW]: batch_speaker_match.py がメンバー一覧をハードコードし members.py 経由でない (定義乖離)

- **file:line**: `projects/dozle_kirinuki/scripts/batch_speaker_match.py:18`
- **observed**:
  ```python
  MEMBER_NAMES = {"dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"}
  ```
  対して中核スクリプトは全て `load_members_from_yaml()` 経由:
  - `speaker_id.py:27,30` MEMBERS = load_members_from_yaml()
  - `vocal_stt_pipeline.py:39,530,656,710,840` 5 箇所で load_members_from_yaml()
  - `stt_merge.py:37,842` 2 箇所
  - `apply_speaker_mapping_srt.py:19,21` MEMBERS = load_members_from_yaml()
- **impact**:
  - `member_profiles.yaml` 更新 (新メンバー追加・脱退) 時に **batch_speaker_match.py だけ反映漏れ**
  - L53 `any(s not in MEMBER_NAMES and len(s) == 1 for s in speakers)` の判定が乖離 → アルファベットラベル検出が誤判定するメンバー名が出る可能性 (例: 新メンバー追加時に「アルファベット」誤検出)
  - 新メンバー導入は YouTube チャンネル運営の中期計画にあり (memory: 「ぺけたん」言及あり) → 中期的に発火確率が上がる
- **recommendation**: `from members import load_members_from_yaml` import + `MEMBER_NAMES = set(load_members_from_yaml())` 化
- **prior_audit_ref**: NEW (cmd_1680 audit 対象外ファイル)

---

## MEDIUM

### M1 [NEW]: auto_fetch.py 冒頭 WARNING 「廃止済み」と全ロジック残存の乖離 (dead module + verbose)

- **file:line**: `projects/dozle_kirinuki/scripts/auto_fetch.py:20-21,22以降`
- **observed**:
  ```python
  print("[auto_fetch] WARNING: このスクリプトは廃止済み。STTはvocal_stt_pipeline.pyとstt_merge.pyを使用せよ。", flush=True)
  # ← この後も import + 全 logic (約 500 行) が継続定義される
  ```
- **call-site 検証**:
  - `crontab -l | grep auto_fetch` → 2 行 hit するが **両方コメントアウト** (`#15 18 * * *` / `#30 19 * * *`)
  - `grep -rn "auto_fetch" scripts/ shared_context/ config/ .claude/` → 自身の docstring + crontab.snapshot.txt のコメント行のみ
  - 実 call site 無し
- **impact**:
  - cron 無効化済 + 呼出元無し → **完全 dead module** で本番影響なし
  - ただし 500 行のスクリプトが warning だけ吐いて全関数定義する状態は誤解の温床 (新 ash がコピペ起点に使う可能性)
- **recommendation**:
  - (a) `legacy/` 配下に移動 (cmd_1679 で `transcribe_with_speakers.py` / `diarize.py` を移動した先例あり)
  - (b) `sys.exit(0)` を warning 直後に追加して即座に終了させる
- **prior_audit_ref**: NEW

### M2 [NEW]: assemblyai_stt_clips.py が SDK 経由・vocal_stt_pipeline.py が REST 直叩き (AssemblyAI 呼出方式の乖離)

- **file:line**: `projects/dozle_kirinuki/scripts/assemblyai_stt_clips.py:9` vs `vocal_stt_pipeline.py:197-247`
- **observed**:
  - `assemblyai_stt_clips.py:9`: `import assemblyai as aai` (公式 Python SDK 経由)
  - `vocal_stt_pipeline.py:197-247`: `import requests` + REST API 直叩き (`https://api.assemblyai.com/v2/upload` 等)
- **call-site 検証**:
  - `grep -rn "assemblyai_stt_clips" projects/ scripts/` → 自身 (Usage docstring) のみ
  - 実 call site 無し → **dead module** (本番影響なし)
- **impact**:
  - 現状は orphan のため実害なし
  - 万一将来 `assemblyai_stt_clips.py` を復活させる場合、SDK と REST で API 呼出方式が混在 → エラーハンドリング・タイムアウト・スピーカー分離設定の整合確認が必要
- **recommendation**: dead と判明済 → M1 と一括で legacy/ 移動 OR 削除
- **prior_audit_ref**: NEW

### M3 [NEW]: apply_speaker_mapping_srt.py COPY_FROM に特定動画名ハードコード

- **file:line**: `projects/dozle_kirinuki/scripts/apply_speaker_mapping_srt.py:33-35`
- **observed**:
  ```python
  COPY_FROM = {
      "merged__sVuKf5Zu4A.srt": Path(__file__).parent.parent / "work" / "20260214_寝ないと死ぬ" / "merged__sVuKf5Zu4A.srt",
  }
  ```
- **impact**:
  - 特定動画 `_sVuKf5Zu4A` (= 2026-02-14 「寝ないと死ぬ」回) のみコピー対象。1 回限りの bootstrap であれば理解できるが、スクリプト本体に埋め込まれており、新規動画増加時に COPY_FROM 更新が必要かどうか不明
  - L48-83 のマッピング適用ロジックは汎用 (yaml 駆動) なのに、L85-112 の COPY_FROM だけ動画固有名
  - work/ ディレクトリ削除時に COPY_FROM 経路で path 検証エラーが発生 (`error: コピー元なし`)
- **recommendation**: COPY_FROM ブロック削除 OR YAML 外出し (`speaker_mappings_copy_from.yaml` 等)
- **prior_audit_ref**: NEW

### M4 [NEW]: batch_speaker_match.py が run_speaker_match_only.py の preflight 確認なし

- **file:line**: `projects/dozle_kirinuki/scripts/batch_speaker_match.py:19-20`
- **observed**:
  ```python
  VENV_PYTHON = str(PROJECT_DIR / "venv" / "bin" / "python3")
  SCRIPT = str(Path(__file__).parent / "run_speaker_match_only.py")
  ```
  L106 で `subprocess.run([VENV_PYTHON, SCRIPT, ...])` を実行する前に **ファイル存在チェックなし**
- **verify**:
  - `ls run_speaker_match_only.py` → **実在** (5/4 作成・2.4K) → 即時実害なし
  - venv 配下の python3 も実在前提 (`venv/bin/python3`)
- **impact**:
  - run_speaker_match_only.py 削除や rename 時に subprocess エラー (FileNotFoundError) で全動画失敗
  - venv 破損時も同様
- **recommendation**: 冒頭で `assert Path(SCRIPT).exists()`・`assert Path(VENV_PYTHON).exists()` 追加
- **prior_audit_ref**: NEW (advisor 検証で dead link を rule out 済 → MEDIUM 確定)

### M5 [cmd_1680 残課題継続]: vocal_stt_pipeline.py:41 dead import + custom_vocabulary.yaml 不在 (compound)

- **file:line**: `vocal_stt_pipeline.py:41` + `auto_fetch.py:42`
- **observed**:
  - `vocal_stt_pipeline.py:41`: `from vocab_helper import apply_vocabulary` ← import 単独・本ファイル内 call site 0
  - `auto_fetch.py:42`: `VOCAB_PATH = PROJ_DIR / "custom_vocabulary.yaml"` ← ファイル不在
  - cmd_1680 final QC で家老判定要として残置済の項目
- **impact**:
  - cmd_1680 から 2 日間放置・変化なし
  - 当該 file は dead module (M1) のため auto_fetch 経路は実害なし
  - vocal_stt_pipeline.py 経路は stt_merge.py で語彙補正されるため機能 OK・但し意味のない import が残る
- **recommendation**: cmd_1680 final QC の家老向け推奨 (vocal_stt_pipeline.py:41 削除 or 利用箇所追加) を follow-up cmd で起票
- **prior_audit_ref**: cmd_1680 final QC (AC8 partial)

---

## LOW

### L1 [NEW・scope-adjacent]: pipeline_utils.py `_get_h264_encoder()` が h264_nvenc ハードコード

- **file:line**: `projects/dozle_kirinuki/scripts/pipeline_utils.py:10-12`
- **observed**:
  ```python
  def _get_h264_encoder() -> str:
      """h264_nvencを返す（RTX 4060 Ti専用機）。"""
      return "h264_nvenc"
  ```
- **scope**: 本 audit は STT パイプライン scope だが、pipeline_utils.py はタスクで列挙対象 + ファイル名から STT 関連と推定可能だった。実態は video エンコード用 utility (STT scope adjacent)
- **impact**:
  - PC換装 (2026-05-04) で RTX 4060 Ti 維持確認済 (memory) → 即時実害なし
  - 但し将来 GPU 換装・別マシン移行で `h264_nvenc` 未対応時に ffmpeg 失敗 (CPU `libx264` フォールバックなし)
- **recommendation**: CPU fallback (`libx264`) 検出ロジック追加 OR `os.environ.get("FFMPEG_H264_ENCODER", "h264_nvenc")` で env override 化
- **prior_audit_ref**: NEW (scope-adjacent qualifier 付き)

### L2 [NEW]: auto_fetch.py legacy_path 計算 `PROJ_DIR.parent.parent`

- **file:line**: `projects/dozle_kirinuki/scripts/auto_fetch.py:35-37`
- **observed**:
  ```python
  SCRIPT_DIR = Path(__file__).parent.resolve()
  PROJ_DIR = SCRIPT_DIR.parent               # projects/dozle_kirinuki/
  SHOGUN_DIR = PROJ_DIR.parent.parent        # multi-agent-shogun/
  ```
  `PROJ_DIR.parent` = `projects/`, `.parent.parent` = `multi-agent-shogun/` → OK
- **impact**:
  - 計算自体は正しい (2階上 = project root)
  - cmd_1680 で `vocal_stt_pipeline.py` の PROJECT_DIR に `parents[3]` + env override を導入したのに対し、`auto_fetch.py` はこの改良が未反映 (env override 無し)
  - 但し auto_fetch.py は dead module (M1) のため実害なし
- **recommendation**: cmd_1680 の path 統一方針 (env override) を全 STT 系 script に展開する follow-up cmd を家老起票
- **prior_audit_ref**: cmd_1680 (STT_C003 設計) — 中核 4 ファイル以外への展開未実施

### L3 [cmd_1680 残課題継続]: smoke test 未実施 (py_compile のみ)

- **file:line**: 全 STT スクリプト
- **observed**: cmd_1680 final QC で「実 STT パイプライン smoke test は API 消費要のため未実行」と記載し家老判断要として残置。5/12 → 5/14 で実行記録の追加形跡なし
- **impact**:
  - 中核 4 ファイル mtime 5/11-5/12 で変更ゼロ → smoke test しなくても regression 確率は低い
  - 但し AC10 が形式上未充足のまま
- **recommendation**: 別 subtask で実 smoke test 起票 (短尺動画 1 本・API 消費数百円許容)
- **prior_audit_ref**: cmd_1680 final QC (AC10 未充足)

---

## dashboard_api_usage.md との乖離 (タスク要件 step 3)

| script | API 利用 | 乖離 |
|--|--|--|
| `vocal_stt_pipeline.py` | (STT 専用・dashboard API 利用なし) | scope外・OK |
| `stt_merge.py` | (STT 専用) | scope外・OK |
| `speaker_id.py` | (STT 専用) | scope外・OK |
| `auto_fetch.py:46` | `INBOX_WRITE_SH = SHOGUN_DIR / "scripts" / "inbox_write.sh"` | bash 直叩き経路 (API 経由ではない・但し dead module ゆえ無視) |

API 利用観点では STT スクリプト群は dashboard API と独立 (動画処理パイプラインのため)。**乖離 finding は dead module auto_fetch.py のみ・実害なし**。

---

## memory/feedback 教訓との照合 (タスク要件 step 3)

- `feedback_scene_search_v2_auth.md` (Vertex AI ADC vs GEMINI_API_KEY): STT 系 script はいずれも `ASSEMBLYAI_API_KEY` / `DEEPGRAM_API_KEY` 利用のみ。Gemini API キー混入なし → 教訓適用済
- `feedback_youtube_subtitle_ip_ban.md` (timedtext API 並列 BAN): 該当処理は本 audit 対象スクリプトに存在せず → 関連なし
- `feedback_git_safety.md` (git add . 禁止 等): STT 系 script は git 操作行わず → 関連なし

---

## 推奨 follow-up cmd (家老・殿判断用)

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **HIGH H1**: `batch_speaker_match.py:18` MEMBER_NAMES を `load_members_from_yaml()` 化 (5 分・足軽 1 人)
2. **MEDIUM M1 + M2**: dead module 2 件 (`auto_fetch.py` / `assemblyai_stt_clips.py`) を `projects/dozle_kirinuki/scripts/legacy/` 配下に移動 (cmd_1679 移動先例に倣う)
3. **MEDIUM M3**: `apply_speaker_mapping_srt.py:33-35` COPY_FROM ブロック削除 OR yaml 化
4. **MEDIUM M4**: `batch_speaker_match.py` preflight 確認 (`run_speaker_match_only.py` + `venv/bin/python3` 存在 assert)
5. **MEDIUM M5**: vocal_stt_pipeline.py:41 dead import 削除 (cmd_1680 残課題)
6. **LOW L1**: `pipeline_utils.py:_get_h264_encoder()` env override 化
7. **LOW L3**: 実 STT smoke test の subtask 起票 (cmd_1680 残課題)

→ HIGH/MEDIUM の **6 件は 1 〜 2 cmd にまとめて一括処理可能** (足軽 1 人で 30 分以内)。dead module 移動 (M1/M2) は単独 cmd でも良い。

---

## メタ情報

- **精読 (全文)**: pipeline_utils.py / assemblyai_stt_clips.py / apply_speaker_mapping_srt.py / batch_speaker_match.py / auto_fetch.py (L1-80 + 主要 region)
- **既読** (cmd_1680 final QC 時に精読・本書では cite のみ): vocal_stt_pipeline.py / stt_merge.py / speaker_id.py / vocab_helper.py
- **schema 確認**: なし (STT 系で SQLite 操作なし)
- **call-site 検証**: `grep -rn` で 5 件全て (auto_fetch / assemblyai_stt_clips / run_speaker_match_only / load_members / member-hardcode) を実機確認
- **未精読**: run_speaker_match_only.py (存在のみ確認・内容は audit scope 外) / その他 projects/dozle_kirinuki/scripts/ の非 STT 系ファイル
- **baseline**: `queue/reports/2026-05-12_cmd_1680_final_qc.md` + 過去 5/9 cmd_1663 / 5/2 cmd_1564
- **advisor()**: 作業前 1 回呼出 (5 ファイル delta scope + 検証 5 点指針)
- **時間**: 02:03 受領 → 02:15 報告書作成 (約 12 分・cmd_1680 で既知のファイル群は再 audit 省略・新規 5 ファイルに集中したため短時間で完了)

## north_star_alignment

- status: aligned
- reason: cmd_1680 で中核 4 ファイルは CONDITIONAL_PASS 済・本書は対象外 5 ファイルを補完 audit。最大 finding は batch_speaker_match.py のメンバー定義乖離 (HIGH) — YouTube 運営の中期メンバー追加計画と関連し、修正未着手だと将来事故源。dead module 2 件 (M1/M2) は legacy 整理で clarity 向上
- risks_to_north_star:
  - H1 を放置すると新メンバー追加時に batch_speaker_match.py のみ反映漏れ・声紋マッチング誤検出
  - dead module 放置で新 ash がコピペ起点に誤利用するリスク
