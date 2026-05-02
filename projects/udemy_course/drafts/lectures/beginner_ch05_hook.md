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
初級編 — 第5章 (約 30 min)<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
講師: 村上誠治 (なぎなた)
</div>

<!--
スピーカーノート:
こんにちは、講師の村上誠治、ニックネームでは「なぎなた」と申します。この第5章では、Claude Codeの「Hook」という仕組みを学びます。Hookは、AIがあなたのプロジェクトで作業する際に、危険な操作を自動的に検知してブロックする安全装置です。30分で、その仕組みと設定方法をしっかり理解しましょう。
-->

---

## 🎯 この 30 分で得られること

1. **Hookとは何か** — AIのライフサイクルイベントに反応する仕組みを説明できる
2. **PreToolUse Hook** の仕組みと役割を理解する
3. AIの危険操作を **自動検知・ブロックする仕組み** を説明できる

<!--
この章の目標は3つです。まずHookが何かを理解し、次に最も重要なPreToolUse Hookの仕組みを学び、最終的に「AIが危険な操作をする前に自動で止める仕組み」を自分の言葉で説明できるようになります。讲座全体を通して一貫するテーマは「安全」です。
-->

---

# あなたのコード、無防備じゃありませんか？

> 🪞 AIに「このファイルを消して」と言われたら、どうしますか？

- AIは強力な道具 — しかし **誤操作のリスク** もある
- `rm -rf` や `sudo` など、取り返しのつかないコマンドを実行する可能性
- **人間が毎回確認するのは現実的ではない**

> ⚡ Hookは、AIが危険な操作をする前に **自動で立ち止まらせる** 安全装置です

<!--
AIは便利ですが、指示次第ではプロジェクトを破壊するコマンドも実行できてしまいます。「rm -rf」でファイルを一括削除したり、「sudo」でシステム設定を変更したり。毎回人間が確認するのは非現実的です。そこでHookの出番です。Hookは、AIが危険な操作を実行する前に自動的に止めてくれる安全装置。たった1本の設定で、あなたのコードを守れます。
-->

---

# Hookとは — AIのライフサイクルに反応する仕組み

**Hook = AIの行動の前後に割り込むプログラム**

- Claude Codeが **ツールを使う前** にチェック処理を挟める
- Claude Codeが **ツールを使った後** に通知処理を挟める
- これにより **AIの振る舞いを監視・制御** できる

> 💡 Web開発の「ミドルウェア」や「イベントリスナー」と同じ考え方

<!--
Hookの本質は「AIの行動の前後に割り込む仕組み」です。Claude Codeがファイルを読む、コマンドを実行する、ファイルを書く、こうした操作の前後に独自の処理を挟めます。Web開発経験者には「ミドルウェア」や「イベントリスナー」と言うとイメージしやすいでしょう。AIの振る舞いを監視し、制御するための窓口がHookです。
-->

---

# 7つのイベント種類

| イベント | タイミング | 代表的な用途 |
|----------|-----------|-------------|
| **PreToolUse** | ツール実行の **前** | 危険なコマンドをブロック |
| **PostToolUse** | ツール実行の **後** | 実行結果のログ記録 |
| **Notification** | AIが通知を送る時 | 外部サービスへの連携 |
| **Stop** | AIの応答が終了した時 | 作業完了の通知 |
| **SubAgentStop** | サブエージェント終了時 | 並列作業の完了監視 |
| **SessionStart** | セッション開始時 | 環境チェック・初期化 |
| **PreCompact** | コンテキスト圧縮前 | 重要情報の保存 |

> 初級編で押さえるべきは **PreToolUse** の1つだけ

<!--
Claude Codeには7つのイベント種類があります。今回の初級編で深く学ぶのは「PreToolUse」の1つだけです。これはツールが実行される「前」に割り込むイベントで、危険なコマンドをブロックするのに使います。残りの6つは、より高度な自動化に使うもので、中級編で詳しく解説します。まずはPreToolUseをしっかり理解しましょう。
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
PreToolUse Hookの動きを図で示しました。AIがコマンドを生成すると、すぐに実行されるわけではありません。間にPreToolUse Hookが入ります。ここでコマンドの内容を検査し、安全ならそのまま実行、危険なら「STOP」でブロックします。人間がいちいち確認しなくても、瞬時に判断して防いでくれます。
-->

---

# Before / After — Hookの有無でこう変わる

**Hookなし**:

- AIが `rm -rf /project` を生成 → **そのまま実行** → プロジェクト消滅
- 後から気づいても **取り返しがつかない**

**Hookあり**:

- AIが `rm -rf /project` を生成 → **Hookが検知** → `STOP: 危険な操作を検知しました`
- 実行される前に **自動ブロック** → プロジェクトは無事

> 🛡️ たった1本のHookで、致命的な事故を **未然に防げる**

<!--
Hookの有無で何が変わるか、極端な例で示します。Hookがなければ、AIが生成した危険なコマンドがそのまま実行されてしまい、プロジェクトが消滅する可能性があります。Hookがあれば、コマンドが実行される前に自動検知してブロック。「STOP: 危険な操作を検知しました」というメッセージが出て、実行は中止されます。たった1本のHookで、致命的な事故を未然に防げるのです。
-->

---

# 設定ファイルの構造

