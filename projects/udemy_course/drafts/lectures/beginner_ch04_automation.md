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

# hookの入門
## AIの安全装置を作る

<div class="meta">
初級編 — 第4章 (約 30 min)<br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
講師: 村上誠治 (なぎなた)
</div>

<!--
スピーカーノート:
こんにちは。この章では「hook（フック）」という仕組みを学びます。hookは、AIがあなたのプロジェクトで作業する際に、危険な操作を自動的に検知してブロックする安全装置です。30分で、この仕組みを理解し、1本のhookを設定できるようになります。
-->

---

## 🎯 この 30 分で得られること

1. **hookとは何か** — AIのライフサイクルイベントに反応する仕組みを理解する
2. **PreToolUse hook の仕組み** — コマンド実行前の検査とブロックを理解する
3. **設定方法** — `.claude/settings.json` にhookを記述できる
4. **危険操作の自動検知** — AIが `rm -rf` や `sudo` を実行前にブロックする仕組みを説明できる

<!--
この章のゴールは4つです。まずhookが何かを理解し、次に最も重要なPreToolUse hookの仕組みを学び、実際に設定ファイルに書けるようになること。最後に、AIが危険なコマンドを実行する前に自動でブロックされる仕組みを自分の言葉で説明できることが到達点です。
-->

---

# あなたのAI、何でも実行してしまいませんか？

> 🪞 「AIに『このファイルを消して』と言われたら、どうしますか？」

- AIは指示に従って **どんなコマンドも実行** する可能性がある
- `rm -rf` / `sudo` / `DROP TABLE` — 元に戻せない操作も
- 人間が常に監視していれば安全だが... **ずっと見ていられますか？**

> ⚡ hook は、AIが危険な操作をする前に **自動で立ち止まらせる**

<!--
AIは便利ですが、言われたことを何でも実行してしまうリスクがあります。ファイルを消すコマンド、管理者権限で実行するコマンド、データベースのテーブルを削除するコマンド。これらは人間が承認すれば問題ありませんが、24時間ずっと画面を見ているわけにはいきません。そこでhookの出番です。hookは、AIが危険な操作を実行する前に自動で「ストップ」をかけます。
-->

---

# hookとは — AIのライフサイクルイベントに反応する仕組み

```
  AIの動作        hookが反応するタイミング
  ─────────────────────────────────
  セッション開始  → SessionStart
  ツール使用前    → PreToolUse    ← 今回学ぶ
  ツール使用後    → PostToolUse
  作業完了        → Stop
```

- **hook = イベントに反応して自動実行されるスクリプト**
- AIの動作の「前」や「後」に **独自の処理を挟み込む** 仕組み
- Web開発のミドルウェアと同じ考え方

<!--
hookとは、AIが動くタイミングで自動的に反応する仕組みです。AIがセッションを開始した時、ツールを使う前、ツールを使った後、作業が終了した時。これら全てにhookを設定できます。今回はこの中で最も重要な「PreToolUse」を学びます。PreToolUseは、AIがツールを使う「直前」に実行されるため、危険な操作を未然に防げます。
-->

---

# 7つのイベント種類

| イベント | タイミング | 代表的な用途 |
|---------|-----------|-------------|
| **SessionStart** | セッション開始時 | 環境確認・初期設定 |
| **PreToolUse** | ツール使用前 | **危険操作のブロック** |
| **PostToolUse** | ツール使用後 | ログ記録・通知 |
| **Notification** | 通知送信時 | 通知のカスタマイズ |
| **Stop** | 作業完了時 | 最終チェック |
| **SubagentStop** | サブエージェント完了時 | 結果の検証 |
| **UserPromptSubmit** | ユーザー入力時 | 入力の事前検証 |

> 💡 この章では **PreToolUse** の1本だけ解説。18本の全網羅は中級編で。

<!--
Claude Codeには7つのイベント種類があります。今回はPreToolUseに絞って解説します。PreToolUseはAIがツールを使う直前に発火するため、「この操作は安全か？」を検査するのに最適です。他のイベントも便利ですが、まずは1本で確実に安全を確保することが重要です。残りのイベントと18本のhook設定は中級編で深く学びます。
-->

---

# PreToolUse hook の仕組み

```
  AIがコマンドを実行しようとした
          │
          ▼
  ┌─────────────────────┐
  │  PreToolUse hook    │
  │  コマンドを検査      │
  │  危険パターン？      │
  └────────┬────────────┘
           │
     ┌─────┴─────┐
     │           │
   安全        危険
     │           │
  実行継続   ブロック＋警告
```

- AIがコマンドを実行する **直前** に自動検査
- 危険パターンにマッチ → **実行をブロック** して警告を表示
- 安全 → そのまま実行

<!--
PreToolUse hookの仕組みを図で示しました。AIがコマンドを実行しようとすると、まずhookがそのコマンドを検査します。「rm -rf」や「sudo」などの危険パターンにマッチした場合、実行をブロックし、AIに警告メッセージを表示します。安全なコマンドであれば、何もせずにそのまま実行されます。人間がいちいち確認しなくても、hookが自動で門番を務めてくれるイメージです。
-->

---

# 設定ファイルの構造

**ファイル**: `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash scripts/pretool_check.sh"
      }
    ]
  }
}
```

- **hooks** — hook設定のルートキー
- **PreToolUse** — イベント名
- **matcher** — どのツールに反応するか（`Bash` = シェルコマンド実行時）
- **command** — 実行する検査スクリプトのパス

<!--
設定は`.claude/settings.json`に書きます。このファイルはプロジェクトのルートディレクトリにある`.claude`フォルダの中に配置します。PreToolUseイベントに対して、Bashツール（シェルコマンド）が使われる前に`pretool_check.sh`というスクリプトを実行するよう設定しています。このスクリプトの中で危険なコマンドパターンを検査します。
-->

