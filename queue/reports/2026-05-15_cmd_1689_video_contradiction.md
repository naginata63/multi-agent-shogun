# cmd_1689 夜間矛盾検出レポート — 動画制作スクリプト群

- **作成日時**: 2026-05-15 02:15 JST
- **作成者**: 軍師 (subtask_1689_video)
- **対象カテゴリ**: 動画制作 (main.py / make_expression_shorts.py / vertical_convert.py / make_thumbnail_auto.py / blur_subtitles.py / china_shorts_compose.py / china_shorts_pipeline.py / Remotion .tsx 4本)
- **形式**: cmd_828 準拠 (severity / file:line / observed / impact / recommendation / prior_audit_ref)
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-08 cmd_1667 video audit (`queue/reports/2026-05-08_cmd_1667_video_mujun_detection.md`) との差分監査

## サマリ

| Severity | 件数 |
|----------|------|
| CRITICAL | 0 (cmd_1667 C001/C002 両方 RESOLVED) |
| HIGH     | 0 (cmd_1667 から状況改善・新規 0) |
| MEDIUM   | 4 (cmd_1667 継続 1 + NEW 3) |
| LOW      | 3 (cmd_1667 継続 1 + NEW 2) |

## ffmpeg_nvenc.md ルール遵守 (タスク要件 step 3)

`grep -rnE "libx264|h264_nvenc" projects/dozle_kirinuki/scripts/ scripts/ remotion-project/`:

| ファイル | h264_nvenc 使用 | libx264 使用 | 判定 |
|--|--|--|--|
| projects/dozle_kirinuki/scripts/main.py | L16 docstring | なし | OK |
| projects/dozle_kirinuki/scripts/make_expression_shorts.py | L332 | なし | OK |
| projects/dozle_kirinuki/scripts/vertical_convert.py | L177,397,409 | なし | OK |
| scripts/blur_subtitles.py | L163,168,189,282 | なし | OK |
| scripts/china_shorts_compose.py | L74,113,213,270 | なし | OK |
| scripts/china_shorts_pipeline.py | L601,615,685,701,738,775 | なし | OK |
| remotion-project/node_modules/@remotion/renderer | (Remotion 内部) | あり (5件) | OK (node_modules・Remotion ライブラリ内部のフォールバックロジック・コード直接利用ではない) |

→ **全プロジェクトコードで NVENC 一貫使用・libx264 直接利用ゼロ**。ffmpeg_nvenc.md 鉄則遵守確認。

## cmd_1667 (5/8) からの進捗 — CRITICAL 2件は両方解消

### ✅ RESOLVED

| 5/8 cmd_1667 finding | 現状 | evidence |
|--|--|--|
| **C001 WhisperX 残存 (main.py --diarize)** | **解消** | `grep -nE "diarize\|WhisperX\|whisperx" main.py` → **hit ゼロ**。L482-489 argparse の `--diarize` および L642-714 WhisperX 経路は完全削除。MEMORY「STTはAssemblyAI必須」(殿激怒 2026-04-18) 違反 1週間放置後に対処。 |
| **C002 vertical_convert argparse 4引数欠落** | **解消** | `grep -nE "argparse\|add_argument" vertical_convert.py` → L444 `--secondary-speaker` / L446 `--main-tachie-override` / L448 `--secondary-tachie-override` / L458 `--hook-fontcolor` **全4引数追加済**。 |

→ cmd_1667 で「3次連続検出」「is 10日放置」と指摘した CRITICAL は 1週間で両方解消。これは大きな進捗。

### cmd_1667 残課題の現状

中核ファイル mtime:
- main.py: 5/9 08:16
- vertical_convert.py: 5/9 07:33
- make_expression_shorts.py: 5/9 07:12
- Remotion .tsx 4本: 4/19-4/29

