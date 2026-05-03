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

# PreToolUse Phase-Gating
## タスク起票前の自動検証

<div class="meta">
中級編 v4 — 第13章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第13章へようこそ。この章ではPreToolUse Phase-Gatingを解説します。AIエージェントが新しいタスクを開始する前に、自動で過去の類似事例を検索し、安全に作業を開始できるかを確認する仕組みです。Bounded Deterministic Workflowsの考え方をベースに、AIの振る舞いを予測可能にする手法を学びます。なぎなたと申します。
-->

---

## この章で学ぶこと [L3: Create]

1. **PreToolUse hook** の概念と登録方法を説明できる
2. **Phase-Gating** によるタスク開始前の自動検証を設計できる
3. **セマンティック検索パイプライン** の3段階を理解する
4. **Bounded Deterministic Workflows** の考え方を説明できる
5. **検索精度のチューニング** 方法を理解する

<!--
この章では5つの到達点を目指します。PreToolUse hookの概念と登録方法、Phase-Gatingによるタスク開始前の自動検証設計、セマンティック検索パイプラインの3段階、Bounded Deterministic Workflowsの考え方、検索精度のチューニング方法を学びます。Bloomの分類で言えばCreateレベル、実際の設計と実装を理解するレベルです。
-->

---

# 「同じ問題を2度解いていませんか？」

> AIエージェントはセッションをまたぐと、過去に解決した問題を忘れます。
> 1ヶ月前に直したバグと同じ調査を、また最初からやり直している。

- コンテキストウィンドウには限界がある
- すべての過去履歴を常時ロードすることは不可能
- **必要なときに必要な過去事例だけを自動検索する仕組み** が必要

<!--
このスライドがつかみです。AIエージェントを使って開発していると、セッションをまたぐたびに過去の解決履歴がリセットされます。同じバグの調査を何度も繰り返す無駄をなくすためには、タスク開始時に自動で過去事例を検索する仕組みが必要です。これがPreToolUse Phase-Gatingの動機です。
-->

---

# PreToolUse Hook — ツール実行前の自動介入

