# cmd_1623 矛盾検出レポート — 動画制作スクリプト群

- **task_id**: subtask_1623_mujun_detection
- **parent_cmd**: cmd_1623
- **worker_id**: gunshi (Plan agent委任 + 軍師検証)
- **timestamp**: 2026-05-05T02:10:00+09:00
- **方針**: 読んで報告のみ・コード修正禁止・テスト禁止
- **findings 件数**: H=1 / M=9 / L=12 / 該当なし=4観点

## 対象ファイル
1. `projects/dozle_kirinuki/scripts/main.py` (1471行)
2. `projects/dozle_kirinuki/scripts/make_expression_shorts.py` (351行)
3. `projects/dozle_kirinuki/scripts/vertical_convert.py` (459行)
4. `remotion-project/package.json` + `remotion.config.ts` (短)
5. `projects/dozle_kirinuki/scripts/archive/make_shorts_complex_v16.py` (103行)

## 検出観点
- A. 関数間矛盾 (引数不整合・戻り値型ミスマッチ)
- B. 依存関係不整合 (import未定義・循環依存)
- C. dead code / 到達不能 (未使用変数・未呼出関数)
- D. 危険パターン (`rm -rf`・`shell=True`・ハードコードパス・秘密鍵)
- E. ファイル間結合矛盾

---

## H (致命) — 1件

### H1. main.py が参照する Remotion ディレクトリと cmd 指定対象の不一致
- **証跡**: `main.py:164-217` (`render_with_remotion()`) ／ `remotion-project/src/Root.tsx:13-71` ／ `projects/dozle_kirinuki/remotion-overlay/src/Root.tsx:48`
- **種別**: B/E (依存関係 + ファイル間結合)
- **問題**: `render_with_remotion()` は `remotion-overlay` ディレクトリの `ShortsOverlay` Composition を参照するが、cmd_1623 で対象指定された `remotion-project/` には `ShortsOverlay` Composition も `remotion.ts` エントリポイントも**存在しない**。`remotion-project/src/Root.tsx` には `DozPreview / DozFull / OrarishTelop / OdinCountdownTest` のみ・エントリは `src/index.ts`。実体の Shorts Remotion 経路は `projects/dozle_kirinuki/remotion-overlay/` 側にある。
- **影響**: もし `remotion-project` を「Shorts用 Remotion」と誤認したまま依存整理すれば Shorts レンダリングが完全停止する。逆に `remotion-project` を消しても main.py は壊れない。**ファイル間結合の前提自体が大きく食い違う致命的不整合**。
- **推奨アクション (修正禁止のため記録のみ)**: 後続cmdで「main.pyが実際参照するRemotion先=remotion-overlay」を明示し、cmd_1623対象指定を訂正する。

---

## M (重要) — 9件

### M1. 未定義オプション getattr による silent fail
- **証跡**: `main.py:818, 823, 825`
- **種別**: A/C
- **問題**: `getattr(args, "model", "claude-opus-4-6")` `getattr(args, "min_duration", 600)` `getattr(args, "no_integrate_llm", False)` を使うが、argparse で `--model` / `--min-duration` / `--no-integrate-llm` は **add_argument が一切無い** (grep ヒット0)。常にデフォルト値が返る。
- **影響**: highlight2 モードでモデル/閾値の切替が殿意図通り効かない。CLI 指定が黙殺される。

### M2. detect_scene_changes 関数の dead import
- **証跡**: `main.py:34`
- **種別**: B/C
- **問題**: `from detect_scene_changes import detect_scene_changes, snap_to_scene_change, ..., get_vocals_path, ...` のうち `detect_scene_changes`, `snap_to_scene_change`, `get_vocals_path` は本体内で1度も呼び出されていない。
- **影響**: 読み手が `--scene-snap` がまだ生きていると誤認する。L40 の「非推奨」記述があるが実装が無い stale arg。

### M3. --scene-snap dead flag
- **証跡**: `main.py:476-477`
- **種別**: C
- **問題**: `--scene-snap` arg は追加されているが、`args.scene_snap` を参照する分岐が存在しない（find_silence_cut しか実呼び出しなし）。
- **影響**: 完全な dead flag。指定しても何も起こらない（殿が「効かない」と再現報告する事故になる）。

### M4. compute_dbfs_1s 重複ロジック
- **証跡**: `main.py:110-133`
- **種別**: C
- **問題**: トップレベル関数 `compute_dbfs_1s(video_path)` が全プロジェクトから1度も呼ばれていない。同等のロジックは L948-983 で main 内にインライン展開されている。
- **影響**: dead function。重複ロジックの片方を更新し忘れる risk。

