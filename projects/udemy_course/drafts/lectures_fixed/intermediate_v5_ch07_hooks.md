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

<!--
スピーカーノート:
第7章の冒頭。ch06 で「advisor は AI が skip することもある (任意発動)」と学んだ。本章は hook (強制発動) を学び、両者を使い分けられるようにする。hook は Anthropic Claude Code 公式機能・全 29 種類のライフサイクルイベントで、本章は代表的な 4 つを抜粋して解説する。「手動 → 自動 → 自律」の中継地点として、ch04 検索を自動化し、ch11 Skill 自律化への橋渡しを担う。
-->

<!-- _class: cover -->

# 自動で動かす — 主要 hook と Skill 連携 (代表抜粋)
## — ハーネス層 (L3) の自動化編

<div class="meta">
中級編 — 第7章 (約 20 min)<span class="free">FREE</span><br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
</div>

---

# ch07. 自動で動かす — 主要 hook と Skill 連携 (代表抜粋)

---

<!--
スピーカーノート:
ch06 advisor は任意発動・skip ありの軽量レビューだった。確実な品質ゲートが必要な場面では hook (強制発動) を使う。加えて ch04 で手動で叩いていた検索コマンドは UserPromptSubmit hook で自動発動できる。「ch06 確実性確保」と「ch04 自動化」の 2 つの路線が ch07 hook に合流する構図を示し、ch07 の位置付けを明確にする。
-->

## 前章 (ch06) の核心 と ch07 への 2 つの路線

> ch06 で学んだこと:
> - **advisor は任意発動** — AI が自律判断で呼ぶ・skip することもある (確実な品質ゲートではない)
> - advisor は Anthropic API beta tool・ハイブリッド構造 (executor=client 側 / advisor=server-side)
> - 確実性が要る場面では「**強制発動の仕組み**」が必要

**ch07 への 2 つの路線が合流する:**

```
[路線①: ch06 → ch07]  確実性確保
  advisor (任意発動・skip あり)  ──→  hook (強制発動・skip なし)

[路線②: ch04 → ch07]  自動化
  検索コマンドを手動で叩く  ──→  UserPromptSubmit hook で自動発動
```

本章で扱う **hook** は Anthropic Claude Code 公式機能で **全 29 種類のライフサイクルイベント**。本章は代表的な 4 つを抜粋して解説します。

---

<!--
スピーカーノート:
ch04との連結を維持。ch04で学んだ検索技術が、ch07で自動化され、ch11で自律化されるという進化の路線図を意識させてください。「手動→自動→自律」の3段階のどこにいるかを常に意識させるのがこの章のポイントです。
-->

## ch04 → ch07 → ch11 の進化路線

> ch04 で学んだ検索技術 —
> 人間が叩かなくても勝手に動く仕組み、それが **hook** です。
> ch04 で動かした検索コマンドを、この章では **自動発動** させて完成形にします。

```
ch04 [手動]  検索コマンドを手で叩く    ──→  「便利だけど面倒」
ch07 [自動]  hook で勝手に動く        ──→  「意識しなくていい」
ch11 [自律]  Skill が自律判断で呼ぶ   ──→  「AI が自分で選ぶ」
```

同じ技術が **手動 → 自動 → 自律** へ進化する。本章はその中継地点。

---

<!--
スピーカーノート:
この章で扱う困りごと⑧⑨の紹介。⑧は「API変更後にテストせず壊れる」で PostToolUse hook が解決。⑨は「大事なドキュメントを確認しない」で UserPromptSubmit hook が解決。「毎回検索コマンド叩くの面倒」という不満が、hook によって自動化されることを予告してください。
-->

## この章で解決する「困りごと」

> **⑧ API 変更後にテストせず壊れる**
> **⑨ 大事なドキュメントを確認しない**

- ch04 で覚えた検索コマンド、**毎回叩くの面倒**
- ファイル編集後にテストを忘れる
- prompt 送信時に関連ドキュメントを毎回貼り直している
- 長文ドキュメントを貼っているうちに AI が中央の内容を読み飛ばしてしまう (Lost in the Middle)

