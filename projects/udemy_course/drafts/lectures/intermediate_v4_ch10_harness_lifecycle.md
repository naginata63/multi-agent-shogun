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

# Agent Harness 入門: AI Control Plane の設計思想
## AIエージェントに「監視と制御」の仕組みを組み込む

<div class="meta">
中級編 v4 — 第10章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第10章へようこそ。ここからL3ハーネス層に入ります。テーマはAgent Harness、つまりAIエージェントの動作を監視し制御する仕組みです。業界ではControl PlaneやGuardrailsといった用語で議論されています。この章では、エージェントライフサイクルの7つのイベントフックポイントを理解し、最小のハーネスを自分で設計できるようになります。40分間、一緒に学んでいきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと [L2: Understand + L3: Apply]

1. **Agent Harness / Control Plane** の概念を説明できる
2. **7 lifecycle events** の名前と発火タイミングを理解する
3. **最小hookの構造** を設計し、自分で書ける
4. **settings.json** へのhook登録方法を説明できる
5. **hook発火確認** の手順を説明できる

<!--
この章では5つの到達点を目指します。まずAgent HarnessとControl Planeの概念を理解します。次にClaude Codeのライフサイクルにおける7つのイベントを把握します。そして最もシンプルなhookを自分で書けるようになり、settings.jsonへの登録方法と発火確認の手順を習得します。
-->

---

# 「AIエージェントに監視カメラを付ける」

> 「AIが勝手にファイルを消した」「AIが想定外のコマンドを実行した」
> — この問題の根本原因は、**Agentの動作を誰も監視していなかった** ことです。

- L1 (プロンプト) = Agentに「何をさせるか」
- L2 (コンテキスト) = Agentに「何を知らせるか」
- **L3 (ハーネス)** = Agentの「動作を監視・制御」する

> 業界では **Control Plane** と呼ばれます — Kubernetesがコンテナを管理するように、ハーネスはエージェントを管理します

<!--
つかみのスライドです。L1で指示を書き、L2で知識を与えても、エージェントが実際に何をしたかを監視していなければ安全な開発とは言えません。業界ではこの監視・制御層をControl Planeと呼びます。Kubernetesがコンテナを管理するように、ハーネスはAIエージェントの動作を管理します。この章から視点が「Agentに何を教えるか」から「Agentが何をしたかを見張る」に変わります。
-->

---

# 7 Lifecycle Events — 全体フロー

AI開発CLIのセッションは、**7つのイベント** に沿って進行します:

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
AI開発CLIのライフサイクルには7つのイベントがあります。セッションが開始されるとSessionStartが1回だけ発火します。ユーザーがプロンプトを送信するたびにUserPromptSubmitが発火し、エージェントがツールを使うたびにPreToolUseとPostToolUseがペアで発火します。通知が送信されるとNotification、コンテキストが圧縮される前にPreCompact、そしてセッションが終了するとStopが発火します。この7つのイベントが、ハーネスのフックポイントです。
-->

---

# 各イベントの用途 (1/2)

### SessionStart — セッション開始時
- **用途**: 初期化処理、環境チェック、Agent識別
- **業界用語**: Bootstrap / Warm-up Phase

### UserPromptSubmit — ユーザーがプロンプト送信時
- **用途**: 入力チェック、通知トリガー、デバッグフラグ確認
- **業界用語**: Input Validation / Request Interceptor

### PreToolUse — ツール実行の直前
- **用途**: **最も重要なイベント** — 危険な操作の検知・ブロック
- **業界用語**: Pre-execution Guardrail / Policy Gate

<!--
3つのイベントの用途です。SessionStartはセッションの開始時に1回だけ発火し、初期化処理に使います。業界ではBootstrap Phaseとも呼ばれます。UserPromptSubmitは入力の検証や通知のトリガーに使います。PreToolUseは最も重要で、ツール実行の直前に発火し、危険なコマンドをブロックできます。業界ではPre-execution GuardrailやPolicy Gateと呼ばれるパターンです。
-->

---

# 各イベントの用途 (2/2)

### PostToolUse — ツール実行の直後
- **用途**: 実行結果の検証、ログ記録、状態更新
- **業界用語**: Post-execution Hook / Result Validator

### Notification — 通知送信時
- **用途**: 通知内容の加工、外部サービスへの転送
- **業界用語**: Event Router / Output Gateway

### PreCompact — コンテキスト圧縮の直前
- **用途**: 圧縮前の重要情報保存
- **業界用語**: State Snapshot / Checkpoint

### Stop — セッション停止時
- **用途**: 終了処理、未完了タスクの通知、リソース解放
- **業界用語**: Graceful Shutdown / Teardown Phase