### M5. tempfile + Remotion 強制kill のレース
- **証跡**: `main.py:171, 233, 240-247, 280-298`
- **種別**: D
- **問題**: `tempfile.mkstemp/mkdtemp` で `props_path / intermediate_path / tmp_public_dir` を `/tmp` に作成し、Remotion失敗時に `signal.SIGTERM → SIGKILL` で強制 kill → `time.sleep(2)` の後 finally で削除。例外途中で proc が None のまま break すると mkstemp はクリーンされるが、L298 `os.unlink(intermediate_path)` 時に NVENC 出力がファイルに上書き中だと TOCTOU の可能性。
- **影響**: 連続失敗時に `/tmp` ゴミ堆積。稀にレース。

### M6. selected_check_hook.sh のパス組み立て破綻
- **証跡**: `main.py:753, 840`
- **種別**: D
- **問題**: 外部スクリプトを `os.path.dirname(...3回...)` で組み立て・main.py が `projects/dozle_kirinuki/scripts/` 直下にいる前提だが、symlink 等で別場所から実行した瞬間にパス破綻。`subprocess.run(..., check=False)` なので失敗を黙る。
- **影響**: hook が黙って無効化されると殿が承認したことにならない事故が起きる。

### M7. hook ブランチ dead branch (from-candidates 経由)
- **証跡**: `main.py:1078-1081`, L884, L882
- **種別**: A
- **問題**: scene_type が `"hook"` のシーンは `convert_candidates_to_selected()` が一切作らない (intro / highlight_* のみ生成 L416,441)。L882 で `hook = next((s for s in scenes if s["scene_type"] == "hook"), None)` だが from-candidates 経路では None 一択。
- **影響**: dead branch。仕様としては有効だが、コード上 hook付き selected.json を作るパスが main.py 内に存在しないので、保守時に「hook はもう使ってない」と誤判断される。

### M8. hook 分岐 dead path 同根
- **証跡**: `main.py:923-924`
- **種別**: C
- **問題**: 上記 M7 と同理由で `if hook is not None: all_scenes = [hook, intro] + body_scenes` 分岐は from-candidates 経由では届かない（外部から手書き selected.json を `--skip-select` で食わせた場合のみ生きる）。
- **影響**: 仕様としては有効だが、コード上 hook付き selected.json 生成パスがないため誤読の温床。

### M9. vertical_convert.py 直接実行 ImportError
- **証跡**: `vertical_convert.py:11-13`
- **種別**: B/D
- **問題**: モジュールトップレベルで `from font_config import get_font_path, FALLBACK_FONT_PATH`。font_config が `scripts/` ディレクトリ前提の sys.path を持たないため、別 cwd から `python3 vertical_convert.py ...` を直接呼ぶと **ImportError**。
- **影響**: cmd_1548 のような事故再発リスク。procedure 経由限定の「直接実行NG」コメントだけでは技術的にガードできていない。

---

## L (軽微) — 12件

### L1. detect_scene_changes 関数名重複 import
- **証跡**: `main.py:34`
- **種別**: C
- **問題**: `from detect_scene_changes import detect_scene_changes` と関数名がモジュール名と被り・関数自体は未使用。

### L2. _speaker_results デバッグ print
- **証跡**: `main.py:730`
- **種別**: C
- **問題**: `print(f"... 検出セグメント数: {len(_speaker_results)}")` の `_speaker_results` は識別子先頭アンスコ済（プライベート扱い）だが直後で print するだけのデバッグ用途。値は捨てられる。

### L3. unreachable warning print
- **証跡**: `main.py:1078, 1081`
- **種別**: A
- **問題**: L879 で「scenes 空ならsys.exit(1)」している以上 `scenes[0]` フォールバックは安全だが、警告 print が dead path にあるので log 解析を惑わす。

### L4. tachie None ガード未確認
- **証跡**: `main.py:1283, 1315`
- **種別**: A
- **問題**: `tachie_filename = os.path.basename(default_tachie) if default_tachie else None` で `props["tachiePath"]` に None が渡る。Remotion TS 受け側の None 対応は別途要確認。

### L5. open without with
- **証跡**: `main.py:1367`
- **種別**: D
- **問題**: `open(srt_path, "w").close()` で context manager 不使用。同等動作だが linter 警告対象。

### L6. sys.path 制御に依存した import
- **証跡**: `main.py:36-40`
- **種別**: B
- **問題**: 通常 `from X import Y` するモジュール (`compress_thumbnail`, `generate_chapters`, `font_config`, `pipeline_utils`, `subtitle_utils`, `ffmpeg_ops`) は同一ディレクトリ前提。L87で1度のみ sys.path 追加。`python3 -m projects.dozle_kirinuki.scripts.main` のような呼び出しで破綻。

