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

# ハーネスとは: Claude Code lifecycle 7イベント
## AIの動作を「監視」する仕組み

<div class="meta">
中級編 v4 — 第10章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第10章へようこそ。この章のテーマは「ハーネス」です。ここまでの章では、AIに何を覚えさせるか、どうコンテキストを管理するかを学んできました。この章からは視点が大きく変わります。AIが何をしたかを監視し、制御する仕組みを学びます。いわば、AIに監視カメラを付けるようなものです。40分間、一緒にハーネスの世界に入っていきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと [L2: Understand + L3: Apply]

1. **Claude Code lifecycle 7イベント** の名前と発火タイミングを説明できる
2. **各イベントの用途** を理解し、適切な場面で選択できる
3. **最小hookの構造** を理解し、自分で書ける
4. **settings.json** へのhook登録方法を説明できる
5. **hook発火確認** の手順を実行できる

<!--
この章では5つの到達点を目指します。まずClaude Codeのライフサイクルにおける7つのイベントの名前と発火タイミングを理解します。次に、各イベントがどのような用途に適しているかを学びます。そして、最もシンプルなhookを自分で書けるようになり、settings.jsonへの登録方法と、hookが正しく発火しているかの確認方法を習得します。Bloomの分類で言えばUnderstandとApplyレベル、理解と応用が中心です。
-->

---

# 「AIに監視カメラを付ける」

> 「AIが勝手にファイルを消した」「AIが想定外のコマンドを実行した」
> — この問題の根本原因は、**AIの動作を誰も監視していなかった** ことです。

- L1 (プロンプト) = AIに「何をさせるか」
- L2 (コンテキスト) = AIに「何を知らせるか」
- **L3 (ハーネス)** = AIの「動作を監視・制御」する

> **L3はL1/L2と独立**: どんなに良いプロンプトを書いても、監視がなければ安全ではない

<!--
つかみのスライドです。L1で指示を書き、L2で知識を与えても、AIが実際に何をしたかを監視していなければ、安全な開発とは言えません。L3のハーネスは、AIの動作を監視し、必要に応じて制御する仕組みです。今までの章が「AIに何を教えるか」だったのに対し、この章からは「AIが何をしたかを見張る」に視点が変わります。この違いを意識しておいてください。
-->

---

# 7つのライフサイクルイベント — 全体フロー

Claude Codeのセッションは、**7つのイベント** に沿って進行します:

| # | イベント | タイミング |
|---|---------|-----------|
| 1 | **SessionStart** | セッション開始時 (1回) |
| 2 | **UserPromptSubmit** | ユーザーがプロンプト送信時 |
| 3 | **PreToolUse** | ツール実行の直前 |
| 4 | **PostToolUse** | ツール実行の直後 |
| 5 | **Notification** | 通知送信時 |
| 6 | **PreCompact** | コンテキスト圧縮の直前 |
| 7 | **Stop** | セッション停止時 (1回) |

- **PreToolUse / PostToolUse は何度も発火** — AIがツールを使うたびに
- **SessionStart / Stop は各1回** — セッションの最初と最後

<!--
Claude Codeのライフサイクルには7つのイベントがあります。セッションが開始されるとSessionStartが1回だけ発火します。ユーザーがプロンプトを送信するたびにUserPromptSubmitが発火し、AIがツールを使うたびにPreToolUseとPostToolUseがペアで発火します。通知が送信されるとNotification、コンテキストが圧縮される前にPreCompact、そしてセッションが終了するとStopが発火します。この7つのイベントが、AIの動作を監視するためのフックポイントです。
-->

---

# 各イベントの用途 (1/2) — SessionStart / UserPromptSubmit / PreToolUse

### SessionStart — セッション開始時
- **用途**: 初期化処理、環境チェック、エージェント識別
- **例**: セッション開始時にtmux環境変数を読み込み、自分の役割を特定する

### UserPromptSubmit — ユーザーがプロンプト送信時
- **用途**: 入力チェック、通知トリガー、デバッグフラグ確認
- **例**: ユーザーがプロンプトを送信するたびに、通知設定をチェックする