**PreToolUse hook** = AIがツール（Write, Edit等）を呼び出す直前に実行される処理

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "bash scripts/search_and_validate.sh"
      }
    ]
  }
}
```

- **matcher**: どのツール呼出で発火するか
- **command**: 発火時に実行するスクリプト
- **ユースケース**: 過去事例検索、バリデーション、安全性確認

<!--
PreToolUse hookの基本概念です。AIがツールを呼び出す直前に、指定したスクリプトが自動実行されます。matcherで発火条件を指定し、commandで実行する処理を定義します。この仕組みを使えば、AIがファイルに書き込む前に過去事例を自動検索したり、入力をバリデーションしたりできます。
-->

---

# Phase-Gating — フェーズ間の品質関門

**Phase-Gating** = あるフェーズが完了するまで次フェーズに進めない品質管理手法

| 手法 | 役割 | 適用タイミング |
|------|------|---------------|
| **PreToolUse Gate** | 実行前の条件確認 | ツール呼出直前 |
| **PostToolUse Gate** | 実行後の結果検証 | ツール完了直後 |
| **Session Gate** | セッション境界の整合性 | /clear後の復旧時 |

- Phase-Gatingをhookに組み込むことで **AIの振る舞いを予測可能に** する
- 人間のレビュー待ちなしに **自動で品質を担保** できる

<!--
Phase-Gatingの概念です。元は製造業の品質管理手法で、あるフェーズが品質基準を満たすまで次フェーズに進めない仕組みです。これをAI開発に応用し、PreToolUse、PostToolUse、Sessionの3つのタイミングで品質関門を設けます。hookに組み込むことで、人間の介入なしにAIの振る舞いを予測可能にできます。
-->

---

# Bounded Deterministic Workflows

**Bounded Deterministic Workflows** = AIの振る舞いを境界づけられた確定的なフローに制約する設計パターン

- **Bounded**: AIが取りうる行動の範囲を明示的に制限
- **Deterministic**: 同じ入力に対して同じ結果を返す
- **Workflow**: 一連の処理を定義された順序で実行

> **設計原則**: AIの自由度を下げるのではなく、**安全な範囲内で最大限の自由度を確保する**

| 無制約 | Bounded Deterministic |
|--------|----------------------|
| AIが任意の操作を実行可能 | 許可された操作のみ実行 |
| 結果が予測不能 | 同じ条件で同じ結果 |
| デバッグが困難 | ログで原因追跡が容易 |

<!--
Bounded Deterministic Workflowsは、AIの振る舞いを境界づけられた確定的なフローに制約する設計パターンです。Boundedは行動範囲を制限し、Deterministicは同じ入力に同じ結果を返し、Workflowは処理順序を定義します。AIの自由度を下げるのではなく、安全な範囲内で最大限の自由度を確保するのが狙いです。Phase-Gatingはこのパターンの具体的な実装手法の一つです。
-->

---

# セマンティック検索パイプライン

**3段階のパイプライン**で過去事例を自動検索:

| 段階 | 処理 | 役割 |
|------|------|------|
| **1. 抽出** | タスク情報からキーワードを抽出 | 検索クエリの生成 |
| **2. 検索** | メモリバックエンドを検索 | 過去事例の発見 |
| **3. 注入** | 検索結果をコンテキストに注入 | AIが過去事例を認識 |

- この3段階を **PreToolUse hook** として自動化
- タスク開始前に必ず過去事例を検索 — 人間の介入なし

<!--
セマンティック検索パイプラインの全体像です。第1段階はキーワード抽出、第2段階はメモリバックエンドの検索、第3段階は結果のコンテキスト注入です。この3段階をPreToolUse hookとして登録しておけば、新しいタスクを開始するたびに自動的に過去事例が検索されます。
-->

---

# ハイブリッド検索 — キーワード + セマンティック

| 検索方式 | 特徴 | 用途 |
|---------|------|------|
| **キーワード検索** | 高速・精密一致 | 固有名詞・コマンド名 |
| **セマンティック検索** | 意味ベースの類似度 | 概念的な関連事例 |
| **ハイブリッド** | 2方式の組み合わせ | 表現ゆれに強い検索 |

- **Embedding類似度** で意味的な関連性を計測
- 上位N件（通常3〜5件）を結果として返す
- 注入量は **1件あたり200トークン程度** に制限

<!--
メモリ検索の仕組みです。キーワード検索とセマンティック検索の2方式をハイブリッドで使います。キーワード検索はコマンド名や固有名詞に強く、セマンティック検索は意味的な類似性で「SQLiteの移行」と「データベースの引越し」のような表現ゆれに対応できます。2方式を組み合わせることで精度の高い検索が可能です。
-->

---

# hit=0 — 「過去事例なし」の警告

> 検索結果が0件だった場合、それは情報ではなく **警告** です。

- **hit=0 の3パターン**:
  - 初回の問題（新規性が高い）→ 正常
  - 過去に解決済みだが記録漏れ → 問題
  - キーワード抽出の不適切 → チューニング必要

- **警告注入の仕組み**:
  ```
  [search] Warning: 過去事例なし — 新規問題の可能性
  → 完了後に必ずメモリに記録すること
  ```

- **設計意図**: 記録漏れを自動検知し、**知識蓄積サイクルを閉じる**

<!--
検索結果が0件だった場合の対応です。hit=0は単なる結果なしではなく、文脈によって意味が変わります。初回の新規問題なら正常ですが、過去に解決済みなのに記録されていなければ問題です。hit=0のときは警告を注入し、タスク完了後の記録を促すことで知識蓄積サイクルを閉じます。
-->

---

# タスク定義スキーマの拡張

検索動作をタスク定義ファイルで制御する拡張:

```yaml
task_id: task_1595
description: "Phase-Gatingハーネスの設計"
search_config:
  enabled: true
  keywords: ["Phase gate", "ハーネス"]
  exclude_keywords: ["初心者", "入門"]
  max_results: 5
```

| フィールド | 役割 | デフォルト |
|-----------|------|-----------|
| `enabled` | 検索の有効/無効 | `true` |
| `keywords` | 手動指定キーワード | 自動抽出 |
| `exclude_keywords` | 除外キーワード | なし |
| `max_results` | 最大結果件数 | 3 |

> **設計思想**: 自動抽出を基本としつつ、**手動での微調整** を可能にする

<!--
タスク定義スキーマの拡張です。search_configフィールドを追加することで検索動作を制御できます。enabledで有効無効、keywordsで手動指定、exclude_keywordsで除外、max_resultsで件数制限を設定します。自動抽出を基本としつつ手動で微調整できる柔軟性を持たせています。
-->

---

# プロジェクト実装例

> **本講座サンプル実装**: 以下は具体例です。概念の理解に役立ててください。

```
Step 1: キーワード抽出 → "SQLite", "監査", "スクリプト"
Step 2: メモリ検索 → 3件ヒット
Step 3: 結果注入 ↓

[search] 過去3件の類似事例を発見:
  1. "SQLite dual-path実装" → dual-path書込パターン
  2. "SQLite p1初期導入" → 導入時のエラーと対処法
  3. "SQLite書込改修" → 具体的コード例