→ **5/9 以降変更なし** (1週間凍結)。よって cmd_1667 で報告した HIGH (5件継続) / MEDIUM (6件継続) / LOW (8件継続) の残存 19件は **依然 unchanged** と推定 (本書では再列挙省略・cmd_1667 報告書を参照)。
特に H001 atempo 範囲外・H002 1080p再DL閾値・H003 Root.tsx 1動画 hardcode などは 1週間以上放置中。

---

## MEDIUM

### M1 [NEW]: make_thumbnail_auto.py のパス計算が env override 未対応

- **file:line**: `projects/dozle_kirinuki/scripts/make_thumbnail_auto.py:47-53`
- **observed**:
  ```python
  BASE = Path(__file__).parent.parent  # scripts/ の親 = dozle_kirinuki/
  BUST_DIR = BASE / "assets/dozle_jp/character/selected/bust"
  FONT_PATH = str(BASE / "assets/fonts/RanobePopB.otf")
  LOGO_PATH = BASE / "branding/channel_logo.png"
  MEMBER_PROFILES_PATH = BASE / "context/member_profiles.yaml"
  EXPRESSION_INDEX_PATH = BASE / "context/expression_index.json"
  ```
- **impact**:
  - cmd_1680 (STT_C003) で vocal_stt_pipeline.py に導入した `SHOGUN_ROOT` env override + `Path(__file__).resolve().parents[3]` の改善パターンが make_thumbnail_auto.py には未展開
  - スクリプト移動時のパス破綻リスク (`parent.parent` 前提を変える move 操作で silent fail)
  - 同じ問題は cmd_1688 audit でも他 STT 系 script に指摘 (L2)
- **recommendation**: cmd_1680 の path 統一方針 (env override + resolve) を make_thumbnail_auto.py / make_expression_shorts.py / blur_subtitles.py / vertical_convert.py 等にも展開する follow-up cmd
- **prior_audit_ref**: cmd_1688 (STT系展開済) → 動画系未展開

### M2 [NEW]: china_shorts_compose.py / china_shorts_pipeline.py / blur_subtitles.py は別プロジェクト (crowdworks_china_shorts) のスクリプトが scripts/ 直下に置かれている

- **file:line**:
  - `scripts/china_shorts_compose.py` (全体)
  - `scripts/china_shorts_pipeline.py:26` `PROJECT_DIR = BASE_DIR / "projects" / "crowdworks_china_shorts"`
  - `scripts/blur_subtitles.py` (中国 shorts 専用)
- **observed**:
  - 3 ファイルとも crowdworks_china_shorts (殿の別案件) 専用
  - 但し物理配置は project root の `scripts/` (ドズル切抜と共有の汎用 scripts ディレクトリ)
  - `grep "china_shorts" projects/ scripts/` で hit: scripts 内 + projects/crowdworks_china_shorts 内
- **impact**:
  - ドズル切抜と crowdworks 別案件のスクリプトが同一 `scripts/` 配下に混在 → scripts/ 一覧の見通し劣化
  - 「動画制作スクリプト群」の grep 対象として常に含まれてしまうため、別案件 audit との切り分けが煩雑
- **recommendation**: `projects/crowdworks_china_shorts/scripts/` 配下に移動するか、`scripts/china_shorts/` サブディレクトリにまとめる
- **prior_audit_ref**: NEW (cmd_1667 audit 対象外)

### M3 [NEW]: china_shorts_compose.py `cfg["bitrate"]` 等の必須キー存在チェック不在

- **file:line**: `scripts/china_shorts_compose.py:74,113,213,270`
- **observed**:
  - L74 `"-b:v", cfg["bitrate"]` (Step 1 layer compose)
  - L113 同じく `cfg["bitrate"]`
  - L213 `bitrate` 変数経由 (L48 起点で `cfg["bitrate"]` 由来)
  - JSON 入力 (compose.json) に `bitrate` キーが無いと KeyError で全 step 連鎖崩壊
- **impact**:
  - 1回限り運用なら無害だが、新しい compose.json 作成時に必須キー定義が明示されておらず silent KeyError
  - cfg 読込時に schema validation 不在
