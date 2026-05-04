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

# Agent Harness 入門: AIエージェントの監視と制御
## AIに「監視カメラと非常停止ボタン」を付ける仕組み

<div class="meta">
中級編 v4 — 第10章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第10章へようこそ。ここからL3ハーネス層に入ります。テーマはAgent Harness、つまりAIエージェントの動作を監視し制御する仕組みです。例えるなら、AIに監視カメラと非常停止ボタンを付けるようなものです。この章では、エージェントライフサイクルの7つのイベントフックポイントを理解し、最小のハーネスを自分で設計できるようになります。40分間、一緒に学んでいきましょう。なぎなたと申します。
-->

---

## この章で出てくる用語

> この章で初めて登場する用語を先にまとめます。安心して読み進めてください。

| 用語 | 読み方 | この章での意味 |
|------|--------|----------------|
| **hook（フック）** | — | 特定のタイミングで自動実行される小さなプログラム。AIの動作に「ひっかけて」監視する |
| **Agent Harness** | エージェント・ハーネス | AIエージェントを監視・制御する仕組み全体の名前 |
| **Control Plane** | コントロール・プレーン | 業界での呼び方。ハーネスと同じ意味（管理の仕組み） |
| **lifecycle event** | ライフサイクル・イベント | AIが動く中で自動的に起きる7つのタイミング（開始・実行・終了など） |
| **settings.json** | — | hookを登録する設定ファイル。プロジェクトの`.claude/`ディレクトリに置く |

---

## この章で学ぶこと

1. **Agent Harness** の概念を説明できる
2. **7つのlifecycleイベント** の名前と発火タイミングを理解する
3. **最小hookの構造** を設計し、自分で書ける
4. **settings.json** へのhook登録方法を説明できる
5. **hook発火確認** の手順を説明できる

<!--
この章では5つの到達点を目指します。まずAgent Harnessの概念を理解します。次に7つのlifecycleイベントを把握します。そして最もシンプルなhookを自分で書けるようになり、settings.jsonへの登録方法と発火確認の手順を習得します。
-->

---

# 「AIエージェントに監視カメラを付ける」

> 「AIが勝手にファイルを消した」「AIが想定外のコマンドを実行した」
> — この問題の根本原因は、**Agentの動作を誰も監視していなかった** ことです。

**AI開発の3階層（おさらい）**:
- **L1 (プロンプト)** = Agentに「何をさせるか」を指示する（第1〜4章）
- **L2 (コンテキスト)** = Agentに「何を知らせるか」を与える（第5〜9章）
- **L3 (ハーネス)** = Agentの「動作を監視・制御」する（この章から）

> ハーネスは **AIに付ける監視カメラと非常停止ボタン** です
> 工場で言えば、安全センサーと非常停止スイッチに相当します

<!--
つかみのスライドです。L1で指示を書き、L2で知識を与えても、エージェントが実際に何をしたかを監視していなければ安全な開発とは言えません。ハーネスはAIに付ける監視カメラと非常停止ボタンです。工場の安全センサーと非常停止スイッチと同じ考え方です。この章から視点が「Agentに何を教えるか」から「Agentが何をしたかを見張る」に変わります。
-->

---

# 7 Lifecycle Events — 全体フロー

Claude Code等のAIエージェントCLIのセッションは、**7つのイベント** に沿って進行します:

| # | イベント | タイミング |
|---|---------|-----------|
| 1 | **SessionStart** | セッション開始時 (1回) |
| 2 | **UserPromptSubmit** | ユーザーがプロンプト送信時 |
| 3 | **PreToolUse** | ツール実行の直前 |
| 4 | **PostToolUse** | ツール実行の直後 |
| 5 | **Notification** | 通知送信時 |
| 6 | **PreCompact** | コンテキスト圧縮の直前 |
| 7 | **Stop** | セッション停止時 (1回) |

- **PreToolUse / PostToolUse は何度も発火** — エージェントがツールを使うたびに
- **SessionStart / Stop は各1回** — セッションの最初と最後

<!--
Claude Code等のAIエージェントCLIのライフサイクルには7つのイベントがあります。セッションが開始されるとSessionStartが1回だけ発火します。ユーザーがプロンプトを送信するたびにUserPromptSubmitが発火し、エージェントがツールを使うたびにPreToolUseとPostToolUseがペアで発火します。通知が送信されるとNotification、コンテキストが圧縮される前にPreCompact、そしてセッションが終了するとStopが発火します。この7つのイベントが、ハーネスのフックポイントです。
-->

