| 観点 | 重大度 | 具体的問題 | 該当行 | 推奨対応 |
|------|--------|-----------|--------|---------|
| ①致命傷 (hook種類数) | 高 | 「hook (Anthropic Claude Code 公式機能・全 29 種類のライフサイクルイベント)」と断定。Claude Code 公式 hook event は SessionStart/UserPromptSubmit/PreToolUse/PostToolUse/Notification/Stop/SubagentStop/PreCompact 等の **約 8〜10 種類** が一次ソースで確認可能。「29 種類」は要verify、誤情報の可能性高 | 前章繋がりスライド スピーカーノート冒頭 | docs.anthropic.com/en/docs/claude-code/hooks を再確認し、正確な数に差替、もしくは「代表的な〇〇種類 (詳細は公式)」表記に変更 |
| ①致命傷 (公式概念断定) | 中 | 「Anthropic 公式概念 (Engineering Blog「Effective harnesses for long-running agents」2025-11)」を複数箇所で断定引用。記事タイトル・公開時期は訓練データ範囲外で要verify | 前章繋がり / まとめ / カバー完了スライド | URL・記事タイトル・公開日を一次ソースで確認、未確認なら「Anthropic が用いる用語」程度に弱める |
| ①致命傷 (Permissions仕様) | 中 | 「権限モード (6 種): default / acceptEdits / plan / auto / dontAsk / bypassPermissions」と断定列挙。公式に確認できるのは default / acceptEdits / plan / bypassPermissions 等で、`auto`/`dontAsk` は要verify。「評価順 deny → ask → allow」も要verify | 公式 Permissions スライド | docs.anthropic.com/en/docs/claude-code/iam で正確なモード名と評価順を再確認 |
| ②論理飛躍 | 低 | 「`try/except` と呼ばれます」を未経験者に投げているが、それが何を意味するか説明なし。「エラーを捕捉して握り潰し」だけでは初学者は像が結べない | 「完了しました」スライド | 「`try/except` = エラーが起きても止まらず先に進む書き方」と1行補足 |
| ③専門用語の唐突登場 | 中 | `jq -r '.tool_input.command'` がスライドに登場するが説明ゼロ。社会人 2-3 年目には不明。`stderr`/`stdout`/`exit code` も同様 | PreToolUse BLOCK スライド | コード例にコメントで「jq = JSON から値を抜き出す道具」「stderr = エラーメッセージ用の出力先」等を併記 |
| ③専門用語の唐突登場 | 低 | `cron`「(スケジュール実行)」は括弧書きあるが「hook と組み合わせて」が唐突 | watcher スライド | 「Claude Code 単体での `cron` 統合は公式機能ではなく、外部スケジューラを併用するイメージ」と注記 |
| ④フック文型 | 中 | カバータイトル「失敗を見逃さない仕組み — 黙って壊れる AI を検知し、止めるべき操作を止める」はやや教科書的。痛点呼びかけ型なら「『完了しました』を信じて本番を壊したあなたへ」等のほうがインパクト高 | カバースライド | 痛点直接呼びかけ型へ差替検討 (前章ch06のレビュー観察と同方向) |
| ⑤スライド数 | 高 | カバー + 本編 + 確認問題 + 解答 + 完了カバー で **計 19 枚**。10-12 枚推奨を大幅超過 | 全体 | (a)「4 つの解決策まとめ」スライドと「この章のまとめ」を統合、(b)「禁止操作リスト具体例」と「ch07 との連動」を 1 枚 2 列化、(c)「watcher」と「--dry-run」を 1 枚に圧縮 → 14 枚以下を目指す |
| ⑥ターゲット適合 | 中 | bash スクリプト例 (`INPUT=$(cat); COMMAND=$(echo ... \| jq -r ...); if echo ... \| grep -qE ...; then exit 2; fi`) は「なんとか IT 用語わかる程度」には完全に未知の領域。SQL の `DROP TABLE`/`TRUNCATE` も同様 | PreToolUse BLOCK スライド・禁止操作具体例 | スクリプトは付録扱いにし本編では擬似コード or 図式化。「DROP TABLE = テーブルごと全削除する SQL」と注釈 |
| ⑥ターゲット適合 | 低 | 「終了コードが 0 以外（プログラムが正常終了すると 0、異常終了すると別の番号を返す仕組みです）」は丁寧でOK。同様の親切さを exit code 2 にも適用すべき | PreToolUse BLOCK | 「exit code 2 = Claude Code に『この操作を中止せよ』と伝える特別な番号 (公式仕様)」と一行補足 |
| ⑦章間整合性 | 低 | ch07 振り返りで「stdin JSON 一択 (`$1`・環境変数は公式仕様に無い)」と再強調しており整合性 OK。ハーネス概念の引用も ch01〜ch07 と整合 | 前章繋がりスライド | 修正不要 |
| ⑧handoff/rehydrate 残存 | — | 該当箇所なし | — | 修正不要 |
| ⑨v4/v5/なぎなた残存 | — | 該当箇所なし | — | 修正不要 |

**総合所見**: ch08 は「黙って失敗の3パターン → 4 解決策 → ch07 連動 → BLOCK プロトコル」という骨格が明快で、ハーネス層の総まとめとしての構造設計は良好。一方、最大の懸念は **hook「全 29 種類」断定**・Permissions モデルの 6 モード列挙・「Effective harnesses for long-running agents 2025-11」記事の引用が訓練データ範囲外で一次ソース未verify な点であり、収録前に公式 docs での再確認が必須。また bash/jq/SQL のコード露出が「IT 用語わかる程度」のターゲットには重く、19 枚という枚数も推奨を大幅超過。技術的事実の verify + コード露出の付録化 + スライド統合の 3 点で品質を上げられる。

**総合重大度**: 中

**残存問題** (優先度順):
- [高] hook event 数「29 種類」を docs.anthropic.com/en/docs/claude-code/hooks で再確認し、正確な数 (約 8〜10 種) に修正
- [高] スライド総数 19 → 14 枚以下に圧縮 (4 解決策まとめ + 章まとめ統合、watcher + dry-run 統合、ch07 連動 + Permissions 統合等)
- [中] Permissions モデルの権限モード 6 種類 (`auto`/`dontAsk` 含む) と評価順を一次ソースで verify
- [中] 「Effective harnesses for long-running agents 2025-11」記事の存在・タイトル・公開日を anthropic.com で確認、未確認なら表現を弱める
- [中] bash スクリプト例 (jq/grep/exit code 2/JSON) を付録分離し、本編は概念図 + 擬似コードで簡略化
- [中] カバータイトルを痛点直接呼びかけ型へ差替検討 (「『完了しました』を信じて本番を壊した経験はありませんか?」等)
- [低] `try/except`・`stderr`・`stdout`・`cron`・`DROP TABLE` に各 1 行の注釈追加
