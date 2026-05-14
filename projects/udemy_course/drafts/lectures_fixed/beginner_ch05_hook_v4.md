---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 1.7em; padding: 50px 70px; background: #fafafa; display: flex !important; flex-direction: column !important; justify-content: flex-start !important; align-content: flex-start !important; align-items: stretch !important; }
  section h1:first-child, section h2:first-child { margin-top: 0; }
  section.cover { background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%); color: #fff; text-align: center; justify-content: center !important; align-items: center !important; }
  section.cover h1 { font-size: 1.6em; color: #fff; border: none; }
  section.cover h2 { font-size: 1.0em; color: #fde68a; }
  section.cover .meta { font-size: 0.7em; opacity: 0.85; margin-top: 1.5em; }
  h1 { color: #1e3a8a; border-bottom: 3px solid #1e3a8a; padding-bottom: 0.2em; font-size: 1.4em; }
  h2 { color: #2563eb; font-size: 1.1em; }
  h3 { color: #4b5563; font-size: 1.0em; }
  blockquote { border-left: 4px solid #f59e0b; background: #fffbeb; padding: 0.4em 0.8em; font-style: italic; color: #78350f; }
  code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  pre { background: #1e293b; color: #f1f5f9; padding: 0.6em; font-size: 0.7em; border-radius: 6px; }
  table { font-size: 0.78em; border-collapse: collapse; }
  th { background: #1e3a8a; color: #fff; padding: 0.4em 0.8em; }
  td { padding: 0.4em 0.8em; border: 1px solid #ddd; }
  .big { font-size: 1.6em; font-weight: bold; color: #1e3a8a; }
  .free { background: #facc15; color: #78350f; padding: 2px 8px; border-radius: 4px; font-size: 0.65em; font-weight: bold; }
---

<!-- _class: cover -->

# Hookの入門
## AIの安全装置を作る

<div class="meta">
初級編 — 第5章 (約 30 min) [L3 ハーネス入門]<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
こんにちは、なぎなたと申します。この第5章では、Claude Codeの「Hook」という仕組みを学びます。前章で 3階層モデルの L3 ハーネスが Anthropic 公式の概念 (Agent = Model + Harness) であり、hook はその実装基盤を構成する公式機能の一つだと学びました。本章ではその hook の最も基本的なイベントである PreToolUse を実際に使い、AI がプロジェクトで作業する際に危険な操作を自動的に検知してブロックする安全装置を作ります。30分で、その仕組みと設定方法をしっかり理解しましょう。
-->

---

## 🎯 この 30 分で得られること

1. **Hookとは何か** — AIのライフサイクルイベントに任意の処理を発火させる仕組みを説明できる
2. **PreToolUse Hook** の仕組みと役割を理解する
3. AIの危険操作を **自動検知・ブロックする仕組み** を説明できる

<!--
この章の目標は3つです。まず Hook が何かを理解し、次に最も重要な PreToolUse Hook の仕組みを学び、最終的に「AI が危険な操作をする前に自動で止める仕組み」を自分の言葉で説明できるようになります。Hook には公式で 29 種類のライフサイクルイベントがありますが、本章ではその代表例である PreToolUse 1 つに集中します。讲座全体を通して一貫するテーマは「安全」です。
-->

---

# 前章からの続き — L3ハーネスの代表機能を実装する

> 前章 (第4章) で確認した到達点:
> **L1 プロンプト** = 人間の意図を伝える
> **L2 コンテキスト** = プロジェクト知識を永続化する
> **L3 ハーネス** = hooks/skills/sub-agents 等でAIを制御・拡張する周辺基盤
> (Anthropic 公式: **Agent = Model + Harness** / Engineering Blog 2025-11)

- L1 と L2 は **指示を与える** 仕組み
- L3 ハーネスは **動作を監視・制御・拡張** する設計分野で、その中心実装の一つが **Hook**
- 前章で触れた **公式 29 種類のライフサイクルイベント** のうち、本章は最も基本となる **PreToolUse** に絞って入門する
- 建築現場に「安全監督」がいるように、PreToolUse Hook は **AI のツール実行直前に立ち止まる監視役**

> 💡 この章で学ぶ Hook = **L3 ハーネスの公式実装機能 / その入口にあたる PreToolUse**

<!--
前章「生成AIエンジニアリングの歴史」で、3階層モデルが必然的に生まれた経緯と、特に L3 ハーネスが Anthropic 公式の概念であることを学びました。L3 ハーネスは「Agent = Model + Harness」の通り、hooks や skills、サブエージェントなどモデル周辺の実装基盤全体を指します。その中で hook は公式 29 種類のライフサイクルイベントに任意の処理を差し込める仕組みで、本章ではその最も基本的な PreToolUse に絞って入門します。L1 と L2 は AI に「こうしてほしい」と指示する仕組みですが、L3 ハーネスは AI の動作を制御・拡張する設計分野です。今日はその中で「やってはいけないことを自動で防ぐ」用途を入口に体験します。
-->

---

# あなたのコード、無防備じゃありませんか？

> 🪞 AIに「このファイルを消して」と言われたら、どうしますか？

- AIは強力な道具 — しかし **誤操作のリスク** もある
- `rm -rf`（ファイルの一括削除）や `sudo`（管理者権限での実行）など、取り返しのつかないコマンドを実行する可能性
- **人間が毎回確認するのは現実的ではない**

> ⚡ Hookは、AIが危険な操作をする前に **自動で立ち止まらせる** 安全装置として機能します

<!--
AIは便利ですが、指示次第ではプロジェクトを破壊するコマンドも実行できてしまいます。「rm -rf」でファイルを一括削除したり、「sudo」で管理者権限を使ってシステム設定を変更したり。毎回人間が確認するのは非現実的です。そこで Hook の出番です。Hook は AI のライフサイクルイベントに任意の処理を発火させる広い仕組みですが、その代表的な用途のひとつが「AI が危険な操作を実行する前に自動的に止める安全装置」です。たった 1 本の設定で、あなたのコードを守れます。
-->

---

# Hookとは — AIのライフサイクルに割り込む仕組み

**Hook = AI のライフサイクルイベント (セッション開始 / プロンプト送信 / ツール実行前後 / 圧縮前 / 終了 など) に、任意の処理を発火させる仕組み**

- Claude Codeが **ツールを使う前** にチェック処理を挟める (本章のテーマ)
- Claude Codeが **ツールを使った後** に通知処理を挟める
- セッション開始時に資料を自動で渡す、終了時にログを残す、なども同じ仕組み
- **安全装置はそのうちの代表的な一用途**

> 💡 銀行のATMで「大金を引き出す前に暗証番号を確認する」のと同じ — 実行前に一旦止めて確認する用途は、Hook の使い道のひとつです

<!--
Hook の本質は「AI のライフサイクルイベントに、独自の処理を発火させる仕組み」です。ツール実行前後はもちろん、セッション開始、プロンプト送信時、コンテキスト圧縮の直前、終了時など、AI が動作する各タイミングに割り込めます。前章の 3階層モデルで言えば、Hook は L3 ハーネスを構成する公式機能のひとつで、AI の振る舞いを監視・拡張・制御するための窓口です。本章ではその代表用途である「ツール実行前の安全チェック」に絞りますが、Hook 自体は「安全装置」だけではなく、資料の自動注入や運用記録など幅広い用途を持つことを覚えておいてください。
-->

---

# この章で扱うイベント — **PreToolUse 1つだけ**

> 💡 まず安心情報: Hook には **公式で全 29 種類** のイベントがありますが、**初級編で覚えるのはこの 1 つだけ** です。

| イベント | タイミング | 代表的な用途 |
|----------|-----------|-------------|
| **PreToolUse** ★ | ツール実行の **前** | 危険なコマンドをブロック |

- 残り 28 種類のうち、本講座中級編で扱う代表例: **PostToolUse / SubagentStop / SessionStart / PreCompact / Notification / Stop** など
- 「他にも多様なタイミングで割り込める」とだけ知っておけば十分です — 全 29 種類を一度に覚える必要はありません

<!--
Claude Code の hook には公式で 29 種類のイベントがあります。これは前章の歴史で触れたとおり「公式仕様」です。本講座の初級編で深く学ぶのは PreToolUse 1 つだけ。残り 28 種類のうち、よく使う PostToolUse・SubagentStop・SessionStart・PreCompact・Notification・Stop などは中級編で扱いますので、ここで暗記する必要はありません。表を 1 行にしぼったのは「PreToolUse に集中しよう」という目印です。PreToolUse はツールが実行される「前」に割り込むイベントで、危険なコマンドをブロックするのに使います。ちなみに「SubagentStop」は a が小文字、これは公式表記なので大文字 A で書くと動きません — 中級編で扱うときに改めて触れます。
-->

---

# PreToolUse Hook — コマンド実行前のチェックポイント

**PreToolUse = ツールが実行される「直前」に検査を挟む仕組み**

```
AIがコマンドを生成
       ↓
  【PreToolUse Hook】← ここで検査！
       ↓
  安全 → 実行
  危険 → ブロック (STOP)
```

- AIが生成したコマンドを **実行前に検査**
- 危険なパターンに一致すれば **自動でブロック**
- 人間の確認なしに **瞬時に判断**

<!--
PreToolUse Hookの動きを図で示しました。AIがコマンドを生成すると、すぐに実行されるわけではありません。間にPreToolUse Hookが入ります。ここでコマンドの内容を検査し、安全ならそのまま実行、危険なら「STOP」でブロックします。人間がいちいち確認しなくても、瞬時に判断して防いでくれます。これが L3 ハーネスを使った安全制御の基本パターンです。
-->

---

# Before / After — Hookの有無でこう変わる

**Hookなし**:

- AIが `rm -rf /project` を生成 → **そのまま実行** → プロジェクト消滅
- 後から気づいても **取り返しがつかない**

**Hookあり**:

- AIが `rm -rf /project` を生成 → **Hookが検知** → チェックスクリプトが `STOP: 危険な操作を検知しました` と表示
- 実行される前に **自動ブロック** → プロジェクトは無事

> 🛡️ たった1本のHookで、致命的な事故を **未然に防げる**

<!--
Hookの有無で何が変わるか、極端な例で示します。Hookがなければ、AIが生成した危険なコマンドがそのまま実行されてしまい、プロジェクトが消滅する可能性があります。Hookがあれば、コマンドが実行される前に自動検知してブロック。「STOP: 危険な操作を検知しました」というメッセージが出て、実行は中止されます。たった 1 本の Hook で、致命的な事故を未然に防げるのです。これが L3 ハーネスの威力のひとつです。
-->

---

# 設定ファイルの構造 — 少しずつ組み立てる

**`.claude/settings.json`** — プロジェクト直下に **自分で新規作成する** ファイルです:

> 💡 まだ存在しない場合、`.claude/` フォルダを作り、その中に `settings.json` を作ります

**Step 1**: 一番外枠 — Hook設定の「入れ物」を作る:
```json
{ "hooks": { } }
```

**Step 2**: どのイベントに反応するか — PreToolUse（ツール実行前）を指定:
```json
{ "hooks": { "PreToolUse": [ ] } }
```

**Step 3**: どのツールに反応するか — `matcher` で Bash（コマンド実行）を指定:
```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash" } ] } }
```

**Step 4**: 実行する処理を追加 — 内側の `"hooks"` にチェックコマンドを書く（**外側 hooks = 設定の入れ物 / 内側 hooks = 実行リスト** と役割が違う点に注意。詳しい覚え方は下のコードのすぐ下に）:
```json
{
  "hooks": {                       // ← 外側 = 「Hook 設定全体の入れ物」
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [                 // ← 内側 = 「実行するコマンドのリスト」
          { "type": "command", "command": "bash scripts/pretool_check.sh" }
        ]
      }
    ]
  }
}
```

> 💡 **入れ子の `hooks` が2回出てくる理由**: 外側は「設定の入れ物」、内側は「実行リスト」。**役割が違うのに同じ単語** ですが、Claude Code の設定書式の決まりなので、初学者はまず「**外側＝箱・内側＝中身**」と覚えるだけでOKです。

- チェックスクリプトが **exit 2** を返すと **実行がブロックされます** (詳しい意味は次のスライドで)

<!--
Hookの設定は、プロジェクトの`.claude/settings.json`ファイルに書きます。段階的に組み立てると分かりやすいです。まず外枠の「hooks」入れ物を作り、次にイベントの「PreToolUse」を指定し、反応対象の「matcher」でBashツールを指定し、最後に実行するコマンドを書きます。外側の `hooks` は「設定全体の入れ物」、内側の `hooks` は「実行するコマンドのリスト」と役割が違いますが、Claude Codeの設定書式の決まりです。最初は「外側＝箱・内側＝中身」と単純に覚えれば十分です。
-->

---

# `exit` とは？ — スクリプトの「終了報告」

> Step 4 で `bash scripts/pretool_check.sh` を呼ぶと、スクリプトの結果は **数字で報告** されます。これが `exit コード` です。

- `exit` = **シェルスクリプトを終了するコマンド** (Unix の慣習)
- 直後の数字は「終了状況の報告」

| 数字 | 意味 | 由来 |
|------|------|------|
| **`exit 0`** | 「異常なし」 — そのまま実行を続ける | Unix 標準（成功 = 0）|
| `exit 1` | 「何らかのエラー」 | Unix 標準（汎用エラー）|
| **`exit 2`** | 「**危険検知 → 実行をブロック**」 + stderr にメッセージ出力 | **Claude Code 固有の PreToolUse BLOCK プロトコル** |

> 💡 **覚え方**: `exit 0` = 緑信号 / `exit 2` = 赤信号。本章はこの2つだけ覚えればOK。

> ⚠️ `exit 2 = ブロック` は Claude Code が PreToolUse hook 用に決めた取り決め。Unix 一般では「2」に固有の意味はありません — 混同しないように注意。

> 📝 上級の代替: stdout に `permissionDecision: "deny"` を含む JSON を返す方式もあります（中級編で扱います）

<!--
exitコマンドの意味をシェル一般とClaude Code固有に分けて整理しました。Unixでは「exit 0 = 成功」「それ以外 = 何らかのエラー」が慣習です。Claude Code はこの仕組みに乗って PreToolUse Hook で「exit 2 = 危険検知だからブロック、メッセージは stderr へ」という固有のプロトコルを定めています。初級編では exit 0 と exit 2 の 2 つだけ覚えれば本章のスクリプトは全て読めます。中級編では stdout に JSON で `permissionDecision: "deny"` を返す上級の代替方式も扱います。
-->

---

# `pretool_check.sh` の作り方 — 3ステップで組む

> Step 4 で指定した `bash scripts/pretool_check.sh` の **本体ファイル** を、プロジェクト直下の `scripts/` フォルダに新規作成します。

**Step A**: `scripts/` フォルダを作り、その中に `pretool_check.sh` という空ファイルを作成

**Step B**: シェルスクリプトの宣言と「**何もせず成功する**」最小骨格を書く:
```bash
#!/bin/bash    # ← このファイルが bash で動くと宣言
exit 0         # ← 何もせず「異常なし」で終了
```

**Step C**: 「危険なら止める」検査を追加。**Claude Code は hook に JSON を「標準入力 (stdin)」経由で渡す** ので、まず JSON を受け取って `tool_input.command` を取り出してから判定します（**コードの意味は次スライドの前提知識表で読み解きます — 今は形だけ眺めるのでOK**）:
```bash
#!/bin/bash
INPUT=$(cat)                                       # stdin から JSON を全部読み込む
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')  # コマンド文字列を取り出す
if echo "$COMMAND" | grep -q 'rm -rf'; then
  echo "STOP: 危険な操作を検知しました" >&2
  exit 2       # ← 危険検知 → ブロック
fi
exit 0         # ← 安全 → 実行を続ける
```

> 💡 ファイル作成後 **実行権限** を付けます: `chmod +x scripts/pretool_check.sh` (= **このファイルを実行できるように許可する** ためのコマンド・一度だけの作業)
>
> 💡 `jq` コマンドが必要です: 未インストールなら `sudo apt install jq` (Ubuntu) または `brew install jq` (macOS) で導入できます

<!--
settings.json とは別に、本体のチェックスクリプト pretool_check.sh を scripts/ フォルダに作ります。シェルスクリプトに馴染みがない方のために 3 段階に分けました。Step A で空ファイルを作り、Step B で「何もせず成功する」最小骨格を書き、Step C で検査を追加します。先頭の #!/bin/bash は「このファイルは bash で動かす」という宣言です。Claude Code の hook は JSON ペイロードを標準入力経由で渡すので、まず INPUT=$(cat) で受け取り、jq で .tool_input.command を取り出します。この受け取り方が公式の仕様で、これを使わないとコマンドの中身が取れません。最後に chmod +x で実行権限を付けるのを忘れないでください。jq コマンドが未導入の方は apt や brew で先にインストールしておきましょう。これで settings.json から呼び出されたときに動作します。
-->

---

# ブロック例 — 何を防ぐのか

よくある危険パターンと検知例:

| 危険パターン | 具体例 | 被害 |
|-------------|--------|------|
| 再帰削除 | `rm -rf /` | OS / プロジェクト全体を消去 |
| 特権実行 | `sudo`, `su` | システム設定を変更 |
| データ破壊 | `DROP TABLE` | データベースのテーブルを削除 |
| 強制push | `git push --force` | リモートの履歴を破壊 |

> 💡 これらを **数行のスクリプトで検知** できます。コードを読む前に、5つの前提知識を確認しましょう:

| 書き方 | 意味 |
|--------|------|
| `INPUT=$(cat)` | **標準入力 (stdin)** から JSON を全部読み取って `INPUT` 変数に入れる。Claude Code は hook に **JSON ペイロードを stdin 経由で渡す** のが公式仕様 |
| `jq -r '.tool_input.command'` | JSON から `.tool_input.command` フィールド (AI が実行しようとしたコマンド) を取り出す。`-r` は「クォートなしで生の文字列を返す」オプション |
| `\|` (パイプ) | 左のコマンドの出力を、右のコマンドに渡す仕組み |
| `grep -q` | 指定した文字列が含まれているかを調べるコマンド（`-q` は「結果を黙って判定する」オプション） |
| `if ... then ... fi` | 「もし〜なら〜する」の条件分岐。`fi` は `if` の終わりを示す（if を逆さにした文字） |
| `exit 数字` | スクリプトを終了し、数字を「結果の報告」として Claude Code に伝える (exit 2 = ブロック) |

```bash
# pretool_check.sh の中身（最小例）— 上の表を見ながら読んでみましょう:

#!/bin/bash
# Claude Code が JSON を stdin で渡してくるので、まずそれを受け取る
INPUT=$(cat)
# JSON から AI が実行しようとしたコマンドを取り出す
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

# COMMAND の中に「rm -rf」が含まれているか判定
if echo "$COMMAND" | grep -q 'rm -rf'; then
  echo "STOP: 危険な操作を検知しました" >&2  # 理由を stderr に出す
  exit 2  # ブロック（exit 2 = 「危険だから止まれ」という合図）
fi
exit 0    # 安全（そのまま実行）
```

> 💡 **このコードは「読めなくてもOK」です** — 表の説明を眺めて「stdin で受けて、jq でコマンドを取り出して、grep で判定してそう」と思えれば十分。コピペで動くので、中身を理解するのは後回しで構いません。

<!--
Hookが防ぐべき危険なパターンを4つ紹介します。再帰削除はプロジェクトやOS全体を消去してしまう致命的な操作。特権実行はシステム設定を変更してしまう危険性があります。データ破壊はデータベースのテーブルを削除。強制 push はリモートの履歴を破壊します。これらを、数行のシェルスクリプトで検知できるのが Hook の強みです。重要なポイントは、Claude Code の hook が **stdin 経由で JSON ペイロードを渡してくる** ことです。$1 や $CLAUDE_TOOL_INPUT といった引数や環境変数は公式仕様には存在しません — 必ず INPUT=$(cat) で受け取って jq で取り出します。これは公式仕様なので、コピペした後も覚えておくと中級編がスムーズです。L3 ハーネスはこのようなシンプルな検査で大きな安全性を実現します。
-->

---

# Hookの実行フローまとめ

```
1. ユーザーがプロンプトを入力
2. AIがツールの使用を判断（例: Bash で rm -rf を実行）
3. PreToolUse Hook が発動
4. Claude Code がチェックスクリプトに JSON を stdin で渡す
5. スクリプトが JSON から .tool_input.command を取り出して検査
6. 安全（exit 0）→ 実行継続
   危険（exit 2 + stderr メッセージ）→ ブロック + 警告表示
7. AIがブロック理由を受け取り、別の方法を検討
```

> Hookは **「検閲」ではなく「安全ネット」** — AIも理由を理解して別案を出す

<!--
Hookの全体フローを整理します。ユーザーのプロンプトに対して AI がツールを使おうとすると、PreToolUse Hook が発動します。このとき Claude Code は hook 用のスクリプトに JSON ペイロードを標準入力経由で渡します。スクリプトは JSON から .tool_input.command を取り出して検査し、安全なら exit 0 で実行継続、危険なら exit 2 + stderr メッセージでブロックします。重要なのは、ブロックされた後も AI は理由を受け取り、別の安全な方法を自動的に検討する点です。Hook は単に「禁止」するのではなく、AI により良い選択を促す安全ネットとして働きます。
-->

---

# 🖐️ ミニ演習 — 自分でHookを設定してみよう

**手順 (5分)**:

1. プロジェクト直下に `.claude/` フォルダを作る
2. その中に `settings.json` を作成し、以下を貼り付け:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash scripts/hook_demo.sh" }
        ]
      }
    ]
  }
}
```

3. `scripts/hook_demo.sh` を新規作成して以下を貼り付け、`chmod +x scripts/hook_demo.sh` で実行権限を付与:

```bash
#!/bin/bash
# Claude Code が stdin で JSON を渡してくるので受け取る
INPUT=$(cat)
# AI が実行しようとしたコマンドを取り出して標準エラーに表示
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
echo "[CHECK] $COMMAND" >&2
exit 0   # ブロックせず、観察だけして実行を許可
```

> 💡 `INPUT=$(cat)` で標準入力 (stdin) から JSON を全部読み取り、`jq` で `tool_input.command` フィールドを取り出します。**hook は stdin から JSON を受け取るのが公式仕様** — `$1` や独自の環境変数で取り出す方法は公式に存在しません。**コピペで動かない致命傷を避けるためにも、必ずこの形を使ってください**。

4. **新しいセッションを開始** (Claude Code 上で `/clear` を実行するか、ターミナルを一度終了して再度 `claude` で起動) して settings.json を読み直させる
5. Claude Codeに「現在のディレクトリのファイル一覧を表示して」と入力 → `[CHECK] ls -la` のようにコマンドが表示されれば **Hookが動いている証拠**

> 💡 この設定は「ブロックしない」安全な練習用です。まず「Hookが正しく反応しているか」を確認するのが目的です。本番のブロック設定（exit 2）は中級編で学びます。

<!--
ミニ演習です。settings.json と本体スクリプト hook_demo.sh の 2 ファイルを作って、hook が動くことを観察します。ポイントは hook_demo.sh の INPUT=$(cat) と jq の組み合わせ。これが公式仕様の「hook は stdin から JSON ペイロードを受け取る」を実装した最小コードです。$1 で受け取る書き方や $CLAUDE_TOOL_INPUT のような環境変数は公式にはなく、コピペしても動かないので必ずこの形を使ってください。設定を反映させるには /clear で新しいセッションを開始するか、ターミナルを一度終了して claude を再起動します。実行して「現在のディレクトリのファイル一覧を表示して」と頼んだとき [CHECK] ls -la のように表示されれば成功です。
-->

---

# 📚 まとめ — この章で学んだこと

**3つのポイント**:

1. **Hook = L3ハーネスの公式実装機能** — AI のライフサイクルイベント (公式 29 種類) に任意の処理を発火させ、動作を制御・拡張する仕組み
2. **PreToolUse Hook** — コマンド実行前に検査し、危険な操作を自動ブロック (exit 2 + stderr メッセージ)
3. **設定はシンプル** — `.claude/settings.json` + チェックスクリプト数行で安全装置が有効に。**hook へのデータ受け渡しは stdin 経由の JSON** が公式仕様

> 3階層モデルの全体像:
> **L1 プロンプト** + **L2 コンテキスト** + **L3 ハーネス (Agent = Model + Harness)** = 安心してAIに任せる基盤

<!--
まとめです。この章で学んだことを 3 つのポイントで整理します。Hook は L3 ハーネスを構成する公式機能のひとつで、AI のライフサイクルイベント、公式 29 種類のタイミングに任意の処理を発火させて動作を制御・拡張します。特に PreToolUse Hook は、コマンド実行前に検査を行い、危険な操作を exit 2 + stderr メッセージで自動ブロックします。設定は settings.json とチェックスクリプト数行でできますが、hook へのデータ受け渡しは標準入力 (stdin) 経由の JSON が公式仕様、という点だけは忘れないでください。ここまでで 3 階層モデルの全てを学びました。L1 プロンプト、L2 コンテキスト、L3 ハーネス。「Agent = Model + Harness」の通り、この 3 つが揃って初めて、安心して AI に作業を任せられる基盤が完成します。
-->

---

# 🚀 次のレクチャー予告 (第6章)

## **終章: 中級編への橋渡し** (25 min)

> 初級編で3つの武器を手に入れました。プロンプト、コンテキスト、ハーネス。
> これは「入り口」に過ぎません。

- 初級編の **学習到達点3点** を振り返る
- 中級編で学ぶ **本格的な自動化システム** の全体像
- 自分にとって **次に進むべきステップ** を判断する

<!--
次は最終章「中級編への橋渡し」です。ここまでで3階層モデルの全てを学びました。L1プロンプトで意図を伝え、L2コンテキストで知識を永続化し、L3ハーネスで安全性を確保する。この3つの武器が揃いました。しかし、これは「入り口」に過ぎません。最終章では、初級編の学習到達点を振り返り、中級編で学ぶ本格的な自動化システムの全体像を紹介します。あなたにとって次に進むべきステップを判断する材料になります。
-->

---

<!-- _class: cover -->

# 第5章 完了 🎓
## 次は終章「中級編への橋渡し」

<div class="meta">
✅ Hookとは何か (L3ハーネスの公式実装機能・29種類のライフサイクルイベント)<br>
✅ PreToolUse Hook の仕組みと役割<br>
✅ AI の危険操作を自動検知・ブロックする仕組み (exit 2 + stderr / stdin JSON 受取)<br><br>
<b>続けて終章をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この第5章で、3階層モデルの最後のピース「L3 ハーネス」の代表的な公式機能である Hook の仕組みを理解いただけたでしょうか。Hook は公式 29 種類のライフサイクルイベントに任意の処理を発火させる仕組みで、本章ではその中の PreToolUse を使ってコマンド実行前の検査を行い、危険な操作を exit 2 + stderr メッセージで自動ブロックする方法を学びました。hook へのデータ受け渡しは stdin 経由の JSON、ここだけはコピペが効かない部分なので忘れないでください。これで L1 プロンプト、L2 コンテキスト、L3 ハーネスの 3 層が揃い、安心して AI に作業を任せられる基盤が完成しました。次は最終章「中級編への橋渡し」で、これまでの学びを整理し、次のステップを確認します。
-->
