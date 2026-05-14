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

# 「気がついたら消されてた」を防ぐ — Hook で作る AI の最後の砦
## AIの安全装置を作る

<div class="meta">
第5章 (約 30 min) [L3 ハーネス入門]<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
</div>

<!--
スピーカーノート:
この第5章では、Claude Code の「Hook」という仕組みを学びます。前章で 3 階層モデルの L3 ハーネスが Anthropic 公式の概念 (Agent = Model + Harness) であり、hook はその実装基盤を構成する公式機能の一つだと学びました。本章ではその hook の最も基本的なイベントである PreToolUse を実際に使い、AI が作業する際に危険な操作を自動的に検知してブロックする安全装置を 30 分で組み立てます。まずは「なぜそれが必要なのか」を、実際の事故例から確認しましょう。
-->

---

# 🚨 AIに「掃除して」と頼んだら、プロジェクトが消えた

> 「不要なファイルを整理して」と頼んだ瞬間、AI が `rm -rf .` を実行 — **プロジェクト全消失**。
> ChatGPT 普及以降、業界で実際に報告されているエージェント暴走事故の典型形です。

- AI は強力だが、**自律性が高まるほど誤操作リスクも増大** (前章 L3 ハーネス誕生の動機そのもの)
- `rm -rf` (一括削除) や `sudo` (管理者権限実行) を毎回人間が「実行していい?」と確認するのは **非現実的**
- 必要なのは「AI が危険な操作をする前に **自動で立ち止まらせる仕組み**」 = 本章で作る **Hook**

**この 30 分で得られること**:
1. **Hookとは何か** — AI のライフサイクルイベントに任意の処理を発火させる仕組みを説明できる
2. **PreToolUse Hook** の仕組みと役割を理解し、設定例を読める
3. AI の危険操作を **自動検知・ブロックする仕組み** を実際に設定できる

<!--
冒頭でいきなり受講者の痛点を突きます。AI が `rm -rf` でプロジェクトを消す事故は架空ではなく、エージェント自律化が進む 2024〜2025 年に各社で報告されてきた典型例です。前章で L3 ハーネスが誕生した理由として「AI 暴走事故」を挙げましたが、本章はその防衛策を実装する回です。学習目標も 3 つに絞り、ゴールが明確に見えるようにしました。Hook が「何のためにあるのか」を最初の 1 枚で腹落ちさせるのが狙いです。
-->

---

# 前章からの続き — L3 ハーネスの代表機能を実装する

> 前章 (第4章) で確認した到達点:
> **L1 プロンプト** = 人間の意図を伝える
> **L2 コンテキスト** = プロジェクト知識を永続化する
> **L3 ハーネス** = hooks/skills/sub-agents 等で AI を制御・拡張する周辺基盤
> (Anthropic 公式: **Agent = Model + Harness** / Engineering Blog 2025-11)

- L1 と L2 は **指示を与える** 仕組み
- L3 ハーネスは **動作を監視・制御・拡張** する設計分野で、その中心実装の一つが **Hook**
- 公式 hook イベントは **全 29 種類**。本章は最も基本となる **PreToolUse** に絞って入門する

> 💡 本章の Hook = **L3 ハーネスの公式実装機能 / その入口にあたる PreToolUse**

<!--
前章で学んだ 3 階層モデルを 1 行ずつ再掲し、L3 ハーネスの中で本章が扱う位置を明示します。「Agent = Model + Harness」は Anthropic 公式の定義であり、ハーネスは hooks・skills・サブエージェント・コンテキストポリシー・回復経路など、モデルを実運用で信頼できる形にする実装基盤全体を指します。Hook はその中の公式実装機能のひとつで、29 種類のライフサイクルイベントに任意の処理を差し込めます。本章ではそのうち PreToolUse 1 つに絞ります — 全部覚える必要はない、と最初に安心情報を出しておきます。
-->

---

# Hookとは — AIのライフサイクルに割り込む仕組み

**Hook = AI のライフサイクルイベント (セッション開始 / プロンプト送信 / ツール実行前後 / 圧縮前 / 終了 など) に、任意の処理を発火させる仕組み**