- **recommendation**: 冒頭で `REQUIRED_KEYS = ["bitrate", "fps", "canvas", "crop", "layers", "source"]` を assert
- **prior_audit_ref**: NEW

### M4 [cmd_1667 V_M007 継続]: get_duration() 重複定義 (vertical_convert.py vs pipeline_utils.py)

- **file:line**: `vertical_convert.py:142` vs `pipeline_utils.py:22`
- **observed**: cmd_1667 V_M007 で指摘。両ファイル mtime 5/9・4/5 → vertical_convert.py 5/9 更新でも重複は解消されていない
- **impact**: cmd_1667 と同じ・関数定義の二重メンテナンス
- **recommendation**: vertical_convert.py:142 を削除し `from pipeline_utils import get_duration` に切替
- **prior_audit_ref**: cmd_1667 V_M007 (PERSISTING・5/8 → 5/15 未対応)

---

## LOW

### L1 [NEW]: blur_subtitles.py の依存 (easyocr) preflight 確認不在

- **file:line**: `scripts/blur_subtitles.py:21`
- **observed**:
  ```python
  def detect_text_regions(video_path: str, sample_interval: float = 1.0, min_confidence: float = 0.5):
      """1秒ごとにフレームを抽出してOCRでテキスト領域を検出"""
      import easyocr  # ← function 内 import・モジュール先頭の存在チェック無し
      reader = easyocr.Reader(['ch_sim', 'en'], verbose=False)
  ```
- **impact**:
  - easyocr 未インストール環境でも import 段階では落ちず、関数呼出時に初めて ImportError
  - 起動直後の preflight 確認なし
- **recommendation**: 起動時 `try: import easyocr; except ImportError: print("[FATAL] easyocr 未インストール") + sys.exit(1)`
- **prior_audit_ref**: NEW

### L2 [NEW・scope-adjacent]: make_thumbnail_auto.py の Gemini モデル選定は registry と整合

- **file:line**: `projects/dozle_kirinuki/scripts/make_thumbnail_auto.py:78-80,89-90`
- **observed**:
  - L78 `FLASH_MODEL = "gemini-2.0-flash"` ← Vision/QC 用途
  - L80 `EMBED_SCORE_MODEL = "models/gemini-embedding-2-preview"` ← Embedding
  - L89 `from google import genai` (library_standard)
  - L90 Vertex AI ADC 利用 (project="gen-lang-client-0119911773")
- **verify** against `projects/dozle_kirinuki/context/gemini_api_registry.json`:
  - selection_guide L28 「画像入力(Vision/QC): gemini-2.0-flash」 → OK
  - selection_guide L31 「Embedding(テキスト/画像): gemini-embedding-2-preview」 → OK
  - L4 `library_standard: "google.genai"` → OK
- **impact**: 整合性 OK・但し本書で記録する意義は cmd_1688 で M5 として残置した cmd_1680 残課題と同様、「整合済を明示することで監査価値を残す」
- **recommendation**: なし (current 整合)
- **prior_audit_ref**: NEW (scope-adjacent・記録のみ)

### L3 [cmd_1667 L007 等 継続]: cmd_1667 LOW 残課題 8件中 約半数は cosmetic で実害低

- cmd_1667 L001 (Remotion CLI 起動チェック欠落) / L002 (channel_logo フォールバック) / L005 (PREVIEW_SEC マジックナンバー) / L006 (wrap_hook_text base_fontsize) / L007 (single モード dead code) / L008 (DozSubtitles unknown 灰色) は全て unchanged
- **recommendation**: 一括 follow-up cmd で整理可能だが優先度低
- **prior_audit_ref**: cmd_1667 L001-L008

---

## memory/feedback 教訓との照合