---

## 章のゴール

**言える 1 文:**
> hook で AI のライフサイクルイベントに処理を差し込めば、テスト忘れも資料確認忘れも防げる

**できる 1 動作:**
> hook を 1 つ作って、プロンプト送信時に自動で関連ドキュメントを検索する仕組みを動かせる

---

<!--
スピーカーノート:
hook の概念説明。「防犯カメラの動体検知センサー」の比喩を使って、普段は静観して特定タイミングで自動発動する仕組みを直感的に理解させる。公式定義として「AI のライフサイクルイベントに任意処理を差し込む仕組み」と広義に押さえ、安全装置・関連資料注入はあくまで代表的用途の一つに過ぎないことを明確にしてください。
-->

## hook とは — AI のライフサイクルイベントに処理を差し込む仕組み

```
┌───────────────────────────────┐
│  普段は何もしない (静観)        │
│                               │
│  特定のライフサイクル          │
│  イベントが起きた瞬間に発火     │
│  → 任意の処理を実行            │
└───────────────────────────────┘
```

**hook = AI のライフサイクルイベント** (セッション開始 / プロンプト送信 / ツール実行前後 / 圧縮前 / 終了等) **に任意の処理を差し込む Claude Code 公式機能**

- ライフサイクルイベントは **全 29 種類** (本章は代表抜粋)
- 差し込める処理: シェルコマンド・HTTP 呼出・MCP ツール・プロンプト等
- 用途: 安全装置・関連資料注入・自動テスト・通知 等 (安全装置は代表的用途の一つに過ぎない)

---

<!--
スピーカーノート:
代表的な 4 つの hook を一覧で示す。「全タイミング網羅」とは断定しない (公式 hook は全 29 種類で、本章は実用度の高い代表 4 つを抜粋)。受講者には「公式は 29 種類あるが、まずこの 4 つを押さえれば実用的な自動化が組める」と伝えてください。
-->

## 主要 hook の発火タイミング (公式 29 種類中の代表抜粋)

| hook | いつ発火するか | 何に使うか |
|--------|--------------|-----------|
| **SessionStart** | セッション開始時 | ルールを自動で読み込む |
| **PreToolUse** | ツール実行の **直前** | 「本当に実行していいか」検査 |
| **PostToolUse** | ツール実行の **直後** | 「本当に成功したか」検証 |
| **UserPromptSubmit** | プロンプト送信時 | 関連資料を自動で探す |

> ⚠️ Claude Code 公式 hook は **全 29 種類** (SessionStart / PreToolUse / PostToolUse / UserPromptSubmit / SubagentStop / Notification / PreCompact / PostCompact / Stop / SessionEnd ほか)。本章では実用度の高い 4 つを抜粋して解説します。全種類の一覧は公式 hooks ドキュメントを参照してください。

---

## SessionStart — セッション開始時に自動読込

### 何が起きるか
AI を起動した瞬間に、**自動でルールを読み込む**

### 実例
```
# セッション開始 → 自動で以下が読み込まれる
- プロジェクトの基本ルール (CLAUDE.md)
- 役割別の指示 (instructions/*.md)
- 過去の判断・教訓 (memory/)
```

### 効果
- 毎回「このプロジェクトのルールは…」と説明しなくていい
- AI が **最初からルールを知った状態** で作業を始める
- ch05 の役割別ファイルが自動で読み込まれる

> ※ `instructions/<role>.md` は VSCode + GitHub Copilot 公式の `.github/instructions/NAME.instructions.md` 規約に着想を得て、Claude Code 用にアレンジした本リポジトリ独自運用 (ch05 で扱った)

---

## PreToolUse — 実行前に「本当にいいか?」を検査

### 何が起きるか
AI がツール (ファイル編集・コマンド実行等) を使う **直前** に検査が走る