### PreToolUse — ツール実行の直前
- **用途**: **最も重要なイベント** — 危険な操作の検知・ブロック
- **例**: `rm -rf` や `git push --force` などの危険コマンドを検知してBLOCK

<!--
3つのイベントの用途を詳しく見ます。SessionStartはセッションの開始時に1回だけ発火し、初期化処理に使います。UserPromptSubmitはユーザーがプロンプトを送信するたびに発火し、入力チェックや通知のトリガーに使います。PreToolUseは最も重要なイベントで、AIがツールを実行する直前に発火します。ここで危険なコマンドを検知してブロックすることができます。PreToolUseがL3の要となるイベントです。
-->

---

# 各イベントの用途 (2/2) — PostToolUse / Notification / PreCompact / Stop

### PostToolUse — ツール実行の直後
- **用途**: 実行結果の検証、ログ記録、状態更新
- **例**: YAMLファイル編集後にフォーマットチェックを実行

### Notification — 通知送信時
- **用途**: 通知内容の加工、外部サービスへの転送
- **例**: 通知をSlackやスマホに転送する

### PreCompact — コンテキスト圧縮の直前
- **用途**: 圧縮前の重要情報保存
- **例**: 進行中の作業状態をファイルに保存

### Stop — セッション停止時
- **用途**: 終了処理、未完了タスクの通知、リソース解放
- **例**: セッション終了時に未読メッセージの有無を確認

<!--
残り4つのイベントです。PostToolUseはツール実行後に発火し、結果の検証や状態更新に使います。Notificationは通知送信時に発火し、外部サービスへの転送などに使います。PreCompactはコンテキスト圧縮の直前に発火し、重要な情報をファイルに保存するチャンスです。Stopはセッションの最後に1回だけ発火し、終了処理や未完了タスクの通知に使います。7つのイベントを理解することで、AIの動作をあらゆるタイミングで監視できます。
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
| 標準出力 | AIへのメッセージとして表示 |
| 終了コード 0 | **許可** (ツール実行を継続) |
| 終了コード 2 | **BLOCK** (ツール実行を中止) |

- 標準出力のテキストはAIのコンテキストに注入される
- `exit 2` でブロック — **これがL3の制御力の源泉**

<!--
最小のhookを見てみましょう。シェルスクリプト1行で動きます。echoで文字列を出力すると、それがAIのコンテキストに注入されます。終了コードが0ならツールの実行が継続され、終了コードが2ならツールの実行がブロックされます。このexit 2によるブロック機能が、L3ハーネスの制御力の源泉です。AIが危険な操作をしようとしたときに、スクリプトが割り込んで止めることができます。
-->

---

# settings.json — hookの登録方法

Claude Codeのhookは `.claude/settings.json` に登録します:

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
- **hooks配列** に複数のhookを登録可能 — 1イベントに複数の監視員を配置
- **timeout**: hookの実行時間上限 (秒) — 長すぎるとAIが待たされる

<!--
hookの登録はsettings.jsonで行います。hooksオブジェクトのキーにイベント名を指定し、hooks配列の中にhookの設定を書きます。typeはcommand、commandに実行するスクリプトのパス、timeoutで実行時間の上限を指定します。1つのイベントに複数のhookを登録でき、順番に実行されます。どれか1つでもexit 2を返せば、ツールの実行はブロックされます。
-->

---

# hook発火確認 — 「動いている」を証明する

hookが正しく動いているか確認する手順:

1. **hookスクリプトにログ出力を追加**:
   ```
   echo "[$(date)] PreToolUse fired: $TOOL_NAME" >> /tmp/hook.log
   ```

2. **Claude Codeでツールを実行** (例: `Read` や `Bash`)

3. **ログファイルを確認**:
   ```
   cat /tmp/hook.log
   # [2026-05-03 12:00:00] PreToolUse fired: Read
   ```

> **確認のコツ**: 最初は `echo` だけの最小hookで発火を確認してから、本格的な処理を追加する

<!--
hookが正しく発火しているかを確認する方法です。hookスクリプトにログ出力を追加し、Claude Codeでツールを実行した後にログファイルを確認します。ログに日時とツール名が記録されていれば、hookは正しく動いています。重要なのは、最初は最小のhookで発火を確認してから、徐々に本格的な処理を追加していくことです。いきなり複雑な処理を書くと、動かないときに原因の特定が難しくなります。
-->

