# --max-tokens 棚卸し調査レポート (cmd_1404)

- **調査日**: 2026-04-17
- **調査者**: 足軽2号
- **背景**: posttool_cmd_check.sh で `claude -p --max-tokens 100` が silent fail していた（本日発覚・commit 4445663 で修正済み）

## 検索概要

- `--max-tokens` (CLIオプション形式): **3件**（プロジェクト内、venv/queue自己参照除外）
- `max_tokens` (Python API形式): **多数**（全てvenv/サードパーティライブラリまたはqueue内アーカイブ）

## `--max-tokens` CLIオプション形式の検出結果

| # | ファイルパス | 行番号 | 該当行 | silent fail懸念度 |
|---|-------------|--------|--------|------------------|
| 1 | `projects/dozle_kirinuki/context/remotion_llm_style_design.md` | 227 | `"--max-tokens", "2000",` | **高** — claude CLI subprocess呼び出しコード |
| 2 | `work/cmd_1393/design.md` | 169 | `timeout 30 claude -p --max-tokens 100 2>/dev/null` | **高** — claude -p 併用の実行例 |
| 3 | `queue/reports/gunshi_report_qc_1393a.yaml` | 28 | `timeout 30 claude -p --max-tokens 100 (L83)` | **低** — 既に修正済みのQC報告書 |

### 除外（自己参照・第三 Party）

以下は調査対象外:

| ファイルパス | 理由 |
|-------------|------|
| `queue/shogun_to_karo.yaml` (多数) | cmd_1404のタスク定義自身 |
| `queue/tasks/ashigaru2.yaml` (多数) | subtask_1404aのタスクYAML自身 |
| `dashboard.md:144` | cmd_1404の進捗表示 |
| `venv/.../openai/cli/_api/chat/completions.py` | OpenAI CLIの独自オプション（Claude CLIとは無関係） |
| `venv/.../openai/cli/_api/completions.py` | 同上 |
| `data/semantic_index/metadata.json` | セマンティック検索インデックス（キャッシュデータ） |

## `max_tokens` Python API形式の検出結果（参考）

プロジェクト固有ファイル（venv除外）:

| ファイルパス | 行番号 | 内容 | 備考 |
|-------------|--------|------|------|
| `queue/archive/reports/gunshi_181a.yaml` | 10 | `gemini_flash_max_tokens: 8192` | 古いQC報告・参考値 |
| `queue/archive/tasks/gunshi_broken_*.yaml` | 複数 | APIコール例（`"max_tokens":1024`等） | アーカイブ済みタスク |
| `queue/cmd_archive/cmds_20260305_202724.yaml` | 177, 193 | max_tokens設定言及 | アーカイブ済みcmd |
| `queue/handoff/ashigaru1_*.md` | 複数 | `max_tokens=4096`（Python API） | 引き継ぎファイル |

**判定**: Python API形式（`max_tokens`）は全てアーカイブ/報告書内の記録。実行コードではないため silent fail リスクなし。

## 結論

### 高リスク（要対応）

1. **projects/dozle_kirinuki/context/remotion_llm_style_design.md:227**
   - Claude CLI subprocess呼び出しで `--max-tokens 2000` を使用
   - このコードが実際に実行される場合、Claude Code CLI v2.1.112+ で silent fail する
   - **対応**: `--max-tokens` を削除するか、代替手段に変更

2. **work/cmd_1393/design.md:169**
   - design doc 内の `claude -p --max-tokens 100` の実行例
   - この例がコピペされて使用されるリスクあり
   - **対応**: サンプルコードから `--max-tokens` を削除し、注意書きを追加

### 低リスク（対応不要）

3. **queue/reports/gunshi_report_qc_1393a.yaml:28** — 修正済みのコードへの言及
4. **venv/** — 第三 Party (OpenAI CLI)
5. **queue内自己参照** — タスク定義・cmd定義

### 修正済み（確認済み）

- **scripts/posttool_cmd_check.sh** — commit 4445663 で修正済み（本日）