---

# 各イベントの用途 (1/2)

### SessionStart — セッション開始時
- **用途**: 初期化処理、環境チェック、Agent識別
- **何が起きる**: セッションが始まった瞬間に1回だけ自動実行

### UserPromptSubmit — ユーザーがプロンプト送信時
- **用途**: 入力チェック、通知トリガー、デバッグフラグ確認
- **何が起きる**: ユーザーがメッセージを送るたびに自動実行

### PreToolUse — ツール実行の直前
- **用途**: **最も重要なイベント** — 危険な操作の検知・ブロック
- **何が起きる**: AIがファイル読み込みやコマンド実行をする直前に自動実行

<!--
3つのイベントの用途です。SessionStartはセッションの開始時に1回だけ発火し、初期化処理に使います。UserPromptSubmitはユーザーがメッセージを送るたびに発火し、入力の検証や通知のトリガーに使います。PreToolUseは最も重要で、AIがツールを実行する直前に発火し、危険なコマンドをブロックできます。
-->

---

# 各イベントの用途 (2/2)

### PostToolUse — ツール実行の直後
- **用途**: 実行結果の検証、ログ記録、状態更新
- **何が起きる**: AIがツールを使った直後に自動実行

### Notification — 通知送信時
- **用途**: 通知内容の加工、外部サービスへの転送
- **何が起きる**: 通知が送られる瞬間に自動実行

### PreCompact — コンテキスト圧縮の直前
- **用途**: 圧縮前の重要情報保存
- **何が起きる**: AIの記憶が整理される直前に自動実行

### Stop — セッション停止時
- **用途**: 終了処理、未完了タスクの通知、リソース解放
- **何が起きる**: セッションが終わる瞬間に1回だけ自動実行

<!--
残り4つのイベントです。PostToolUseはツール実行後の検証や状態更新に使います。Notificationは通知の転送に使います。PreCompactはコンテキスト圧縮の前に重要な情報を保存するチャンスです。Stopはセッション終了時の後処理に使います。これら7つのイベントが、hookを仕掛けるポイントです。
-->

---

# 最小hookの構造 — 「hello from hook!」

最もシンプルなPreToolUse hook:

```
#!/bin/bash
# hello_hook.sh — 最小のhook
echo "hello from hook!"
```

**hookの基本構造**:

| 要素 | 説明 |
|------|------|
| 実行ファイル | シェルスクリプト (`.sh`) |
| 標準出力 | Agentへのメッセージとして表示 |
| 終了コード 0 | **許可** (ツール実行を継続) |
| 終了コード 2 | **BLOCK** (ツール実行を中止) — Claude Codeの仕様で2がブロック用に予約されている |

- 標準出力のテキストはAgentのコンテキストに注入される
- `exit 2` でブロック — **これがControl Planeの制御力の源泉**

<!--
最小のhookです。シェルスクリプト1行で動きます。echoで文字列を出力するとAgentのコンテキストに注入され、終了コード0なら実行継続、2ならブロックされます。終了コード2はClaude Codeの仕様でブロック用に予約されている番号です。1（一般的なエラー）ではなく2なのは、この予約仕様のためです。
-->

---

# settings.json — hookの登録方法

hookはプロジェクト直下の `.claude/settings.json` ファイルに登録します:
- 場所: `~/your-project/.claude/settings.json`（プロジェクト固有の設定）
- または `~/.claude/settings.json`（全プロジェクト共通の設定）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/hello_hook.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

- **イベント名** がキー: `PreToolUse` / `PostToolUse` / `Stop` 等
- **hooks配列** に複数のhookを登録可能
- **timeout**: hookの実行時間上限 (秒)

<!--
hookの登録はsettings.jsonで行います。hooksオブジェクトのキーにイベント名を指定し、hooks配列の中にhookの設定を書きます。1つのイベントに複数のhookを登録でき、順番に実行されます。どれか1つでもexit 2を返せば、ツールの実行はブロックされます。
-->

---

# hook発火確認 — 「動いている」を証明する

hookが正しく動いているか確認する手順:

1. **hookスクリプトにログ出力を追加**:
   ```
   echo "[$(date)] PreToolUse fired: $TOOL_NAME" >> hook.log
   ```
   - `$TOOL_NAME` はhook実行時にClaude Codeが自動で渡す環境変数で、使われたツール名（Read, Bash等）が入ります

2. **CLIでツールを実行** (例: `Read` や `Bash`)