### 実例: 危険なコマンドを自動阻止
```
AI が実行しようとしたコマンド: rm -rf /
                              ↓
PreToolUse hook が発火
→「この操作は禁止リストに含まれています」
→ 実行をブロック
```

### 効果
- 「この操作は禁止」と宣言した操作に **実行時の強制力** を与える (→ ch08 で詳細)
- 「止めろ」と言ったのに進む問題が解決する

---

## PostToolUse — 実行後に「本当に成功したか?」を検証

### 何が起きるか
AI がツールを使った **直後** に検証が走る

### 実例: API 変更後の自動テスト
```
AI がコードを編集した
              ↓
PostToolUse hook が発火
→ テストを自動実行
→ 失敗すれば即座に通知
```

### 効果
- **⑧ API 変更後にテストせず壊れる** の直接解決
- 「テストし忘れた」が起きない — hook が勝手に走るから

---

<!--
スピーカーノート:
本章の核心スライド。UserPromptSubmit は「プロンプト送信時に自動で検索」する hook。ch04 で手動で叩いていた検索コマンドが、この hook 1 つで完全自動化されることを強調。Lost in the Middle（長文読み飛ばし）対策も「人手で長文を貼らなくていい＝貼らないから読み飛ばしも起きない」という二重の効果がある点を説明してください。なお、UserPromptSubmit hook が「関連資料を自動注入する」のは hook の代表的用途の一つであり、hook 全体の定義ではないことに注意。
-->

## UserPromptSubmit — 入力時に自動検索 (★ 本章の核心)

### 何が起きるか
あなたがプロンプトを送信した瞬間に、**関連する資料を自動で探して読み込む**

```
あなたが入力: 「A 社の提案書を書いて」
              ↓
UserPromptSubmit hook が発火
→「A 社」が含まれるファイルを自動検索
→ 関連する過去の議事録・要望を自動で注入
              ↓
AI が回答: A 社の過去の要望を踏まえた提案書
```

### 効果
- **⑨ 大事なドキュメントを確認しない** の直接解決
- ch04 の「手動で検索」が **自動化** された

---

## ch04 の検索が自動化された瞬間

```
┌─────────────────────┐       ┌─────────────────────┐
│  ch04 [手動版]       │       │  ch07 [自動版]       │
│                     │       │                     │
│  毎回検索コマンド   │ ──→   │  UserPromptSubmit    │
│  を手で叩く         │       │  が勝手に検索する     │
│                     │       │                     │
│  「便利だけど面倒」  │       │  「意識しなくていい」 │
└─────────────────────┘       └─────────────────────┘
```

> 同じ技術が、**手動 → 自動** へ進化した
> 長文読み飛ばし (Lost in the Middle) 対策も自動化 — 人手で長文を貼らなくていい

---

## 実例 — 営業の顧客対応 (UserPromptSubmit)

### Before
- 「A 社の提案書を書いて」と頼む
- 毎回 A 社の議事録・要望をコピペするのが面倒
- 貼らなくなった → AI が古い情報で提案 → ズレる

### After (hook 導入)
```
入力: 「A 社の提案書を書いて」
→ hook が自動で「A 社」関連ファイルを検索
→ 過去の議事録・要望・クレーム履歴を自動注入
→ AI が最新情報に基づいた提案書を作成
```

**置換**: 自社の顧客名・案件名に置き換えて即応用

---

## 実例 — PM の仕様変更確認 (PostToolUse)

### Before
- API の仕様書が更新されたのに AI が古い仕様でコードを書いた
- テストもせずコミット → 本番でシステムエラーが発生

### After (hook 導入)
```
AI がコードを編集
→ PostToolUse hook が発火
→ テストを自動実行
→ 失敗すれば即座に「テストが落ちました」と通知
```

**置換**: 自社の API・テストコマンドに置き換えて即応用

---

## 実例 — データ分析の安全確認 (PreToolUse)

### Before
- 分析用 SQL を実行する前に毎回「本番 DB じゃないか?」「WHERE 句はあるか?」を手動確認
- 面倒だから確認をスキップ → 本番で事故