- Claude Code が **ツールを使う前** にチェック処理を挟める (本章のテーマ)
- セッション開始時に資料を自動で渡す、終了時にログを残す、なども同じ仕組み
- **「安全装置」はそのうちの代表的な一用途**にすぎない

| イベント | タイミング | 代表的な用途 |
|----------|-----------|-------------|
| **PreToolUse** ★ | ツール実行の **前** | 危険なコマンドをブロック (本章で扱う) |

- Hook は公式で **全 29 種類**。本章で覚えるのは **PreToolUse 1 つだけ** で十分
- 残り 28 種類 (PostToolUse / SubagentStop / SessionStart / PreCompact / Notification / Stop など) は応用編で扱う

> 💡 銀行 ATM で「大金を引き出す前に暗証番号を確認する」のと同じ — 実行前に一旦止めて確認する用途は Hook の使い道のひとつ

<!--
Hook の本質を正しく定義します。「AI の動きに制限をかける仕組み」と狭く捉えるのは誤りで、本質は「AI のライフサイクルイベントに任意処理を発火させる広義の機構」です。安全装置はそのうちの代表的な一用途。公式で全 29 種類のイベントがあることを明示し、本章では PreToolUse 1 つに集中することを宣言します。残り 28 種類のうちよく使うイベントを名前だけ紹介して安心情報にしますが、「SubagentStop」は a が小文字、これは公式表記なので大文字 A で書くと動きません — 応用編で扱うときに改めて触れます。
-->

---

# PreToolUse Hook の動き — Before / After

**PreToolUse = ツールが実行される「直前」に検査を挟む仕組み**

```
AIがコマンドを生成
       ↓
  【PreToolUse Hook】← ここで検査！
       ↓
  安全 → 実行
  危険 → ブロック (STOP)
```

**Hookなし**: AI が `rm -rf /project` を生成 → そのまま実行 → **プロジェクト消滅**
**Hookあり**: AI が `rm -rf /project` を生成 → Hook が検知 → `STOP: 危険な操作を検知しました` → **未然に防止**

> 🛡️ たった 1 本の Hook で、致命的な事故を未然に防げる — これが L3 ハーネスの威力

<!--
PreToolUse の動きを図と Before/After で 1 枚にまとめました。AI が生成したコマンドはまっすぐ実行されるわけではなく、PreToolUse Hook が間に入って検査します。安全なら通過、危険ならブロック。人間がいちいち判断しなくても、瞬時に止められるのが価値です。冒頭の痛点フックで提示した `rm -rf` 事故も、この仕組み 1 本で未然に防げる。L3 ハーネスの効き目を最初に体感してもらいます。
-->

---

# 設定ファイルの構造 — `.claude/settings.json`

**`.claude/settings.json`** をプロジェクト直下に **自分で新規作成** します。`.claude/` フォルダがなければ作る:

**Step 1**: 外枠の入れ物 → **Step 2**: イベントを指定 → **Step 3**: 対象ツールを `matcher` で指定 → **Step 4**: 実行コマンドを書く

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

> 💡 **`hooks` が 2 回出てくる理由**: 外側は「設定の入れ物」、内側は「実行リスト」。役割が違うのに同じ単語だが、Claude Code 設定書式の決まり。初学者はまず「**外側＝箱・内側＝中身**」と覚えれば OK。

> 💡 設定の意味: 「**Bash ツールを使う前に `bash scripts/pretool_check.sh` を実行せよ**」を JSON で記述しているだけ

<!--
Hook の設定は `.claude/settings.json` に書きます。外側 → イベント → matcher → 内側コマンド、の 4 段を 1 枚にまとめました。入れ子の `hooks` キーワードが 2 回出てくるのが初学者の最大のつまずきポイントですが、「外側＝箱、内側＝中身」と覚えれば十分です。意味は単純で「Bash ツールを使う前に pretool_check.sh を実行せよ」と JSON で書いているだけ。読み解ければ怖くないことを伝えます。
-->

---

# `exit` と `>&2` — スクリプトの「結果報告」と「エラー出力」

スクリプトの実行結果は **数字で報告** されます。これが `exit` コード。

- `exit` = シェルスクリプトを終了するコマンド (Unix の慣習)。直後の数字が「終了状況の報告」