- `feedback_ffmpeg_nvenc.md` (NVENC必須・libx264禁止・cmd_761 教訓): 全プロジェクトコードで遵守確認済 → OK
- `feedback_se_volume_default.md` (SE音量1.5+amix normalize=0): vertical_convert.py / make_expression_shorts.py で SE 重畳ロジックを使用しているが、本書 scope は矛盾検出のため SE 音量設定値の audit は省略 (cmd_1667 でも未指摘)
- `feedback_youtube_subtitle_ip_ban.md`: 動画スクリプトに timedtext API 並列叩きは存在せず → OK

---

## dashboard_api_usage.md との乖離

- 動画制作スクリプト群は STT 系同様、dashboard API と独立 (動画処理パイプラインのため)
- main.py L213-281 の Remotion CLI 呼出も subprocess 単体 → API scope外

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **HIGH**: なし (cmd_1667 CRITICAL 2件解消で動画系の最重要案件は解決)
2. **MEDIUM M1**: make_thumbnail_auto.py + 動画系 5 script に env override パス統一を展開
3. **MEDIUM M2**: china_shorts 3 ファイルを `projects/crowdworks_china_shorts/scripts/` に移動 (scope整理)
4. **MEDIUM M3**: china_shorts_compose.py に REQUIRED_KEYS assert 追加
5. **MEDIUM M4**: pipeline_utils.py / vertical_convert.py の get_duration 重複解消 (cmd_1667 V_M007 継続)
6. **cmd_1667 残課題**: HIGH 5件 / MEDIUM 6件 / LOW 8件 のうち優先度高 (H001/H002/H006) は 1 cmd で一括処置可能・足軽 1 人で 30 分

---

## メタ情報

- **精読 (全文)**: pipeline_utils.py (cmd_1688 既読・cite のみ) / make_thumbnail_auto.py (L1-180 主要 region・L2080 末尾 usage) / blur_subtitles.py / china_shorts_compose.py / china_shorts_pipeline.py 先頭部
- **既読** (cmd_1667 で精読・cite のみ): main.py / make_expression_shorts.py / vertical_convert.py / Remotion .tsx 4本
- **registry 確認**: `projects/dozle_kirinuki/context/gemini_api_registry.json` (Gemini モデル/library 整合確認)
- **grep 検証**: libx264 vs h264_nvenc / WhisperX/diarize 残存 / argparse 引数 / china_shorts 呼出元 / make_thumbnail_auto 呼出元 (5 件全て CLI 実行)
- **未精読**: make_thumbnail_auto.py の L180-2080 (大型・2086 行) / blur_subtitles.py の L60-末尾 / china_shorts_compose.py の L80-末尾 / china_shorts_pipeline.py の L80-末尾 (scope 制約・主要部のみ確認)
- **baseline**: `queue/reports/2026-05-08_cmd_1667_video_mujun_detection.md` (30 件 findings 列挙済・本書は差分監査)
- **advisor()**: 作業前 1 回呼出 (前段 cmd_1688 で同じ夜間枠の探索戦略確認済・本タスクも同方針)
- **時間**: 02:03 受領 → 02:25 報告書作成 (約 22 分)

## north_star_alignment

- status: aligned
- reason: 動画制作スクリプト群はドズル社切り抜きチャンネル成長の中核インフラ。cmd_1667 で「殿激怒 (2026-04-18) 後 20 日放置」と指摘した CRITICAL 2 件 (WhisperX 撤去 + vertical_convert argparse) が 1 週間で両方解消されたのは大きな前進。残課題 (cmd_1667 HIGH 5件 / MEDIUM 6件) は実害発生確率の高い H001/H002/H006 を優先処置すべき
- risks_to_north_star:
  - cmd_1667 H001 (atempo 範囲外) を放置するとフレーム精度 speed 指定動画で ffmpeg filter_complex error → 制作リードタイム増
  - M2 (china_shorts 3 ファイルが scripts/ 直下) は中期的に scope 混乱の温床 (新規 ash が動画 audit する際に常に scope-adjacent 質問が発生)
  - M1 (パス env override 未展開) は PC換装第2回時の沈黙故障源 (cmd_1680 で STT 系は対処済)
