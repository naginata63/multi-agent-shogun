# cmd_1625 完了報告: dashboard_lifecycle.sh cron 環境 exit 非0 の根本修正

## ステータス: DONE

## 根本原因

**`set -euo pipefail` と `log()` 関数の `[[ ]] &&` パターンの相互作用**

`scripts/dashboard_lifecycle.sh` の `log()` 関数の最後の行:

```bash
[[ $VERBOSE -eq 1 ]] && echo "$msg"
```

`VERBOSE=0` (デフォルト) の場合:
1. `[[ 0 -eq 1 ]]` → exit code 1 (false)
2. `&&` の右辺 `echo "$msg"` はスキップされるが、リスト全体の exit code は 1
3. これが `log()` の **最後のコマンド** なので、関数自体が exit code 1 で返る
4. `log` は条件コンテキスト (`if`/`||`) なしで直接呼ばれている
5. `set -e` が発動 → スクリプトが即座に終了

**cron 環境固有ではない** — 手動実行でも同様に exit 1 で終了していた (手動実行の成功は誤認だったか、以前は VERBOSE=1 で実行されていた可能性)。

### なぜ気付かれにくかったか

- スクリプトは start ログを書いた直後に `log()` の return code で exit する
- ログには "start" しか残らない ("end" は書かれない)
- stderr は nightly_audit.sh で log ファイルにリダイレクトされるが、エラーメッセージ自体が出力されない (set -e は黙って exit する)

## 修正内容

`scripts/dashboard_lifecycle.sh` line 52:

```diff
-  [[ $VERBOSE -eq 1 ]] && echo "$msg"
+  if [[ $VERBOSE -eq 1 ]]; then echo "$msg"; fi
```

`if/then/fi` 構文を使うことで、条件が false でも `if` 文全体は exit code 0 を返す。`set -e` は発動しない。

## 検証結果

| テスト | 結果 |
|--------|------|
| `bash -n` シンタックスチェック | PASS |
| 通常実行 (`bash scripts/dashboard_lifecycle.sh`) | exit 0 |
| `bash -x` トレース: "end" 到達確認 | PASS |
| cron 環境シミュレーション (`env -i PATH=/usr/bin:/bin`) | exit 0 |
| ログに start + end 両方記録 | PASS |

## 教訓

`set -e` 環境では、関数の **最後のコマンド** として `[[ condition ]] && command` パターンを使ってはならない。条件が false の場合に関数全体が non-zero を返し、呼び出し元の `set -e` が発動する。`if/then/fi` または末尾に `|| true` を付けること。