3. **ログファイルを確認**:
   ```
   cat hook.log
   # [2026-05-03 12:00:00] PreToolUse fired: Read
   ```

> **確認のコツ**: 最初は `echo` だけの最小hookで発火を確認してから、本格的な処理を追加する

<!--
hookが正しく発火しているかの確認方法です。スクリプトにログ出力を追加し、ツールを実行した後にログを確認します。重要なのは最初は最小hookで発火確認してから、徐々に処理を追加していくことです。
-->

---

# 実運用カタログ — 18本のAgent Harness概観

本講座の制作環境で運用している18本のhookを6カテゴリに分類: *(講師の環境での実例。受講者が18本すべてを作る必要はありません)*

| カテゴリ | 本数 | 代表hook | 役割 |
|---------|------|---------|------|
| **安全チェック** | 4 | pretool_check.sh | 危険な操作の検知・ブロック |
| **コンテキスト管理** | 3 | semantic_index_hook.sh | メモリの自動整理 |
| **品質ゲート** | 3 | posttool_yaml_check.sh | ファイル形式の検証 |
| **セッション管理** | 3 | sessionstart / stop hooks | 開始・終了の自動処理 |
| **検索・通知** | 3 | cmd_rag_hook / ntfy hooks | 外部サービス連携 |
| **運用監視** | 2 | precompact_hook.sh | 記憶整理の補助 |

> 18本のAgent Harnessが24時間365日、エージェントの動作を監視する — これが実運用のControl Planeです

<!--
実運用でのhookカタログです。講師の制作環境では18本のhookを運用していますが、これは一つの例です。安全性チェック、コンテキスト管理、品質ゲート、セッション管理、検索・通知、運用監視の6カテゴリに分類しています。まずは1本の最小hookから始めて、必要に応じて増やしていくのがおすすめです。
-->

---

# この章のまとめ

- **Agent Harness** = AIエージェントの動作を監視・制御する仕組み（監視カメラ＋非常停止ボタン）
- **7 Lifecycle Events**: SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Notification / PreCompact / Stop
- **PreToolUse が最重要** — ツール実行前に介入し、危険な操作をBLOCKできる
- **最小hook** は `echo` 1行 + `exit 2` でブロック — シンプルだが強力
- **settings.json** に登録するだけ — 追加のインフラ不要

<!--
この章のまとめです。Agent HarnessはAIエージェントの動作を監視・制御する仕組みです。7つのライフサイクルイベントがフックポイントになり、中でもPreToolUseが最も重要です。最小hookはecho1行とexit 2だけで、settings.jsonに登録するだけで動きます。
-->

---

# 確認問題

**Q1**: エージェントがファイルを削除する直前に介入できるライフサイクルイベントはどれか？
- A: SessionStart
- B: PreToolUse
- C: PostToolUse

**Q2**: hookスクリプトがツールの実行をブロックする終了コードは？
- A: 0
- B: 1
- C: 2

**Q3**: 複数のhookを1つのイベントに登録できるか？
- A: できない (1イベント1hook)
- B: できる (配列に複数登録可能)
- C: settings.jsonの編集権限による

<!--
確認問題です。Q1、ファイル削除の直前に介入できるのはPreToolUseです。ファイル削除はBashツールのrmコマンドで実行されます。つまり「ツール実行」の一種であり、その直前に発火するのがPreToolUseです。Q2、ブロックする終了コードは2です。0なら許可、2ならブロックです。1は一般的なエラー用で、ブロックには使いません。Q3、1つのイベントに複数のhookを登録できます。hooks配列に複数の設定を書けます。
-->

---

<!-- _class: cover -->

# 第10章 完了!
## Agent Harness の設計思想を理解したか?

**到達点チェック**:
- ✅ Agent Harness の概念（監視カメラ＋非常停止ボタン）を説明できる
- ✅ 7つのlifecycleイベントの名前とタイミングを説明できる
- ✅ 最小hookの構造を理解し、自分で書ける
- ✅ settings.jsonへのhook登録方法を説明できる
- ✅ hook発火確認の手順を説明できる

**次章**: Supervisor Pattern — 完了検証Gateの実装

<div class="meta">
講師: なぎなた
</div>

<!--
第10章完了です。Agent Harnessの設計思想を理解できたでしょうか。到達点を振り返りましょう。7つのイベント、各イベントの用途、最小hookの構造、settings.jsonへの登録、発火確認の5つを理解できていれば完璧です。次章では、このhookを使って完了を自動検証するSupervisor Patternを解説します。
-->
