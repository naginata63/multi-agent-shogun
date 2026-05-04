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
  .vocab-box { background: #eff6ff; border: 2px solid #3b82f6; border-radius: 8px; padding: 0.5em 0.8em; }
  .vocab-box h3 { color: #1e3a8a; margin: 0 0 0.3em 0; }
---

<!-- _class: cover -->

# 永続コンテキスト層 (Select戦略)
## LangChainの「選択戦略」でAIに忘れない記憶を与える

<div class="meta">
中級編 v4 — 第6章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第6章へようこそ。この章では永続コンテキスト層をLangChainのSelect戦略の観点から解説します。前章のWrite戦略ではAIに正しい情報を書き込む方法を学びました。本章のSelect戦略は、蓄積された情報から必要なものだけを選択して取り出す手法です。RAGやSupervisor Patternといった業界標準の概念も登場します。40分間、一緒に学んでいきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと

1. **Select戦略**（選択戦略）— 必要な情報を必要な時に取り出す仕組み
2. **3つの保存先**（バックエンド）の特徴と使い分け
3. **4カテゴリ分類** — 情報の種類ごとに管理方法を変える考え方
4. **監督者パターン**（Supervisor Pattern）— 記憶の品質を保つ仕組み
5. **肥大化防止** — メモリに書きすぎないための判断基準

<!--
この章では5つの到達点を目指します。Select戦略は前章のWrite戦略の次のステップで、保存した情報から必要なものを取り出す手法です。3つの保存先を比較し、情報を4つのカテゴリに分類する考え方、監督者パターンによる品質管理、そして肥大化を防ぐ判断基準まで扱います。
-->

---

## この章で出てくる用語

<div class="vocab-box">

| 用語 | 意味 |
|------|------|
| **Select戦略（選択戦略）** | 保存された情報から、必要なものだけを選んで取り出す手法 |
| **RAG** | 外部の知識ベースから関連情報を検索してAIに渡す仕組み。「ラグ」と読む |
| **バックエンド** | 情報を保存する「場所」のこと。データの保管先 |
| **セマンティック検索** | キーワードの一致だけでなく「意味」で探す検索方法 |
| **監督者パターン** | 記憶の読み書きを監督し、品質を保つ仕組み |
| **カテゴリ分類** | 情報を「ユーザー」「指摘」「プロジェクト」「参照」の4種に分ける考え方 |

</div>

<!--
この章で初めて出てくる用語をまとめました。全部で6つ。前章で学んだコンテキストウィンドウ、トークン、Goldilocks Zoneの知識が前提になります。まずはざっと目を通すだけでOKです。この後のスライドで一つずつ丁寧に説明します。
-->

---

# 「覚えてないの？」— Writeだけでは不十分

> AI「了解しました。そのファイルを修正します」
> （翌日）
> あなた「昨日の修正、続きを頼みたいんだけど」
> AI「はい、まず前提を教えてください」— **すべて忘れている**

- 前章のWrite戦略: AIに **書き込む** 情報を最適化する手法
- しかし `/clear` や新セッションで **書き込んだ情報もリセットされる**
- **必要な情報を必要な時に選択して取り出す** 仕組みが必要
- それが **Select戦略** である

<!--
つかみです。Write戦略で情報を最適化しても、/clearや新規セッションでリセットされれば元も子もありません。必要な情報を必要な時に選択して取り出す仕組みが必要です。それが本章のテーマ、Select戦略です。AIに忘れない記憶を与える仕組みを解説します。
-->

---

# Select戦略と RAG — 業界標準のアプローチ

まず簡単な例えから始めましょう。**RAG**（ラグ）は「辞書を引いてから答える」仕組みです:

> **日常の例え**: テストで「わからない問題」に出会したら、教科書やノートを開いて関連ページを探し、そこに書いてあることを参考にして回答を書きますよね。RAGはAIにこの「教科書を開いて調べる」ことをさせる仕組みです。

| 項目 | 意味 |
|------|------|
| **R = Retrieval（検索）** | 保存しておいたデータから関連情報を探す |
| **A = Augmented（拡張）** | 見つけた情報をAIへの質問に付け足す |
| **G = Generation（生成）** | 拡張された情報を元にAIが回答を作る |

> **Select戦略とRAGの関係**: Select戦略はRAGを含む広い概念。Claude CodeでのRAG実装がSelect戦略の一例

<!--
Select戦略とRAGの関係を説明します。まずRAGを日常の例えで説明しましょう。テストでわからない問題があったら教科書やノートを開いて調べますよね。RAGはAIにこの「教科書を開いて調べる」ことをさせる仕組みです。正式名称はRetrieval-Augmented Generationですが、最初は「辞書を引いてから答える仕組み」と覚えてください。Select戦略はRAGを含む広い概念で、Claude CodeでのRAG実装がSelect戦略の具体例の一つです。
-->

---

# 3つの保存先（バックエンド）

AIの記憶を保存する場所には3つの選択肢があります:

| 保存先 | 仕組み | 強み | 向いている用途 |
|------------|--------|------|---------------|
| **Claude Code memory** | 専用ファイルに自動保存 | 標準機能・設定不要 | ユーザー設定・基本ルール |
| **MCP memory** | 外部サーバー経由で保存 | 構造化データの保存・共有 | プロジェクト固有データ |
| **claude-mem** | データベース＋意味検索 | 大量の過去事例を高速検索 | 過去の解決策を探す |

> **Select戦略の基本**: どの保存先から、何を、いつ取り出すかを設計する

<!--
AIの記憶を保存する場所（バックエンド）は3つあります。一番シンプルなのはClaude Code memoryで、設定不要ですぐ使えます。MCP memoryは外部サーバー経由で構造化データを保存・共有できます。claude-memはデータベースと意味検索を組み合わせて、大量の過去事例を高速に検索できます。Select戦略では、これらの保存先から何をいつ取り出すかを設計します。
-->

---

# Claude Code memory — Select戦略の最もシンプルな実装

**仕組み**: `memory/MEMORY.md` に書くだけで、次回セッションで自動Select

- **自動Select**: 新セッション開始時に MEMORY.md が自動的にコンテキストに含まれる
- **手動Write**: AIに「これを覚えて」と指示するだけで更新される
- **階層構造**: `memory/*.md` に個別ファイルを作成し、MEMORY.md に索引を書く

```
memory/
  MEMORY.md           <- 索引 (自動Select対象)
  feedback_xxx.md     <- フィードバック記録
  project_notes.md    <- プロジェクト固有情報
```

> **メリット**: 設定不要・標準機能 / **デメリット**: 200行制限・検索機能なし

<!--
Claude Code memoryはSelect戦略の最もシンプルな実装です。MEMORY.mdに情報を書くだけで、次回セッション開始時に自動的に選択されてコンテキストに含まれます。個別のトピックごとに別ファイルを作成し、MEMORY.mdには索引を書くのが推奨される構成です。シンプルですが、200行制限があり検索機能もありません。大量の情報を管理するには他のバックエンドと組み合わせます。
-->

---

# RAG実践 — claude-mem によるセマンティック検索

> 本講座サンプル実装

本講座では **claude-mem** (SQLite + Gemini Embedding) をRAGバックエンドとして使用:

- **SQLite** = データベース（情報を整理して保存する仕組み）の一種
- **Gemini Embedding** = テキストの「意味」を数字の並び（ベクトル）に変換する仕組み

```
検索クエリ → Gemini Embedding API → ベクトル化
→ SQLite内のベクトルと類似度比較 → 上位N件を返却
```

| 操作 | コマンド |
|------|---------|
| 記憶の保存 | `mem-search search → timeline → get_observations` ※実際の運用で使うコマンド例です |
| 記憶の検索 | セマンティック検索で関連事例を自動取得 |
| 記憶の構造化 | smart_outline / smart_search / smart_unfold |

> **Select戦略の高度な実装**: セマンティック検索で「キーワード一致」を超えた文脈検索が可能

<!--
本講座でのRAG実装例を紹介します。claude-memはSQLiteデータベースとGemini Embedding APIを使ったセマンティック検索バックエンドです。検索クエリをベクトル化し、データベース内のベクトルと類似度を比較して関連事例を取得します。単なるキーワード一致ではなく、意味的な関連性に基づく検索が可能です。これがSelect戦略の高度な実装で、LangChainのRAGと同じ考え方に基づいています。
-->

---

# Supervisor Pattern — メモリ管理の監督者

**Supervisor Pattern** = メモリの読み書きを監督し、品質を保証する仕組み

| 役割 | 責務 | Claude Codeでの実装 |
|------|------|-------------------|
| **Supervisor** | メモリの品質・整合性を管理 | セッション開始時の自動検証 |
| **Writer** | 新しいメモリの作成・更新 | AIへの「これを覚えて」指示 |
| **Reader** | メモリの参照・活用 | 新セッションでの自動読込 |

**Supervisorのチェック項目**:
- メモリの内容がまだ正しいか (ファイルパスの存在確認等)
- 新旧メモリ間の矛盾がないか
- 200行制限を超えていないか

<!--
Supervisor Patternは、メモリ管理を監督する役割を定義するパターンです。Supervisorは品質と整合性を管理し、Writerは新しいメモリの作成を担当し、Readerはメモリの参照を担当します。Claude Codeでは、セッション開始時に自動的にメモリの検証が行われます。ファイルパスがまだ存在するか、新旧メモリに矛盾がないか、200行制限を超えていないかをチェックします。この自動検証がSupervisor Patternの実装に相当します。
-->

---

# 4カテゴリ分類 — 何をどう保存するか

永続コンテキストは **4つのカテゴリ** に分類して管理する

| カテゴリ | 内容 | 例 | 更新頻度 |
|---------|------|-----|---------|
| **user** | ユーザーの役割・好み・知識 | 「React経験3年・Python初心者」 | 低 |
| **feedback** | AIへの指摘・訂正・改善指示 | 「テストは実ファイルで確認せよ」 | 中 |
| **project** | プロジェクト固有の状況・判断 | 「認証方式はJWTに決定」 | 高 |
| **reference** | 外部システムへのポインタ | 「バグ管理はLinearプロジェクトX」 | 低 |

> **Supervisor Patternの観点**: カテゴリごとに更新頻度が違う → それぞれ異なるライフサイクル管理が必要

<!--
メモリを4つのカテゴリに分類します。userはユーザーの基本情報で更新頻度が低い。feedbackはAIへの指摘で中頻度。projectはプロジェクト固有の判断で高頻度。referenceは外部システムへのポインタで低頻度です。Supervisor Patternの観点では、カテゴリごとに更新頻度が違うため、それぞれ異なるライフサイクル管理が必要になります。projectカテゴリは頻繁に検証し、userカテゴリは時々確認すれば良いというように管理頻度を変えます。
-->

---

# MEMORY.md 索引 — Select戦略の「目次」

**MEMORY.md は「本棚の目次」** — 全文ではなく索引を置く

```
# Memory Index
- [Inbox送信ルール](feedback_inbox_spam.md) — 1回送って待て
- [Dashboard完了行削除](feedback_dashboard_cleanup.md) — 自動削除あり
```

### 200行制限の理由 (Select戦略の観点)

- MEMORY.mdは **セッション開始時に毎回自動Selectされる**
- 200行を超えると前章の **Goldilocks Zone** を逸脱する
- **詳細は個別ファイル** に書き、MEMORY.mdには **1行のリンク** だけ

> **アンチパターン**: MEMORY.mdに長文 → Select時のトークン消費増 → Context Rot

<!--
MEMORY.mdはSelect戦略における目次です。全文を書くのではなく、各メモリファイルへのリンクと1行の説明だけを書きます。200行制限がある理由は、MEMORY.mdがセッション開始時に毎回自動Selectされるからです。200行を超えると前章で学んだGoldilocks Zoneを逸脱し、Context Rotの原因になります。詳細は個別ファイルに書き、MEMORY.mdには1行のリンクだけを残すのがSelect戦略の基本です。
-->

---

# メモリのライフサイクル — Supervisor Patternで管理

```
作成 → 参照 → 検証 → 更新 → 削除
```

| フェーズ | 内容 | Supervisor Patternの役割 |
|---------|------|------------------------|
| **作成** | 新しい情報を `memory/*.md` に書く | カテゴリ分類の妥当性確認 |
| **参照** | 新セッションで自動Selectされる | 索引の正確性確認 |
| **検証** | 内容がまだ正しいか確認 | パス存在チェック・矛盾検出 |
| **更新** | 古い情報を新しい情報に書き換え | 追記でなく置換の徹底 |
| **削除** | 不要メモリの削除 | 索引からのリンク削除 |

> **重要**: メモリは「書いて終わり」ではない — Supervisor Patternによる定期的な検証が必要

<!--
メモリには5つのライフサイクルがあります。作成時はカテゴリ分類の妥当性を確認します。参照時は索引の正確性を確認します。検証時はパスの存在チェックや矛盾の検出を行います。更新時は追記ではなく置換を徹底します。削除時は索引からもリンクを削除します。Supervisor Patternは、このライフサイクル全体を監督し、品質を保証する役割を果たします。メモリは書いて終わりではなく、定期的な検証が必要です。
-->

---

# 肥大化防止 — Select戦略の品質基準

**メモリに書くべきでないもの**:

- **コードパターン・規約** → `CLAUDE.md` や `instructions/*.md` に書くべき
- **Git履歴・変更内容** → `git log` で確認できる
- **デバッグの解決策** → コードに反映済みなら不要
- **プロジェクト構造・ファイルパス** → 現在のファイルシステムから確認できる
- **CLAUDE.md に既にある情報** → 重複は矛盾の元

> **判断基準**: 「コードやGitから確認できるか？」→ はい → **書かない**
> 「人間の判断・教訓・好み」か？ → はい → **書く**

<!--
メモリの肥大化を防ぐには、何を書くべきでないかを知ることが重要です。コードパターンや規約はCLAUDE.mdに書くべきでメモリには書きません。Git履歴はgit logで確認できるので不要です。デバッグの解決策もコードに反映済みなら不要です。プロジェクト構造もファイルシステムから確認できます。判断基準はシンプルです。「コードやGitから確認できるか？」がYesなら書かない。「人間の判断、教訓、好みか？」がYesなら書く。これだけです。
-->

---

# この章のまとめ

- **LangChain Select戦略** = 蓄積された情報から必要なものだけを選択するコンテキスト管理手法
- **RAG** と同じ考え方 — 外部知識の検索・取得でAIの回答品質を向上
- **3つのバックエンド** (memory / MCP / claude-mem) を用途に応じて使い分ける
- **4カテゴリ** (user / feedback / project / reference) で更新頻度と寿命を管理
- **Supervisor Pattern** でメモリの品質と整合性を担保する
- **肥大化防止** — コードやGitから確認できることは書かない

<!--
この章のまとめです。LangChainのSelect戦略は、蓄積された情報から必要なものだけを選択するコンテキスト管理手法で、業界標準のRAGと同じ考え方です。3つのバックエンドを用途に応じて使い分け、4カテゴリで更新頻度を管理します。Supervisor Patternで品質と整合性を担保し、肥大化を防ぎます。次章ではCompress戦略を解説します。
-->

---

# 確認問題

**Q1**: LangChainのSelect戦略と業界標準で呼ばれる概念の組み合わせとして正しいものは？
- A: Select = MCP
- B: Select = RAG
- C: Select = auto-compact

**Q2**: メモリの4カテゴリのうち、更新頻度が最も高いのはどれか？
- A: user
- B: feedback
- C: project

**Q3**: Supervisor Patternの主な役割は何か？
- A: メモリに情報を書き込むこと
- B: メモリの品質・整合性を管理すること
- C: メモリを自動的に圧縮すること

<!--
確認問題です。Q1、Select戦略は業界標準のRAGと同じ考え方です。外部知識から関連情報を検索・取得してAIの回答品質を向上させます。Q2、4カテゴリのうち更新頻度が最も高いのはprojectです。プロジェクトの状況や決定事項は頻繁に変わります。Q3、Supervisor Patternの主な役割はメモリの品質と整合性を管理することです。検証、矛盾検出、ライフサイクル管理を担当します。
-->

---

<!-- _class: cover -->

# 第6章 完了!
## Select戦略でAIに「忘れない記憶」を与えられたか?

**到達点チェック**:
- ✅ LangChain Select戦略とRAGの関係を説明できる
- ✅ 3つのバックエンドの特徴を理解している
- ✅ 4カテゴリ分類とSupervisor Patternを説明できる
- ✅ メモリのライフサイクルを把握している
- ✅ 肥大化防止の判断基準を適用できる

**次章**: Compress戦略 — `/clear` しても完全復旧する仕組み

<div class="meta">
講師: なぎなた
</div>

<!--
第6章完了です。Select戦略でAIに忘れない記憶を与える仕組みを理解できましたか。到達点を振り返りましょう。LangChain Select戦略とRAGの関係、3つのバックエンド、4カテゴリとSupervisor Pattern、ライフサイクル管理、肥大化防止策の5つを理解できていれば完璧です。次章ではCompress戦略を解説します。セッションが途切れても完全に復旧する仕組みです。引き続き学んでいきましょう。
-->