---

# 18本hookカタログ — 概観

実プロジェクトで運用している18本のhookを6カテゴリに分類:

| カテゴリ | 本数 | 代表hook | 目的 |
|---------|------|---------|------|
| **安全性チェック** | 4 | pretool_check.sh | 危険コマンドのBLOCK |
| **コンテキスト管理** | 3 | semantic_index_hook.sh | 自動インデックス更新 |
| **品質検証** | 3 | posttool_yaml_check.sh | 編集結果の自動検証 |
| **セッション管理** | 3 | sessionstart_hook.sh / stop_hook_inbox.sh | 開始・終了の自動処理 |
| **検索・通知** | 3 | cmd_rag_hook.sh / userprompt_ntfy_check.sh | 過去事例検索・通知 |
| **運用補助** | 2 | precompact_hook.sh | 圧縮前の状態保存 |

> **このカタログがL3の実力**: 18本のhookが24時間365日、AIの動作を監視している

<!--
実プロジェクトで運用している18本のhookを6カテゴリに分類しました。安全性チェックが4本で最も多く、危険なコマンドの実行をブロックします。コンテキスト管理が3本で、自動的にインデックスを更新します。品質検証が3本で、編集結果を自動でチェックします。セッション管理が3本で、開始と終了の処理を自動化します。検索・通知が3本で、過去の事例を自動検索したり通知を送ったりします。運用補助が2本で、圧縮前の状態保存などに使います。18本のhookが、AIの動作を常に監視しているのがL3の実力です。
-->

---

# この章のまとめ

- **L3ハーネス** = AIの動作を監視・制御する仕組み (監視カメラ)
- **7つのライフサイクルイベント**: SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Notification / PreCompact / Stop
- **PreToolUse が最重要** — ツール実行前に介入し、危険な操作をBLOCKできる
- **最小hook** は `echo` 1行 + `exit 2` でブロック — シンプルだが強力
- **settings.json** に登録するだけ — 追加のインフラ不要
- **18本のhookカタログ** が実運用の実例

<!--
この章のまとめです。L3ハーネスはAIの動作を監視・制御する仕組みで、7つのライフサイクルイベントがフックポイントになります。中でもPreToolUseが最も重要で、ツール実行前に介入して危険な操作をブロックできます。hookの実装はecho1行とexit 2だけで、settings.jsonに登録するだけで動きます。次章では、このhookを使って完了を自動検証する「完了Gate」を解説します。
-->

---

# 確認問題

**Q1**: AIがファイルを削除する直前に介入できるライフサイクルイベントはどれか？
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
確認問題です。Q1、AIがファイルを削除する直前に介入できるのはPreToolUseです。ツール実行の直前に発火するため、危険な操作をブロックできます。Q2、ツールの実行をブロックする終了コードは2です。0なら許可、2ならブロックです。Q3、1つのイベントに複数のhookを登録できます。hooks配列に複数のhook設定を書くことができます。
-->

---

<!-- _class: cover -->

# 第10章 完了!
## AIに監視カメラを付けられたか?

**到達点チェック**:
- ✅ 7つのライフサイクルイベントの名前とタイミングを説明できる
- ✅ 各イベントの用途を理解し、適切に選択できる
- ✅ 最小hookの構造を理解し、自分で書ける
- ✅ settings.jsonへのhook登録方法を説明できる
- ✅ hook発火確認の手順を説明できる

**次章**: 完了Gateハーネス — AIの「完了」を機械的に検証する

<div class="meta">
講師: なぎなた
</div>

<!--
第10章完了です。AIに監視カメラを付ける仕組み、ハーネスについて理解できたでしょうか。到達点を振り返りましょう。7つのイベント、各イベントの用途、最小hookの構造、settings.jsonへの登録、発火確認の5つを理解できていれば完璧です。次章では、このhookを使ってAIの完了報告を機械的に検証する完了Gateハーネスを解説します。引き続き学んでいきましょう。
-->
