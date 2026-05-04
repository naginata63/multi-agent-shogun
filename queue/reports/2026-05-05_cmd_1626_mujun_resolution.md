# cmd_1626 矛盾解消レポート — main.py

- **task_id**: subtask_1626_main_py_fix
- **parent_cmd**: cmd_1626
- **worker_id**: ashigaru2
- **timestamp**: 2026-05-05T06:05:42+09:00
- **status**: done

## 対象ファイル

`projects/dozle_kirinuki/scripts/main.py` (1,451行 → 1,426行, -29/+15)

## 修正項目

### H1. Remotion ディレクトリ不一致 — コメント追加

- **対応**: `render_with_remotion()` docstring 直下に説明コメント2行追加
- **内容**: "ShortsOverlay Remotion レンダリングは remotion-overlay/ を使用。remotion-project/ は別用途(DozPreview/DozFull/OrarishTelop/OdinCountdownTest)。"
- **効果**: 読者が誤認するリスクを排除。コード修正不要（パス自体は正しい）。

### M1. 未定義オプション getattr silent fail — argparse 追加

- **対応**: `--model` (str, default="claude-opus-4-6"), `--min-duration` (int, default=600), `--no-integrate-llm` (store_true) の3つの add_argument を追加
- **効果**: L818/L823/L825 の getattr がデフォルト値を返さず、CLI指定が正しく反映される。

### M2. detect_scene_changes dead import — 削除

- **対応**: `from detect_scene_changes import ...` 行から `detect_scene_changes`, `snap_to_scene_change`, `get_vocals_path` を削除
- **残存**: `find_silence_cut`, `get_demucs_vocals` は実際に使用されているため保持

### M3. --scene-snap dead flag — 削除

- **対応**: argparse から `--scene-snap` の add_argument 行を削除
- **理由**: `args.scene_snap` を参照する分岐がコード内に一切存在しない。完全な dead flag。

### M4. compute_dbfs_1s dead function — 削除

- **対応**: L110-133 の `compute_dbfs_1s()` 関数全体（24行）を削除
- **理由**: 全プロジェクトから1度も呼ばれていない。同等ロジックは main 内 L948-983 にインライン展開済み。

### M5. tempfile/TOCTOU — コメント追加のみ

- **対応**: `finally` ブロック内 `os.unlink(intermediate_path)` の直前に CAUTION コメント追加
- **内容**: "# CAUTION: potential TOCTOU race between unlink and proc finish"
- **理由**: 対応困難（構造的な制約）。コメントで将来の注意喚起のみ。

### M6. selected_check_hook.sh パス組み立て — 修正

- **対応**: dirname 呼び出しを3回→4回に修正（2箇所）
- **原因**: 3回dirname → `projects/` に到達（不正）。4回dirname → `multi-agent-shogun/` に到達（正しい repo root）
- **検証**: `find` で `/home/murakami/multi-agent-shogun/scripts/automation/selected_check_hook.sh` の存在を確認済み

### M7+M8. hook dead branch — コメント追加

- **対応**: 2箇所に説明コメント追加
  - L882 `hook = next(...)` の前: "from-candidates経路では hook=None一択。--skip-selectで外部selected.jsonを食わせた場合のみ有効"
  - L923 `if hook is not None:` の前: 同内容
- **理由**: dead branch だが仕様上有効（外部 selected.json 経由で hook 付きデータを流すユースケースあり）。削除せず説明のみ。

## scope 外 (touch 禁止)

L1-L12 (軽微) は本タスクの scope 外。別 cmd で対応予定。

## 検証

- `python3 -m py_compile projects/dozle_kirinuki/scripts/main.py` → **PASS**
