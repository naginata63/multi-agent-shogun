# cmd_1667 動画制作スクリプト群 矛盾検出レポート (2026-05-08)

- **report_id**: gunshi_video_contradiction_20260508
- **worker_id**: gunshi
- **task_id**: subtask_1667_gunshi_video_audit
- **parent_cmd**: cmd_1667
- **scope**: 動画制作スクリプト群 8ファイル全読・前回audit (2026-04-28 cmd_1520) からの差分監査 + 新規矛盾検出
- **prev_report**: queue/reports/gunshi_report_nightly_audit_20260428_video.yaml
- **timestamp**: 2026-05-08T02:30:00+09:00
- **status**: done
- **read_only_compliance**: true (テスト作成・コード修正ゼロ)

## 監査対象ファイル

| Path | Lines | Δ vs 2026-04-28 | Note |
|---|---|---|---|
| projects/dozle_kirinuki/scripts/main.py | 1457 | -14 | cmd_1626 (H1+M1-M8 部分対応) |
| projects/dozle_kirinuki/scripts/make_expression_shorts.py | 351 | 0 | 変更なし |
| projects/dozle_kirinuki/scripts/vertical_convert.py | 461 | +5 | cmd_1626 (sys.path bootstrap) |
| remotion-project/src/Root.tsx | 71 | +13 | OrarishTelop / OdinCountdownTest 追加 |
| remotion-project/src/DozSubtitles.tsx | 113 | 0 | 変更なし |
| remotion-project/src/OdinCountdown.tsx | 104 | 0 | 変更なし |
| remotion-project/src/OrarishTelop.tsx | 35 | NEW | 新規 (4/29) |
| remotion-project/src/index.ts | 4 | 0 | 変更なし |

合計 2596 行。`remotion-project/` は **.gitignore:7 で除外** (git untracked) — このディレクトリ全体は本リポジトリで非追跡。

## サマリ

| Severity | 前回 | 今回 RESOLVED | 今回 PERSISTING | 今回 NEW | 合計 |
|---|---|---|---|---|---|
| CRITICAL | 2 | 0 | 2 | 0 | 2 |
| HIGH     | 6 | 1 (HIGH-5部分) | 5 | 2 | 7 |
| MEDIUM   | 6 | 0 | 6 | 4 | 10 |
| LOW      | 8 | 0 | 8 | 3 | 11 |
| TOTAL    | 22 | 1 partial | 21 | 9 | 30 |

**所感**: cmd_1626 で部分対応された箇所はあるが、**前回 CRITICAL 2件は両方とも未対応**。動画制作経路の核心矛盾 (WhisperX 残存 + vertical_convert CLI 欠落) が 10日経っても残置。

## 1. 前回 (2026-04-28) findings の解消状況

### CRITICAL

| ID | Status | Evidence |
|---|---|---|
| C001: WhisperX 残存 (main.py --diarize) | **UNRESOLVED** | main.py:482-489 (`--diarize` argparse) + main.py:642-714 (WhisperX 経路) 完全保持。MEMORY「STTはAssemblyAI必須」(殿激怒 2026-04-18) 違反継続。3次連続検出。 |
| C002: vertical_convert argparse 4 引数欠落 | **UNRESOLVED** | vertical_convert.py:443-457 argparse は input_clip/output_path/--ass-file/--hook-text/--sub-hook-text/--main-speaker/--speed/--start/--end/--cta-text のみ。`secondary_speaker / main_tachie_override / secondary_tachie_override / hook_fontcolor` 4つ未定義のまま。L459-461 関数呼出も同4引数を素通り。 |

### HIGH