### After (hook 導入)
```
AI が SQL を実行しようとした
→ PreToolUse hook が発火
→ 本番 DB への接続 / WHERE なし DELETE を検知
→「危険な操作です。実行をブロックします」
```

**置換**: 自社の DB 名・禁止パターンに置き換えて即応用

---

<!--
スピーカーノート:
設定ファイルの書き方を実例で示す。settings.json に数行書くだけで hook が有効になる手軽さを強調。matcher で「ファイル編集時だけ」「コマンド実行時だけ」と絞り込める点と、書き間違えてもエラーが出るだけで壊れない安全性を説明。受講者に「自分でもできそう」と思わせるのがこのスライドの目的です。
-->

## hook の設定方法

プロジェクトの設定ファイルに書くだけ。場所は `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash scripts/check_dangerous.sh"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "bash scripts/auto_test.sh"
      }
    ],
    "UserPromptSubmit": [
      {
        "command": "bash scripts/auto_grep_docs.sh"
      }
    ]
  }
}
```

- ファイルがなければ新規作成、既にあれば追記
- `matcher` で「ファイル編集時だけ」「コマンド実行時だけ」等を絞り込める
- 書き間違えてもエラーが出るだけで壊れないので安心して試せる

---

<!--
スピーカーノート:
hook スクリプトの引数受取仕様。コマンド型の hook は stdin から JSON ペイロードを受け取る。$1 や $CLAUDE_TOOL_INPUT 環境変数は公式仕様には存在しない (コピペすると動作しない致命傷)。受講者がコピペで動くスクリプトを書けるよう、常套句として覚えてもらってください。
-->

## hook スクリプトの引数受取 (★ 公式仕様)

hook の `command` で呼ばれるシェルスクリプトは **stdin から JSON ペイロード** を受け取る。

```bash
#!/bin/bash
# hook スクリプトの正しい引数受取
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
# または: COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)
```

- `$1` でコマンド内容を受け取る ❌ (公式仕様に存在しない)
- `$CLAUDE_TOOL_INPUT` 環境変数で受け取る ❌ (公式仕様に存在しない)
- **stdin JSON 一択** ✅

> コピペで動かないスクリプトの大半は引数受取ミスが原因。`INPUT=$(cat); jq -r '...'` を常套句として覚えてください。

---

<!--
スピーカーノート:
ここから章の後半への転換点。hook は便利だが「いつでも同じ処理」しかできない限界を提示。本当は「この場面ではどの処理を呼ぶべきか」を AI に判断してほしい、という欲求につなげる。Skill との連携がその解決策であることを予告し、ch11 の「自分専用 Skill を作る」への期待感を高めてください。
-->

## hook 単体の限界

hook は「いつでも同じ処理」を発動させる:

```
PreToolUse → いつも同じ危険チェック
PostToolUse → いつも同じテスト実行
```

**でも本当はやりたいこと:**
> 「この場面では **どの処理** を呼ぶべきか」を AI に自律判断してほしい

これを実現するのが **Skill との連携**。

> **Skill とは**: AI が呼び出せる「業務専用の再利用可能なワークフロー定義」(オンデマンド読込)。
> カスタムスラッシュコマンド (`.claude/commands/<name>.md`) の上位互換 —
> 標準形式は `.claude/skills/<skill-name>/SKILL.md` (ディレクトリ + SKILL.md エントリポイント)。
> 公式は「カスタムコマンドはスキルにマージされました」と明記しており、
> AI が文脈 (description のキーワードマッチ) に応じて自律判断で呼び出します (詳細は ch11)

---

## Skill が hook と連携する仕組み