### L7. vertical_convert 動的ロード暗黙依存
- **証跡**: `main.py:1218-1225`
- **種別**: B
- **問題**: `vertical_convert` を `importlib.util.spec_from_file_location` で動的ロードするが、vertical_convert.py 自身が L11-13 でトップレベル import を持つため、ロード元 cwd / sys.path に scripts/ が入っていないと exec_module 中に ImportError。L87 が先行して入れているおかげで動いている暗黙依存。

### L8. dozle_club key の命名揺れ
- **証跡**: `make_expression_shorts.py:26-33, 101-104`
- **種別**: B
- **問題**: `MEMBER_FILE_KEY` に `"dozle"` だけ存在し `"dozle_club"` キーは無い。一方 main.py / vertical_convert.py は `"dozle_club"` を default_speaker に使う (`shorts_list[].main_speaker`)。`make_expression_shorts.py` で `"dozle_club"` を指定すると Unknown member error で sys.exit(1)。

### L9. ffmpeg stderr 末尾切詰め
- **証跡**: `make_expression_shorts.py:342-347`
- **種別**: D
- **問題**: `subprocess.run(cmd, capture_output=True, text=True)` で `check=False`。失敗時に `raise RuntimeError("FFmpeg failed")` するが、長大な filter_complex で stderr 末尾3000文字しか出さないので根本原因を見失う。

### L10. FFMPEG / FFPROBE ハードコード
- **証跡**: `vertical_convert.py:15-16`
- **種別**: D
- **問題**: `FFMPEG = "/usr/bin/ffmpeg"` `FFPROBE = "/usr/bin/ffprobe"` ハードコード絶対パス。main.py は `shutil.which("ffmpeg")` で起動チェックしているのに、vertical_convert は presence を確認せず固定パス。

### L11. tmp clip 残留
- **証跡**: `vertical_convert.py:185-190, 432-434`
- **種別**: D
- **問題**: `subprocess.run(clip_cmd, check=True)` を try/except 汎用で wrap。途中で例外が起きると `_tmp_clip_*.mp4` が work_dir に残留する（ゴミ蓄積）。

### L12. archive/make_shorts_complex_v16.py 副作用 import 危険
- **証跡**: `archive/make_shorts_complex_v16.py:1-103`
- **種別**: C/E
- **問題**: 全体が絶対パス・テロップ/出力ファイル名インラインリテラル・`if __name__ == "__main__"` ガード無し。現行コードからは import 0件。**`python3 archive/make_shorts_complex_v16.py` を直接叩くと固有作業フォルダ `pipeline_iuAP6rAoGFk/` に強制書き込みする副作用あり**。

---

## 該当なし観点 (4件)

- **A. 関数間引数不整合 (呼出側 vs 定義側)**: `convert_candidates_to_selected`, `clip_and_add_text`, `concat_with_xfade`, `vertical_convert` 各シグネチャは呼出と一致 (H1 の結合レベル不一致は B/E に分類)。
- **D. shell=True 直接実行**: 5ファイル全て `shell=True` 不使用 (grep で 0件)。
- **D. 秘密鍵リテラル**: 5ファイル内に API key / token / private key リテラルなし。
- **B. 循環 import**: 5ファイル間で循環 import 検出なし (main.py → ffmpeg_ops/pipeline_utils/subtitle_utils/font_config/detect_scene_changes/compress_thumbnail/generate_chapters の片方向ツリー)。

---

## 軍師所感 (推奨 follow-up cmd 提示)

1. **(H1 解消)**: cmd_1623 対象指定を「`projects/dozle_kirinuki/remotion-overlay/`」に訂正する後続 cmd を立てよ。`remotion-project/` は別用途 (DozPreview/DozFull/OrarishTelop/OdinCountdownTest) であり、Shorts レンダリング経路と切り分け管理する。

2. **(M1+M3 解消)**: argparse 整合性 cmd を立て、`--model`/`--min-duration`/`--no-integrate-llm`/`--scene-snap` の add_argument 不足を修正するか、対応する getattr/参照を撤去せよ。

3. **(M2+M4+M7+M8 解消)**: dead import / dead function / dead branch のクリーンアップ cmd。

4. **(M9 解消)**: `vertical_convert.py` の sys.path 自前ガード (`sys.path.insert(0, os.path.dirname(__file__))`) を冒頭に追加する小規模 cmd。

5. **(L8 解消)**: `MEMBER_FILE_KEY` に `"dozle_club"` を追加するか、main.py 側で `"dozle_club"` → `"dozle"` の正規化を入れる。

6. **(L12 解消)**: `archive/make_shorts_complex_v16.py` を `if __name__ == "__main__":` ガード追加 or `archive/_disabled_*.py` リネームで副作用を封じる。

---

**注**: 本レポートは Plan agent の精読 findings を軍師が検証し採用した結果。コード修正は本タスクの範囲外。後続 cmd で対応せよ。