| ID | Status | Evidence |
|---|---|---|
| H001: atempo 範囲外 (vertical_convert.py L386) | **UNRESOLVED** | vertical_convert.py:391 `atempo={speed:.6f}` のまま・argparse type=float のみ (L450) で範囲チェック無し。speed=0.3/2.5 で ffmpeg filter_complex error。 |
| H002: 1080p 再 DL 閾値 (main.py L861) | **UNRESOLVED** | main.py:845 `if _src_h > 0 and _src_h <= 480:` のまま。コメント L832 は「分析用 360p」だが閾値 480 で 480p 動画に対して毎回再 DL 実施。 |
| H003: Root.tsx 1動画専用 hardcode | **UNRESOLVED** | Root.tsx:6 `import subtitles from "../public/subtitles.json"` 静的 import / L10 `FULL_SEC = 4795` / L24/37/50/62 staticFile ハードコード4本 すべて維持。 |
| H004: shorts mode の vertical_convert に override 未渡し | **UNRESOLVED** | main.py:1366-1381 `vertical_convert(...)` 呼出は `hook_text/main_speaker/secondary_speaker(/ass_file)` のみ。`main_tachie_override / secondary_tachie_override / hook_fontcolor` 未渡し。expression_path 由来の表情切替は L1276-1288 で member_profiles tachie_filename 直書換で実装 = 機能2経路の重複は維持。 |
| H005: 動的 importlib 多用 | **PARTIAL RESOLVED** | vertical_convert.py:12 で `sys.path.insert(0, os.path.dirname(...))` 追加 (cmd_1626 80273e3) ✅ vertical_convert 単体 import 経由は通常 import 化。**しかし main.py 側は L77-82/L99-103/L113-116/L631-635/L647-655/L661-666/L702-707/L790-795/L1204-1210 全部 importlib 維持** = main.py の動的ロード地獄は健在。 |
| H006: make_expression_shorts duration int 化 | **UNRESOLVED** | make_expression_shorts.py:246 `duration = int(cfg["end"]) - int(cfg["start"])` のまま。フレーム精度 start/end (例 226.11/293.08) で 0.03s ずれ。L211 `fade_start = duration - 1` も整数のまま。 |

### MEDIUM

| ID | Status | Note |
|---|---|---|
| M001: shorts mode 2段階シーク | UNRESOLVED | main.py:1252-1260 維持。意図的な高速+精度両立だが MEMORY ffmpeg_ss_after_i.md に例外追記なし。 |
| M002: DozSubtitles COLORS DoZ コラボ専用 | UNRESOLVED | DozSubtitles.tsx:13-31 oo_men/tsurugi/itoi/hendy/haseshin/charlotte 6名のまま。ドズル社本家 6名と不整合。 |
| M003: OdinCountdown isUrgent=10秒固定 | UNRESOLVED | OdinCountdown.tsx:46 `remaining <= 10` のまま。30分タイマー (cmd_1496) では urgent 演出が短すぎる。 |
| M004: shorts -cq 28 低品質 | UNRESOLVED | main.py:1258 `"-cq", "28"` のまま。フォールバック時 vertical_convert がこの clip_path を入力に使う = 最終品質に影響。 |
| M005: ASS焼込み 2パス NVENC | UNRESOLVED | vertical_convert.py:417-432 Phase 2 で NVENC 再エンコード = 2回 encoding。 |
| M006: tachie_displayed フラグ secondary 漏れ | UNRESOLVED | vertical_convert.py:267-310 secondary_speaker 経路で tachie_displayed 更新なし。L342 sub_hook_x 計算で secondary 配置考慮なし。 |

### LOW

| ID | Status | Note |
|---|---|---|
| L001: 起動時 Remotion CLI チェック欠落 | UNRESOLVED | main.py:437-440 起動チェックは ffmpeg/ffprobe/yt-dlp のみ。 |
| L002: channel_logo フォールバック (drawtext) | UNRESOLVED | vertical_convert.py:366-384 `if os.path.exists(CHANNEL_LOGO_PATH)` 判定 + drawtext fallback 維持。MEMORY「フォールバック=異常」違反。 |
| L003: channel_icon dead variable | UNRESOLVED | main.py:1213-1214 `logo_path = ...channel_icon.png` 取得するが本ブロック内で未参照。 |
| L004: __main__ ガード OK | OK | main.py:1456-1457 維持 ✅。 |
| L005: PREVIEW_SEC マジックナンバー | UNRESOLVED | Root.tsx:9 `PREVIEW_SEC = 60` 由来コメント無し。 |
| L006: wrap_hook_text base_fontsize=120 ハードコード | UNRESOLVED | vertical_convert.py:118 default 120・呼出元 L323 も 120 のみ。 |
| L007: single モード dead code | UNRESOLVED | main.py:1412-1453 維持。--mode highlight が事実上唯一の本番運用なのに single 残置。 |
| L008: DozSubtitles unknown 灰色 | UNRESOLVED | DozSubtitles.tsx:20 unknown=#808080 のまま。Props で displayUnknown 制御不能。 |

