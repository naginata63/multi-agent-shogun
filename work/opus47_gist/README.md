# Claude Opus 4.7 移行スニペット集

note記事「[Claude Opus 4.7初日、AIエージェントが自分のモデル切替を8つ観察した記録](https://note.com/naginata63)」に付属するコード断片。

## ファイル

| ファイル | 用途 |
|---------|------|
| `01_breaking_thinking_api.py` | `thinking` API の 4.6 → 4.7 移行（Extended thinking 削除 / Adaptive のみ） |
| `02_occams_razor_test.md` | `xhigh` effort 比較に使ったテストケース |
| `03_claude_p_json_output.json` | `claude -p --output-format json` の出力例（キャッシュ内訳付き） |
| `04_sampling_params_removed.py` | `temperature` / `top_p` / `top_k` が 400 エラーになる件のメモ |

## ライセンス

MIT。記事本体へのリンクはそのまま残してもらえると嬉しい。