| 数字 | 意味 | 由来 |
|------|------|------|
| **`exit 0`** | 「異常なし」 — そのまま実行を続ける | Unix 標準（成功 = 0）|
| `exit 1` | 「何らかのエラー」 | Unix 標準（汎用エラー）|
| **`exit 2`** | 「**危険検知 → 実行をブロック**」 + stderr にメッセージ出力 | **Claude Code 固有の PreToolUse BLOCK プロトコル** |

- **`>&2`** (stderr = 標準エラー出力にリダイレクト): `echo "メッセージ" >&2` で、メッセージを「通常の出力 (stdout)」ではなく「エラー専用の出力 (stderr)」へ流す書き方。Claude Code は `exit 2` 時の **stderr の中身を「ブロック理由」として AI に渡す**

> 💡 **覚え方**: `exit 0` = 緑信号 / `exit 2` = 赤信号。本章はこの 2 つだけ覚えれば OK。

> ⚠️ `exit 2 = ブロック` は Claude Code 固有の取り決め。Unix 一般では「2」に固有の意味はない — 混同しないように注意。

<!--
exit コードと stderr リダイレクトをまとめて整理します。Unix では「exit 0 = 成功」「それ以外 = エラー」が慣習。Claude Code はこの仕組みに乗って、PreToolUse Hook で「exit 2 = 危険検知だからブロック、メッセージは stderr へ」という固有のプロトコルを定めました。`>&2` は「標準エラー出力にリダイレクト」する書き方で、Claude Code は exit 2 時の stderr の内容を AI 側に「ブロック理由」として渡します。だから AI は理由を理解して別案を出せるのです。初級ではここまで覚えれば本章のスクリプトは全て読めます。上級の代替 (stdout に JSON で permissionDecision を返す方式) は応用編で扱います。
-->

---

# `pretool_check.sh` の作り方 — 3 ステップ

> Step 4 で指定した `bash scripts/pretool_check.sh` の **本体ファイル** を、`scripts/` フォルダに新規作成します。

**Step A**: `scripts/` フォルダを作り、その中に `pretool_check.sh` という空ファイルを作成

**Step B**: シェルスクリプトの宣言と「何もせず成功する」最小骨格:
```bash
#!/bin/bash    # ← このファイルが bash で動くと宣言
exit 0         # ← 何もせず「異常なし」で終了
```

**Step C**: 「危険なら止める」検査を追加。**Claude Code は hook に JSON を「標準入力 (stdin)」経由で渡す** ので、stdin で受け取って `tool_input.command` を取り出してから判定する:
```bash
#!/bin/bash
INPUT=$(cat)                                            # stdin から JSON を全部読み込む
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')  # JSON からコマンド文字列を取り出す
if echo "$COMMAND" | grep -q 'rm -rf'; then
  echo "STOP: 危険な操作を検知しました" >&2  # 前スライドで触れた stderr へ理由を出す
  exit 2       # ← 危険検知 → ブロック
fi
exit 0         # ← 安全 → 実行を続ける
```

> 💡 作成後 **実行権限** を付与: `chmod +x scripts/pretool_check.sh` (一度だけ)
> 💡 `jq` 未導入なら `sudo apt install jq` (Ubuntu) または `brew install jq` (macOS)
> ⚠️ `$1` や `$CLAUDE_TOOL_INPUT` で受け取る書き方は **公式仕様に存在せず、コピペしても動かない**。必ず `INPUT=$(cat)` + `jq` 方式で。

<!--
settings.json とは別に、本体のチェックスクリプトを scripts/ フォルダに作ります。3 段階に分けたのは、シェルスクリプト未経験者でも追えるようにするためです。最重要ポイントは Step C の最初の 2 行 — `INPUT=$(cat)` で標準入力から JSON ペイロードを受け取り、jq で `.tool_input.command` を取り出す。これが Claude Code 公式の仕様で、これを使わないとコマンドの中身が取れません。`$1` や独自環境変数で受け取る記事が世にありますが公式には存在せず、コピペしても動きません — ここは絶対に間違えないように強調しておきます。jq 未導入の方は apt や brew で先にインストールしてください。
-->

---

# ブロック例 — 何を防ぐのか + コードの前提知識

よくある危険パターンと検知例:

| 危険パターン | 具体例 | 被害 |
|-------------|--------|------|
| 再帰削除 | `rm -rf /` | OS / プロジェクト全体を消去 |
| 特権実行 | `sudo`, `su` | システム設定を変更 |
| データ破壊 | `DROP TABLE` | データベースのテーブルを削除 |
| 強制 push | `git push --force` | リモートの履歴を破壊 |

前スライドのコードを読み解く前提知識:

| 書き方 | 意味 |
|--------|------|
| `INPUT=$(cat)` | **stdin から JSON を全部読み取って** `INPUT` 変数に入れる。Claude Code は hook に **JSON ペイロードを stdin 経由で渡す** のが公式仕様 |
| `jq -r '.tool_input.command'` | JSON から `.tool_input.command` (AI が実行しようとしたコマンド) を取り出す。`-r` は生の文字列を返す |
| `\|` (パイプ) | 左の出力を右に渡す |
| `grep -q` | 文字列が含まれているかを判定（`-q` は静かに） |
| `if ... then ... fi` | 条件分岐 (`fi` は `if` の終わり) |

> 💡 **コードは「読めなくても OK」** — 表を眺めて「stdin で受けて、jq で取り出して、grep で判定してそう」と思えれば十分。コピペで動く。

<!--
Hook が防ぐべき危険なパターンを 4 つ示します。再帰削除・特権実行・データ破壊・強制 push は実務でも頻出の事故源です。下半分で前スライドのコードを読み解く前提知識を表にまとめました。特に最初の 2 行 — `INPUT=$(cat)` と `jq -r '.tool_input.command'` — が公式仕様の核心です。シェルスクリプトに馴染みがなくても、表を見ながら「stdin で受けて、jq で取り出して、grep で判定してそう」と眺めれば十分。コードを暗記する必要はなく、コピペで動くことを保証します。
-->

---

# Hook の実行フローまとめ

```
1. ユーザーがプロンプトを入力
2. AI がツールの使用を判断（例: Bash で rm -rf を実行）
3. PreToolUse Hook が発動
4. Claude Code がチェックスクリプトに JSON を stdin で渡す
5. スクリプトが JSON から .tool_input.command を取り出して検査
6. 安全（exit 0）→ 実行継続
   危険（exit 2 + stderr メッセージ）→ ブロック + 警告表示
7. AI がブロック理由 (stderr の内容) を受け取り、別の方法を検討
```

> Hook は **「検閲」ではなく「安全ネット」** — AI も理由を理解して別案を出す

<!--
全体フローを 7 ステップで整理します。ユーザーのプロンプトに対して AI がツールを使おうとすると、PreToolUse Hook が発動。Claude Code は hook 用スクリプトに JSON ペイロードを stdin で渡し、スクリプトは jq で `.tool_input.command` を取り出して検査します。安全なら exit 0 で実行継続、危険なら exit 2 + stderr メッセージでブロック。重要なのは、ブロックされた後も AI は stderr の内容を「ブロック理由」として受け取り、別の安全な方法を自動的に検討する点。Hook は単に「禁止」する仕組みではなく、AI により良い選択を促す「安全ネット」として働きます。
-->

---

# 🖐️ ミニ演習 — 自分で Hook を設定してみよう

**手順 (5 分・ブロックしない観察用)**:

1. プロジェクト直下に `.claude/settings.json` を作成:
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "bash scripts/hook_demo.sh" } ] }
    ]
  }
}
```

2. `scripts/hook_demo.sh` を作成 → `chmod +x scripts/hook_demo.sh`:
```bash
#!/bin/bash
INPUT=$(cat)                                            # stdin から JSON を読む
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')  # コマンド文字列を取り出す
echo "[CHECK] $COMMAND" >&2                             # stderr に観察ログを表示
exit 0                                                   # ブロックせず通す
```

3. **新しいセッションを開始** (`/clear` でセッション再起動、またはターミナル終了→`claude` 再起動) して settings.json を読み直させる
4. 「現在のディレクトリのファイル一覧を表示して」と入力 → `[CHECK] ls -la` のように表示されれば **Hook が動いている証拠**

> 💡 この設定は exit 0 = 「ブロックしない」安全な練習用。本番のブロック設定 (exit 2) は応用編で扱う。
> ⚠️ `$1` や独自環境変数で取り出す書き方は **公式に存在しない**。必ず `INPUT=$(cat)` + `jq` の形を使うこと。

<!--
ミニ演習です。settings.json と本体スクリプト hook_demo.sh の 2 ファイルを作って、hook が動くことを観察します。ポイントは hook_demo.sh の `INPUT=$(cat)` と `jq` の組み合わせ。これが公式仕様「hook は stdin から JSON ペイロードを受け取る」を実装した最小コードです。`$1` で受け取る書き方や `$CLAUDE_TOOL_INPUT` のような環境変数は公式にはなく、コピペしても動かない致命傷ゆえ必ずこの形を使ってください。設定を反映させるには `/clear` で新しいセッションを開始するか、ターミナルを一度終了して `claude` を再起動します。「現在のディレクトリのファイル一覧を表示して」と頼んだとき `[CHECK] ls -la` のように表示されれば成功です。
-->

---

# 📚 まとめ + 次のステップ

**この章で学んだ 3 つのポイント**:

1. **Hook = L3 ハーネスの公式実装機能** — AI のライフサイクルイベント (公式 29 種類) に任意の処理を発火させ、動作を制御・拡張する仕組み。「安全装置」はその代表的な一用途
2. **PreToolUse Hook** — コマンド実行前に検査し、危険な操作を自動ブロック (**`exit 2` + stderr メッセージ** で AI にブロック理由を渡す)
3. **設定はシンプル** — `.claude/settings.json` + チェックスクリプト数行で完成。**hook へのデータ受け渡しは stdin 経由の JSON** が公式仕様 (`INPUT=$(cat)` + `jq`)

> **3 階層モデルの全体像**:
> **L1 プロンプト** + **L2 コンテキスト** + **L3 ハーネス (Agent = Model + Harness)** = 安心して AI に任せる基盤

**次の章 (第6章 終章)**: これまでの 3 つの武器を振り返り、より進んだ自動化システムへの道筋を確認する。

<!--
まとめです。3 つのポイントで整理しました。Hook は L3 ハーネスを構成する公式機能のひとつで、AI のライフサイクル 29 種類のイベントに任意の処理を発火させて動作を制御・拡張します。PreToolUse Hook はコマンド実行前に検査し、危険な操作を exit 2 + stderr メッセージで自動ブロック。設定は settings.json とチェックスクリプト数行で完成しますが、hook へのデータ受け渡しは標準入力 (stdin) 経由の JSON が公式仕様で `INPUT=$(cat)` + `jq` の組み合わせを必ず使う、ここだけは忘れないでください。これで 3 階層モデルの全てを学び終わりました。「Agent = Model + Harness」の通り、この 3 つが揃って初めて、安心して AI に作業を任せられる基盤が完成します。次は終章で全体を振り返り、次のステップを確認します。
-->

---

<!-- _class: cover -->

# 第5章 完了 🎓
## 次は終章「次の段階への橋渡し」

<div class="meta">
✅ Hook とは何か (L3 ハーネスの公式実装機能・29 種類のライフサイクルイベント)<br>
✅ PreToolUse Hook の仕組みと役割<br>
✅ AI の危険操作を自動検知・ブロックする仕組み (exit 2 + stderr / stdin JSON 受取)<br><br>
<b>続けて終章で全体を整理しましょう</b>
</div>

<!--
ご視聴ありがとうございました。この第 5 章で、3 階層モデルの最後のピース「L3 ハーネス」の代表的な公式機能である Hook の仕組みを理解いただけたでしょうか。Hook は公式 29 種類のライフサイクルイベントに任意の処理を発火させる仕組みで、本章ではその中の PreToolUse を使ってコマンド実行前の検査を行い、危険な操作を exit 2 + stderr メッセージで自動ブロックする方法を学びました。hook へのデータ受け渡しは stdin 経由の JSON、ここだけはコピペが効かない部分なので忘れないでください。これで L1 プロンプト、L2 コンテキスト、L3 ハーネスの 3 層が揃い、安心して AI に作業を任せられる基盤が完成しました。次は終章で全体を整理し、より進んだ自動化への道筋を確認します。
-->