```
┌────────────────────┐         ┌────────────────────┐
│  hook (引き金)      │ ──発火─→ │  Skill の判定       │
│                    │         │                    │
│  「プロンプト送信時」│         │  「この場面では     │
│                    │         │   どの Skill が    │
│                    │         │   呼ばれるべきか」  │
└────────────────────┘         └─────────┬──────────┘
                                         │
                                         ▼
                               ┌────────────────────┐
                               │  Skill 起動         │
                               │  (業務知識を実行)   │
                               │  → 「議事録要約」   │
                               │  → 「顧客提案書」   │
                               │  → 「データ分析」   │
                               └────────────────────┘
```

---

## hook × Skill の 3 段階比較

| 段階 | 何が動くか | 例 |
|------|----------|-----|
| **hook 単体** | いつも同じ処理 | ファイル編集後にテスト実行 |
| **Skill 単体** | AI が文脈で選ぶ | 「議事録要約して」→ 議事録要約 Skill を呼ぶ |
| **hook + Skill** | 特定タイミングで AI が Skill を選ぶ | prompt 送信時に「関連 Skill を検索してから実行」を強制 |

> ch11 で「**自分専用の Skill を作る**」演習に直結します

---

<!--
スピーカーノート:
ここから実践ケーススタディ。ch06 で学んだ advisor は任意発動＝ AI が skip することもある。これを PostToolUse hook で「確実に効かせる」実装例として done_gate.sh を紹介します。本プロジェクトで実際に使っているコードなので、リアリティがあります。「公式機能だけでどこまでできるか」と「独自ロジックでどこまで拡張できるか」の二層構造を明確に説明してください。
-->

## ケーススタディ — 任意発動を hook で間接強制する

> ch06 で学んだ advisor は AI が **skip できる**
> → 「skip されたら困る」場面では hook で **間接的に強制** できる

```
ch06 advisor (任意発動)          ch07 PostToolUse hook (強制発動)
         │                                   │
         └── skip あり ──→ どうする? ──→  hook で完了ゲートを立てる
```

---

<!--
スピーカーノート:
二層構造の明示スライド。上が Claude Code 公式機能、下が本プロジェクト独自の検査ロジック。この分離が重要な理由: 受講者はまず公式機能を理解し、その上で独自ロジックで拡張できることを知る必要がある。done_gate.sh はあくまで応用例であり、本プロジェクト固有のものです。
-->

## 二層構造 — 公式 hook + 独自ゲート

```
┌─────────────────────────────────────────────┐
│  PostToolUse hook (Claude Code 公式機能)     │
│  → ファイル編集後に自動発動する仕組み自体     │
│    は Claude Code の公式機能                 │
├─────────────────────────────────────────────┤
│  done_gate.sh (本プロジェクト独自の検査)     │
│  → hook から呼ばれる検査ロジックの中身は      │
│    プロジェクトごとに自作する                 │
└─────────────────────────────────────────────┘
```

- **上の層** (公式): hook の発火タイミング・設定方法 — Claude Code が提供
- **下の層** (独自): 何を検査するか — プロジェクトごとに設計

---

<!--
スピーカーノート:
done_gate.sh の仕組みを流れ図で説明。PostToolUse hook が発火→ posttool_verify_runner.sh → done_gate.sh → advisor 未呼出なら BLOCK。この連鎖を理解してもらう。L139 の実コードも見せるので、その前に全体像を把握させます。
-->

## done_gate.sh の仕組み

```
AI が task YAML を編集 (status: done にしようとした)
              │
              ▼
PostToolUse hook が発火
              │
              ▼
posttool_verify_runner.sh が起動
              │
              ▼
done_gate.sh が advisor 呼出回数を確認
              │
    ┌─────────┼─────────┐
    ▼                   ▼
advisor 2回以上       advisor 0〜1回
   呼出済               呼出なし
    │                   │
    ▼                   ▼
  exit 0              exit 2 (BLOCK)
  (done 許可)         「advisor を呼んでから
                      status: done にせよ」
```

---

<!--
スピーカーノート:
実際のコード引用スライド。done_gate.sh L139 の実コードを見せる。意味は「advisor 呼出回数が 2 回未満なら BLOCK する」。2 回という数字は「実装前＋完了前」の 2 回を想定。コードが短くて意図が明確であることを強調してください。さらに、これが Anthropic 公式概念の「ハーネス」(Agent = Model + Harness) における典型的な実装パターンの一つであることを位置付けます。
-->