```

- AIは過去事例を参照し、**同じエラーを回避** しながら実装可能
- 1ヶ月前に解決した問題を、最初からやり直す必要がなくなる

<!--
プロジェクトの実装例です。「SQLite監査スクリプト追加」というタスクを起票したシナリオで、キーワードが自動抽出され、メモリ検索で3件の過去事例が発見されました。AIはこの情報を参照することで、過去に遭遇したエラーを回避し、実装パターンを再利用できます。これがPreToolUse Phase-Gatingの価値です。
-->

---

# 検索精度のチューニング — 5つの調整ポイント

| # | 調整ポイント | 方法 | 効果 |
|---|------------|------|------|
| 1 | **キーワード重み** | description > notes > task_id | 重要フィールドを優先 |
| 2 | **除外キーワード** | 汎用語を除外 | ノイズ削減 |
| 3 | **結果件数** | `max_results` を調整 | コンテキスト消費の制御 |
| 4 | **Embedding モデル** | より高精度なモデルに変更 | 意味検索の精度向上 |
| 5 | **類似度閾値** | 最低閾値を設定 | 低関連事例の除外 |

> **チューニングのコツ**: デフォルト設定で1週間運用 → ログ分析 → 1点ずつ調整

<!--
検索精度のチューニング方法です。5つの調整ポイントがあります。キーワード重み付け、除外キーワード、結果件数、Embeddingモデル、類似度閾値の順に調整できます。コツはデフォルト設定で運用してログ分析してから1点ずつ調整することです。一度に全部変えると、どの変更が効果的だったか分からなくなります。
-->

---

# この章のまとめ

- **PreToolUse hook** = ツール実行前に自動発火する仕組み
- **Phase-Gating** = フェーズ間の品質関門でAIの振る舞いを予測可能に
- **Bounded Deterministic Workflows** = AIの行動範囲を制約する設計パターン
- **セマンティック検索パイプライン** = 抽出 → 検索 → 注入の3段階
- **hit=0 警告** = 知識蓄積サイクルを閉じる仕組み

<!--
この章のまとめです。PreToolUse hookの概念、Phase-Gatingによる品質関門、Bounded Deterministic Workflowsの設計パターン、セマンティック検索パイプライン、hit=0警告の仕組みを学びました。これらを組み合わせることで、AIエージェントが安全かつ効率的にタスクを開始できるようになります。
-->

---

# 確認問題

**Q1**: PreToolUse hookが発火するタイミングはいつか？
- A: ユーザーがプロンプトを入力したとき
- B: AIがツール（Write等）を呼び出す直前
- C: セッションが開始されたとき

**Q2**: Bounded Deterministic Workflowsの「Bounded」の意味として正しいものは？
- A: AIの実行速度に上限を設ける
- B: AIが取りうる行動の範囲を明示的に制限する
- C: コンテキストウィンドウのサイズを固定する

**Q3**: hit=0の警告の設計意図として最も適切なものは？
- A: 検索機能の故障を通知する
- B: 新しいタスクの重要性を強調する
- C: 完了後の記録を促し、知識蓄積サイクルを閉じる

<!--
確認問題です。Q1、PreToolUse hookが発火するのはAIがツールを呼び出す直前です。正解はBです。Q2、Bounded Deterministic WorkflowsのBoundedはAIが取りうる行動範囲を制限する意味です。正解はBです。Q3、hit=0の警告は完了後の記録を促すことで知識蓄積サイクルを閉じるためのものです。正解はCです。
-->

---

<!-- _class: cover -->

# 第13章 完了!
## PreToolUse Phase-Gatingを理解したか?

**到達点チェック**:
- ✅ PreToolUse hookの概念と登録方法を説明できる
- ✅ Phase-Gatingによる自動検証を設計できる
- ✅ セマンティック検索パイプラインの3段階を理解している
- ✅ Bounded Deterministic Workflowsの考え方を説明できる
- ✅ 検索精度のチューニング方法を理解している

**次章**: PostToolUse Supervisor — フィードバック自動化パターン

<div class="meta">
講師: なぎなた
</div>

<!--
第13章完了です。PreToolUse Phase-Gatingの仕組みを理解できましたか。到達点を振り返りましょう。PreToolUse hookの概念、Phase-Gatingによる自動検証、検索パイプライン、Bounded Deterministic Workflows、チューニング方法の5つを理解できていれば完璧です。次章ではPostToolUse Supervisorによるフィードバック自動化パターンを解説します。
-->