**`.claude/settings.json`** にHookを定義:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/pretool_check.sh"
          }
        ]
      }
    ]
  }
}
```

- `matcher`: どのツールに反応するか（`Bash` = コマンド実行時）
- `command`: 実行するチェック用スクリプト
- チェックスクリプトが **exit 2** を返すと **ブロック**

<!--
Hookの設定は、プロジェクトの`.claude/settings.json`ファイルに書きます。重要なのは3つの要素です。「matcher」はどのツールに反応するかを指定します。Bashツール、つまりコマンド実行時に反応させます。「command」は実際に実行するチェック用のスクリプトです。このスクリプトがexit code 2を返すと、コマンドの実行がブロックされます。exit 0ならそのまま実行されます。
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

> 💡 これらを **スクリプト1行で検知** できるのがHookの強み

<!--
Hookが防ぐべき危険なパターンを4つ紹介します。再帰削除はプロジェクトやOS全体を消去してしまう致命的な操作。特権実行はシステム設定を変更してしまう危険性があります。データ破壊はデータベースのテーブルを削除。強制pushはリモートの履歴を破壊します。これらを、チェック用スクリプトの1行の条件分岐で検知できるのがHookの強みです。
-->

---

# Hookの実行フローまとめ

```
1. ユーザーがプロンプトを入力
2. AIがツールの使用を判断（例: Bash で rm -rf を実行）
3. PreToolUse Hook が発動
4. チェックスクリプトがコマンド内容を検査
5. 安全（exit 0）→ 実行継続
   危険（exit 2）→ ブロック + 警告メッセージ表示
6. AIがブロック理由を受け取り、別の方法を検討
```

> Hookは **「検閲」ではなく「安全ネット」** — AIも理由を理解して別案を出す

<!--
Hookの全体フローを整理します。ユーザーのプロンプトに対してAIがツールを使おうとすると、PreToolUse Hookが発動します。チェックスクリプトがコマンドの内容を検査し、安全ならexit 0で実行継続、危険ならexit 2でブロックします。重要なのは、ブロックされた後もAIは理由を受け取り、別の安全な方法を自動的に検討する点です。Hookは単に「禁止」するのではなく、AIにより良い選択を促す安全ネットとして働きます。
-->

---

# 初級編のHook — 1本で十分

**初級編で学ぶこと**:
- PreToolUse Hook の **仕組みと役割** の理解
- なぜHookが必要なのかの **理由の把握**
- 設定ファイルの **構造の理解**

**中級編で学ぶこと**:
- **18本のHook** を実装する実践的な手法
- PostToolUse / Notification / Stop などの活用
- より高度な自動化パイプラインの構築

> まずは「**なぜHookが必要か**」を理解するのが第一歩

<!--
初級編ではPreToolUse Hookの仕組みと役割を理解することに集中します。実際に設定ファイルを書くのは中級編で深く扱いますが、この章で「なぜHookが必要なのか」「どういう仕組みで動くのか」を理解しておけば、中級編での実装もスムーズです。中級編では18本のHookを実装し、より高度な自動化パイプラインを構築します。
-->

---

# 📚 カリキュラム一覧 (8 レクチャー / 約 3.5 時間)

| 章 | 内容 | 所要 |
|---|---|---|
| **序** | Claude Codeとは | 15 min |
| 1 | インストール + 初回起動 | 20 min |
| 2 | プロンプト基礎 — AIに確実に伝える | 30 min |
| 3 | CLAUDE.md ミニマム — プロジェクトの説明書 | 30 min |
| 4 | 簡単な自動化体験 — AIに任せてみる | 30 min |
| **5** | **hook の入門 — AIの安全装置 (今ここ)** | **30 min** |
| 6 | MCP 接続入門 — AIの記憶を拡張 | 30 min |
| **終** | 中級編への橋渡し | 25 min |

<!--
改めてカリキュラムの全体像です。現在は第5章「Hookの入門」にいます。これまでCLAUDE.mdと自動化体験を学び、今回は「安全装置」としてのHookを理解しました。次は第6章で「MCP接続」を学び、AIの記憶を拡張する仕組みを理解します。
-->

---

# 🚀 次のレクチャー予告 (第6章)

## **MCP 接続入門 — AIの記憶を拡張する** (30 min)

> AIとの会話を終えるたびに記憶がリセットされていたら非効率です。
> MCPでAIに「記憶」を与えましょう。

- MCP（Model Context Protocol）とは何か
- memory MCP の役割と設定手順
- Before / After で見る記憶の引き継ぎ

<!--
次の第6章では、MCPという仕組みを学びます。今のままでは、AIとの会話を終えるたびに記憶がリセットされてしまいます。毎回同じ説明を繰り返すのは非効率です。MCPはAIに「記憶」を与える仕組みで、セッションを跨いで情報を引き継げるようになります。この講座の3つ目の学習到達点です。
-->

---

<!-- _class: cover -->

# 第5章 完了 🎓
## 次は第6章「MCP 接続入門 — AIの記憶を拡張する」

<div class="meta">
✅ Hookとは何か（AIのライフサイクルイベントに反応する仕組み）<br>
✅ PreToolUse Hook の仕組みと役割<br>
✅ AIの危険操作を自動検知・ブロックする仕組み<br><br>
<b>続けて第6章をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この第5章で、Claude Codeの「安全装置」であるHookの仕組みを理解いただけたでしょうか。PreToolUse Hookがコマンド実行前に検査を行い、危険な操作を自動ブロックする仕組み。これがAI開発における安全の基盤です。次は最後の章「MCP接続入門」で、AIの記憶を拡張する仕組みを学びます。3つの学習到達点の最後の1つです。
-->