## 実コード引用 — done_gate.sh

```bash
# done_gate.sh 抜粋 (L138-142)
if [ "$ADVISOR_COUNT" -lt 2 ]; then
  echo "BLOCK: ${TASK_ID} advisor 呼出 ${ADVISOR_COUNT} 回" \
       "(必須 2 回: 実装前 + 完了前)" >&2
  echo "対応: advisor() を呼んでから status:done にせよ" >&2
  exit 2
fi
```

**このコードがやっていること:**
1. advisor の呼出ログを数える
2. 2 回未満なら **BLOCK** (done 不許可)
3. 理由を stderr に書いて AI に伝える

> advisor (任意発動) を hook で間接強制する = **Anthropic 公式概念の「ハーネス」(Agent = Model + Harness) における典型的な実装パターンの一つ**
>
> ※ ハーネスは Anthropic Engineering Blog (「Effective harnesses for long-running agents」2025-11) で扱われる業界標準用語。プロンプト・ツール・hooks・サブエージェント・回復経路等で Claude を「実際に仕事を完遂する work engine」に変える層をハーネス層と呼ぶ。本リポジトリの done_gate.sh はそのハーネスの一実装例

---

## この章の振り返り

- hook = AI のライフサイクルイベント (公式 **全 29 種類**) **に処理を自動挿入** する仕組み
- 代表 4 つを学んだ (SessionStart / PreToolUse / PostToolUse / UserPromptSubmit)
- **PreToolUse** → 危険な操作を **実行前に阻止**
- **PostToolUse** → テスト忘れを **実行後に検証**
- **UserPromptSubmit** → ch04 の検索を **自動発動** (長文読み飛ばしの自動対策)
- **引数受取** → stdin JSON 一択 (`$1`・環境変数は公式仕様に無い)
- Skill と連携すれば、AI が **自律的に必要な道具を呼ぶ** ようになる
- **ケーススタディ**: advisor を hook で間接強制する done_gate.sh (公式 hook + 独自検査の二層構造)

---

## ch07 まとめ

**言える 1 文:**
> hook で AI のライフサイクルイベントに処理を差し込めば、テスト忘れも資料確認忘れも防げる

**ケーススタディ (done_gate.sh):**
> advisor (任意発動・ch06) を PostToolUse hook で間接強制する実装例
> — 公式 hook + 独自検査ロジックの二層構造
> — Anthropic 公式概念の「ハーネス」(Agent = Model + Harness) における典型的な実装パターン

**次章への橋渡し:**
> ch08 では「黙って失敗する」AI を能動的に検知する仕組みと、
> 止めるべき操作を宣言的に阻止する仕組みを学びます。
> 本章の PreToolUse hook がその **実行時の強制力** を担います。

**参考**:
- [Claude Code Hooks 公式ドキュメント](https://docs.anthropic.com/en/docs/claude-code/hooks) (全 29 種類のイベント一覧)
- [Effective harnesses for long-running agents (Anthropic Engineering Blog, 2025-11)](https://www.anthropic.com/engineering)

**強化した層: ハーネス層 (L3)** — Anthropic 公式概念のハーネス層を hook で自動化し、Skill 連携の入口に立った

---

<!-- _class: cover -->

# 第7章 完了
## 次は 第8章「黙る AI を能動的に検知する」

<div class="meta">
✅ 公式 29 種類の hook から代表 4 つを習得した<br>
✅ UserPromptSubmit で ch04 の検索を自動発動できる<br>
✅ hook の引数受取は stdin JSON 一択 (コピペで動く)<br>
✅ Skill と連携すれば AI が自律的に道具を選べる<br>
✅ done_gate.sh で advisor を間接強制する Anthropic 公式ハーネスの実装例を知った<br><br>
<b>続けて第8章をお楽しみください</b>
</div>