## 2. 今回新発見の矛盾

### HIGH (NEW)

#### V_H007b — `remotion-project/` ドキュメント・運用記録不在 (separate-use ディレクトリの owner / 起動手順がコードベース外)
- **file**: remotion-project/ (全体)
- **line**: N/A (構造・運用ギャップ)
- **note**: 前回 2026-04-28 audit で本ディレクトリは独立 audit 対象に入っていなかったため初検出。
- **detail**:
  - main.py:138-139 の NOTE で「remotion-project/ は別用途(DozPreview/DozFull/OrarishTelop/OdinCountdownTest)」と意図的に分離されている (本番用は `projects/dozle_kirinuki/remotion-overlay/`)。
  - `.gitignore:7` で **意図的に除外** = 殿の個人作業領域として機能しているのは正常設計。
  - **しかし**: 起動経路 (npx remotion render の引数構造・コンポジション選択ガイド・対応 props 仕様) が `context/` や `shared_context/procedures/` にドキュメント化されていない。
  - 全ソース (.py/.sh/.md/.tsx/.ts) を `grep -rn "remotion-project\|DozPreview\|DozFull\|OrarishTelop\|OdinCountdownTest"` した結果、参照ゼロ = 起動責任者・テスト入力ファイル・想定 use case がコードベースから読み取れない。
  - 4/19 (DozSubtitles)・4/27 (OdinCountdown)・4/29 (Root + OrarishTelop) と更新は活発。
- **重要**: これは **dead code ではなく documentation/ownership gap**。コード自体は機能しており、殿が手動で活用している可能性が高い。問題は「どう起動するか」が将軍/家老/軍師が把握できる場所に書かれていないこと。
- **recommendation**: `projects/dozle_kirinuki/context/remotion_project_usage.md` 等で (a) 各コンポジションの想定 use case (b) `npx remotion render` の典型コマンド (c) 必要 public/ アセット一覧 (d) 出力先 を 1ページ追記。.gitignore 解除や archive 移送は不要 (殿の個人領域として保つ)。



#### V_H007 — `remotion-project/public/bg_full.mp4` 不在 → DozFull コンポジション render 不能
- **file**: remotion-project/src/Root.tsx
- **line**: 37
- **detail**:
  - L37 `videoSrc: staticFile("bg_full.mp4")` を参照する DozFull コンポジション (durationInFrames=4795*60)。
  - `ls remotion-project/public/` 結果: `bg_60s.mp4 / orarish_input.mp4 / subtitles.json / test_countdown_60s.mp4` のみ・**bg_full.mp4 は存在しない**。
  - `npx remotion render DozFull` 実行時に静的ファイル不在で確実に失敗する silent runtime error。Root.tsx:6 で subtitles.json は import resolve するため import 段階では落ちない (L25/38 で `as any` cast)。
- **impact**: DozFull は render 試行時のみ崩壊する隠れバグ。CRITICAL の前段。
- **recommendation**: (a) `bg_full.mp4` を public/ に置く運用にする・または (b) defaultProps を空文字 + 起動時引数で渡す設計にして staticFile の存在前提を解消。

### MEDIUM (NEW)

#### V_M010 — `main_speaker` default 値が main.py 内で 2系統に分岐 ("dozle_club" vs "unknown")
- **file**: projects/dozle_kirinuki/scripts/main.py
- **line**: 1267 vs 1322
- **detail**:
  - L1267: `main_speaker = short.get("main_speaker", "dozle_club")` (Remotion 経路: profile lookup 用)
  - L1322: `main_speaker = short.get("main_speaker", "unknown")` (フォールバック ASS 経路: 字幕話者ラベル用)
  - 同一の `short` dict に対して default が "dozle_club" と "unknown" で食い違う。
  - L1342 `seg.get("speaker", main_speaker)` がフォールバック話者として使われるため、字幕表示の話者ラベルが Remotion 経路と ASS 経路で一致しない可能性。