---

# 検査スクリプトの中身（簡易版）

```bash
#!/bin/bash
# pretool_check.sh — AIの安全装置

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command')

# 危険パターンを検知
if echo "$CMD" | grep -qE 'rm -rf|sudo|DROP TABLE'; then
  echo "BLOCKED: 危険な操作を検知しました"
  exit 1    # exit 1 = ブロック
fi

exit 0      # exit 0 = 許可
```

- **exit 0** → 安全、実行を許可
- **exit 1** → 危険、実行をブロック
- AIはブロック理由を受け取り、別の方法を探る

<!--
検査スクリプトの中身はシンプルです。AIが実行しようとしたコマンドを受け取り、危険なパターンが含まれていないかgrepで確認します。マッチしたら「BLOCKED」と表示してexit 1でブロック。マッチしなければexit 0で許可します。ブロックされたAIは、その理由を受け取り、安全な別の方法を探ります。たったこれだけのコードで、あなたのプロジェクトを守れます。
-->

---

# ブロック例 — 実際に何が防げるか

| 危険なコマンド | 内容 | hookの反応 |
|--------------|------|-----------|
| `rm -rf /` | OS全体を削除 | **BLOCKED** |
| `sudo apt install ...` | 管理者権限で操作 | **BLOCKED** |
| `DROP TABLE users` | DB テーブル削除 | **BLOCKED** |
| `git push --force` | リモート履歴破壊 | **BLOCKED** |
| `curl | bash` | リモートコード実行 | **BLOCKED** |

> 💡 これらは実際の開発現場で **起こり得る事故**。hookなしでは防げない。

<!--
実際のブロック例です。OSを削除するコマンド、管理者権限での操作、データベースのテーブル削除、リモートリポジトリの強制上書き、リモートコードの実行。いずれも人間が意図せずAIに実行させると取り返しがつかない結果になります。hookがあれば、これら全てを自動的にブロックできます。実際の開発現場でも、hookの有無がデータ損失を防ぐ決定的な差になります。
-->

---

# Before / After — hookなし vs hookあり

**hookなし**:
1. AIが `rm -rf project/` を実行
2. ファイルが消える
3. 人間が気づく → **もう遅い**

**hookあり**:
1. AIが `rm -rf project/` を実行しようとする
2. PreToolUse hook が検知 → **BLOCKED**
3. AIが警告を受け取り、安全な方法に切り替え
4. 人間は後でログで確認できる

> ✅ hook = **事故が起きる前に防ぐ** 仕組み

<!--
hookの有無で何が違うかを比較します。hookなしの場合、AIが危険なコマンドを実行してしまい、ファイルが消えた後に人間が気づくことになります。取り返しはつきません。一方、hookありの場合、実行前にブロックされるため、何も失われません。AIはブロック理由を受け取り、自ら安全な代替手段を探ります。これが「事故が起きる前に防ぐ」hookの価値です。
-->

---

# 第4章のまとめ

**学習到達点の確認**:

1. ✅ **hookとは** — AIのライフサイクルイベントに反応する仕組み
2. ✅ **PreToolUse hook** — コマンド実行前に検査し、危険ならブロック
3. ✅ **設定方法** — `.claude/settings.json` にhookを記述
4. ✅ **自動検知** — `rm -rf` / `sudo` / `DROP TABLE` 等を自動ブロック

> 🎓 hookは、あなたとAIの **信頼の土台** です

<!--
この章で学んだことを振り返りましょう。hookはAIのライフサイクルイベントに反応する仕組みで、PreToolUse hookはコマンド実行前に検査して危険な操作をブロックします。設定はsettings.jsonに書くだけで、rm -rfやsudoなどの危険なコマンドを自動検知できます。hookがあることで、AIを安心して自律的に働かせることができます。これが信頼の土台です。
-->

---

# 🚀 次のレクチャー予告 (第5章)

## **MCP 接続入門 — AIの記憶を拡張する** (30 min)

> セッションを終えるたびに記憶がリセットされていたらどうでしょう？

- MCP（Model Context Protocol）とは何か
- AIの記憶をセッションを跨いで引き継ぐ仕組み
- Before / After 比較 — MCPなし vs MCPあり

📌 第5章で、AIの **記憶の永続化** に挑みます。

<!--
次は第5章「MCP接続入門」です。これまでの章では、AIとのセッションを終えると記憶がリセットされるという暗黙の前提がありました。MCPを使うと、AIの記憶をセッションを超えて引き継げるようになります。hookで安全性を確保した上で、MCPでAIの能力を拡張する。この2つが揃うと、AI開発の基盤が完成します。
-->

---

<!-- _class: cover -->

# 第4章 完了 🎓
## 次は第5章「MCP 接続入門 — AIの記憶を拡張する」

<div class="meta">
✅ hookとは何か（AIのライフサイクルイベント）<br>
✅ PreToolUse hookの仕組みと設定方法<br>
✅ AIの危険操作を自動検知・ブロックする仕組み<br>
✅ 設定ファイルの構造と記述方法<br><br>
<b>続けて第5章をお楽しみください</b>
</div>

<!--
第4章は以上です。hookという安全装置の仕組みを理解いただけたでしょうか。PreToolUse hookは、たった1本のスクリプトでAIの危険な操作を未然に防げる強力な仕組みです。次の第5章では、AIの記憶を拡張するMCPという仕組みを学びます。安全装置と記憶の拡張、この2つが揃えばClaude Codeを本格的に活用する準備が整います。続けて第5章をご覧ください。
-->