<!--
残り4つのイベントです。PostToolUseは結果の検証や状態更新に使います。Notificationは通知の転送に使います。PreCompactはコンテキスト圧縮の前に重要な情報を保存するチャンスです。Stopはセッション終了時の後処理に使います。それぞれ業界用語と対応関係を意識しておくと、他のエージェントフレームワークのドキュメントを読むときにも役立ちます。
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
| 終了コード 2 | **BLOCK** (ツール実行を中止) |

- 標準出力のテキストはAgentのコンテキストに注入される
- `exit 2` でブロック — **これがControl Planeの制御力の源泉**

<!--
最小のhookです。シェルスクリプト1行で動きます。echoで文字列を出力するとAgentのコンテキストに注入され、終了コード0なら実行継続、2ならブロックされます。このexit 2によるブロック機能がControl Planeの制御力の源泉です。
-->

---

# settings.json — hookの登録方法

AI開発CLIのhookは `.claude/settings.json` に登録します:

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
   echo "[$(date)] PreToolUse fired: $TOOL_NAME" >> /tmp/hook.log
   ```

2. **CLIでツールを実行** (例: `Read` や `Bash`)

3. **ログファイルを確認**:
   ```
   cat /tmp/hook.log
   # [2026-05-03 12:00:00] PreToolUse fired: Read
   ```

> **確認のコツ**: 最初は `echo` だけの最小hookで発火を確認してから、本格的な処理を追加する

<!--
hookが正しく発火しているかの確認方法です。スクリプトにログ出力を追加し、ツールを実行した後にログを確認します。重要なのは最初は最小hookで発火確認してから、徐々に処理を追加していくことです。
-->

---

# 実運用カタログ — 18本のAgent Harness概観

本講座の制作環境で運用している18本のhookを6カテゴリに分類: *(本講座サンプル実装)*

| カテゴリ | 本数 | 代表hook | 業界での呼称 |
|---------|------|---------|-------------|
| **Safety Guardrails** | 4 | pretool_check.sh | Policy Engine |
| **Context Management** | 3 | semantic_index_hook.sh | Auto-indexing |
| **Quality Gates** | 3 | posttool_yaml_check.sh | Schema Validation |
| **Session Lifecycle** | 3 | sessionstart / stop hooks | Bootstrap / Teardown |
| **RAG / Notification** | 3 | cmd_rag_hook / ntfy hooks | Event Router |
| **Observability** | 2 | precompact_hook.sh | State Snapshot |

> 18本のAgent Harnessが24時間365日、エージェントの動作を監視する — これが実運用のControl Planeです

<!--
実運用でのhookカタログです。安全性チェック、コンテキスト管理、品質検証、セッション管理、検索・通知、運用補助の6カテゴリに分類しています。業界ではPolicy EngineやSchema Validationといった用語が使われます。18本のhookが常にエージェントを監視しているのがControl Planeの実際の姿です。
-->

---

# この章のまとめ

- **Agent Harness / Control Plane** = AIエージェントの動作を監視・制御する仕組み
- **7 Lifecycle Events**: SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Notification / PreCompact / Stop
- **PreToolUse が最重要** — ツール実行前に介入し、危険な操作をBLOCKできる
- **最小hook** は `echo` 1行 + `exit 2` でブロック — シンプルだが強力
- **settings.json** に登録するだけ — 追加のインフラ不要
- **業界用語**: Control Plane / Guardrails / Policy Gate で他フレームワークとも共通

<!--
この章のまとめです。Agent HarnessはControl Planeとしてエージェントを監視・制御する仕組みです。7つのライフサイクルイベントがフックポイントになり、中でもPreToolUseが最も重要です。最小hookはecho1行とexit 2だけで、settings.jsonに登録するだけで動きます。業界用語のControl PlaneやGuardrailsは他のエージェントフレームワークでも共通する概念です。
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
確認問題です。Q1、ファイル削除の直前に介入できるのはPreToolUseです。ツール実行の直前に発火するため、危険な操作をブロックできます。Q2、ブロックする終了コードは2です。0なら許可、2ならブロックです。Q3、1つのイベントに複数のhookを登録できます。hooks配列に複数の設定を書けます。
-->

---

<!-- _class: cover -->

# 第10章 完了!
## Agent Harness / Control Plane の設計思想を理解したか?

**到達点チェック**:
- ✅ Agent Harness / Control Plane の概念を説明できる
- ✅ 7つのライフサイクルイベントの名前とタイミングを説明できる
- ✅ 最小hookの構造を理解し、自分で書ける
- ✅ settings.jsonへのhook登録方法を説明できる
- ✅ hook発火確認の手順を説明できる

**次章**: Supervisor Pattern — 完了検証Gateの実装

<div class="meta">
講師: なぎなた
</div>

<!--
第10章完了です。Agent HarnessとControl Planeの設計思想を理解できたでしょうか。到達点を振り返りましょう。7つのイベント、各イベントの用途、最小hookの構造、settings.jsonへの登録、発火確認の5つを理解できていれば完璧です。次章では、このhookを使って完了を自動検証するSupervisor Patternを解説します。
-->