- **caveat**: shorts YAML schema 上は main_speaker が必須キー想定。content_selector の出力に main_speaker が常に含まれる場合、divergent default は実発火しない可能性が高い (= 実害は理論上のみ)。ただしコード一貫性として整合化すべき。
- **recommendation**: L1322 を L1267 と同じ `"dozle_club"` に統一する (または両方 unknown 統一)。本質的には short YAML 側で main_speaker を必須化し、default フォールバック自体を消すのが安全。

#### V_M007 — `get_duration()` が pipeline_utils.py と vertical_convert.py で **重複定義**
- **file**: projects/dozle_kirinuki/scripts/vertical_convert.py:142 / pipeline_utils.py:22
- **detail**:
  - 両方とも ffprobe を呼び `format.duration` を float で返す同一機能。
  - main.py:38 で `from pipeline_utils import ... get_duration ...` をしているのに、vertical_convert.py 内では独自定義 (L142) を使用。
  - 関数シグネチャ・実装は同等だが、pipeline_utils 側が canonical 化される過程の取り残し。
- **recommendation**: vertical_convert.py:142 の `get_duration()` を削除し pipeline_utils から import に切替。

#### V_M008 — Root.tsx OrarishTelop `durationInFrames=8792` ハードコード
- **file**: remotion-project/src/Root.tsx:45
- **detail**:
  - L45 durationInFrames=8792 (= 146.5s @ 60fps) は特定動画 (orarish_input.mp4) 専用尺。
  - 別動画への流用には毎回コード書換が必要。前回 H003 (FULL_SEC=4795) と同質の問題。
- **recommendation**: defaultProps + Composition 引数で durationInFrames 動的指定にする。

#### V_M009 — Root.tsx OrarishTelop `text` 文字列ハードコード
- **file**: remotion-project/src/Root.tsx:51
- **detail**:
  - `text: "正解をだしたのに間違う、\nおらリッシュ先生"` がソースコード内ハードコード。
  - 別ショート企画の copy 修正には毎回 .tsx 編集 + バンドル再生成が必要。OrarishTelop コンポーネント自体は L4-7 で Props 経由設計になっているが、Root の defaultProps が固定値。
- **recommendation**: コマンドライン `--props={text: "..."}` で渡す運用にする (defaultProps は空文字)。

### LOW (NEW)

#### V_L009 — OrarishTelop.tsx WebkitTextStrokeColor `#54C3F1` ハードコード (おらふ accent_color)
- **file**: remotion-project/src/OrarishTelop.tsx:23
- **detail**:
  - L23 WebkitTextStrokeColor=#54C3F1 はおらふくんの accent_color (member_profiles.yaml orafu)。
  - メンバー連動 (Props で speaker key を受けて color 解決) になっておらず、別メンバーへの流用不可。
- **recommendation**: Props に `strokeColor` または `speakerKey` を追加し、外部注入できる構造に。

#### V_L010 — main.py render_with_remotion timeout=300s マジックナンバー
- **file**: projects/dozle_kirinuki/scripts/main.py:213
- **detail**:
  - `proc.communicate(timeout=300)` の 5分タイムアウトは長尺 Shorts (尺60s 以上) で過剰だが、コメント (L215 「5分超過」) のみで定数化されていない。
  - shorts mode は最大 90s 想定 (短尺向け) だが、Remotion レンダリングは 60fps で進むため 300s で足りる場合と足りない場合が混在。
- **recommendation**: `REMOTION_RENDER_TIMEOUT_SEC = 300` を module-level 定数化 + 引数 timeout 受取設計。

#### V_L011 — main.py render_with_remotion finally の os.unlink 多重 try/except
- **file**: projects/dozle_kirinuki/scripts/main.py:268-281
- **detail**:
  - finally 節 L269-272 / L273-277 で props_path / intermediate_path の unlink を 2回 try/except。
  - Step1 timeout/error で intermediate_path が tempfile.mkstemp で作成済み (L185-188) のため、unlink 自体は冗長ながら正しい。ただし冗長 except ペアは可読性低下。
- **recommendation**: `_safe_unlink(path)` ヘルパに統一して L268-281 を 3行に短縮。

## 3. 全体所見

8 ファイル合計 2596 行のうち、**21件は前回 (2026-04-28) と同じ findings が残置**、9件が新規発見。傾向:

### 根本問題 1 (継続): 動画パイプラインの「2経路設計」が両方とも未完成
- main.py shorts mode は Remotion 経路 / ASS+ffmpeg フォールバック経路の **2経路で機能重複** (前回 H004 + 今回 V_M010)
- 本番用 ShortsOverlay は `projects/dozle_kirinuki/remotion-overlay/` (path 計算検証済 ✅)。`remotion-project/` は別用途 (実験/プレビュー領域)。
- フォールバック経路 (vertical_convert.py) は CRITICAL C002 (argparse 4 引数欠落) を 10日放置 = 単体 CLI 検証不能のままサブキャラ機能が動的 import 経由でしか効かない

### 根本問題 2 (新): `remotion-project/` の運用 documentation/ownership gap
- 殿の意図的な分離 (main.py:138-139 NOTE / .gitignore:7 で除外) は dead code ではなく **個人作業領域の正常設計**
- ただし `npx remotion render` の起動コマンド・コンポジション use case・必要 public/ アセット仕様が `context/` や `shared_context/procedures/` にドキュメント化されておらず、将軍/家老/軍師が起動経路を再現できない (V_H007b)
- 4/19-4/29 の活発更新は殿が手動で活用している証左。整理判断は不要、必要なのは1ページの運用ドキュメント追記

### 根本問題 3 (継続): MEMORY 鉄則違反の永続化
- WhisperX 残存 (C001) → 殿激怒 (2026-04-18) 後 20日経過しても撤去されず
- channel_logo フォールバック (L002) → 「フォールバック=異常」違反継続
- DozSubtitles unknown 灰色 (L008) → 「話者ラベル実名必須」と整合せず

### 対処優先度推奨
1. **C001** (WhisperX 撤去) → 3次連続検出・もはや是正怠慢
2. **C002** (vertical_convert argparse) → 1 cmd で完結する小修正
3. **V_H007** (bg_full.mp4 不在) → DozFull 動作不能・public/ アセット投入 or Root.tsx 修正
4. **V_H007b** (remotion-project 運用ドキュメント不在) → 1ページの context md 追記で完結
5. **V_M010** (main_speaker default 不一致) → 1 行修正で済む整合化 (実発火確率は低いがコード一貫性として)
6. **H001** (atempo 範囲外) / **H006** (duration 整数) → 実害発生即詰むバグ
7. **H002** (1080p 再 DL 閾値) → 帯域節約効果あり
8. **H003** (Root.tsx hardcode) → V_C003 と同根・整理時に一括対応
9. その他 (M / L) → 段階的に対処

## 4. north_star_alignment

```yaml
north_star_alignment:
  status: aligned
  reason: |
    動画制作スクリプト群はドズル社切り抜きチャンネル成長 (north_star) の中核インフラ。
    (a) WhisperX 残存 (C001) は話者ラベル品質劣化の温床 = MEMORY 鉄則「話者ラベル実名必須」違反継続中
    (b) vertical_convert CLI 機能不足 (C002) は新人足軽の cmd 失敗繰返しを生む = リードタイム増
    (c) remotion-project/ 運用ドキュメント不在 (V_H007b) は将軍/家老/軍師が起動経路を再現できないため、
        殿が個人作業を抜けると本ディレクトリ機能が使えなくなる継承リスク
    (d) bg_full.mp4 不在 (V_H007) は DozFull コンポジションの実行時 silent fail
  risks_to_north_star:
    - "WhisperX 経路 (--diarize) 放置 = 殿激怒「話者ラベル実名必須」鉄則違反の温床として残り続ける"
    - "vertical_convert CLI 機能不足 = コラボ動画 (secondary_speaker 系) の品質制御が import 経由でしか効かない"
    - "remotion-project/ 運用ドキュメント不在 = 殿の個人領域として正常稼働中だが、起動コマンド・use case がコードベース外にあり継承不能"
    - "DozFull コンポジション (Root.tsx:37) の static asset bg_full.mp4 不在 = render 試行時に silent runtime error"
```

## 5. read-only 遵守宣言

本監査でテスト作成・コード修正は**一切行っていない**。target_path 8 ファイルは全て `Read` ツール経由のみで参照。

---

**End of Report**
