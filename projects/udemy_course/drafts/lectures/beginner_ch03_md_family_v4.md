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

# .md仲間たち
## コンテキストを深める設定ファイル群

<div class="meta">
初級編 — 第3章 [L2: 深化] (約 30 min)<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
こんにちは。このレクチャーでは「.md仲間たち」を解説します。前章でCLAUDE.mdを学びましたが、実はClaude CodeにはCLAUDE.md以外にも設定ファイルが複数あります。エージェントの行動指針、ワンクリックコマンド、再利用可能なスキル、外部設定の取り込み、グローバル設定。これら6つの.md仲間たちを理解することで、AIを本格的な開発パートナーに変えることができます。30分でしっかり学びましょう。
-->

---

## この章で出てくる用語

> 📝 まず名前だけ覚えておきましょう。後ほど詳しく解説します

> **結論**: **必須は CLAUDE.md だけ**。残り5つは「あったら便利」な拡張機能です

| 用語 | 一言でいうと |
|------|------------|
| **agents.md** | AIの役割別マニュアル（人格を切り替える設定ファイル） |
| **commands** | よく使う指示をテンプレート化したもの（`/review` で起動） |
| **skills** | 複数ステップの作業を自動化する仕組み |
| **imports** | 外部ファイルをCLAUDE.mdに取り込む機能 |
| **global CLAUDE.md** | あなたのPC全体で共通のAI設定 |

---

## この 30 分で得られること

1. **6つの設定機構** を名前と役割で挙げられる
2. **CLAUDE.md / agents.md / commands / skills / imports / global** の使い分けを説明できる
3. **初心者がどの順番で導入すべきか** 判断できる
4. 各機構が **「なくても動くが、あると劇的に変わる」** 理由を理解する

<!--
この章のゴールは4つです。CLAUDE.mdだけだと思っていた設定が、実は6つ以上のファイル群で支えられていることに気づくのが第一歩。そして「全部書かないといけないの？」という不安を「いいえ、必要なものだけ」という安心感に変えていただきます。
-->

---

# .mdファイル群の全体像

> 🪞 「CLAUDE.md以外にも、AIが読む説明書がある？」
>
> **結論**: 必須は CLAUDE.md だけ。残り5つは「あったら便利」です

| 機構 | 役割 | 例 |
|------|------|-----|
| **CLAUDE.md** | プロジェクト固有ルール | コーディング規約・使用技術 |
| **agents.md** | エージェント別の行動指針 | 役割ごとの人格切り替え |
| **commands/** | ワンクリックコマンド | 定型操作のテンプレート |
| **skills/** | 再利用ワークフロー | 複数ステップの自動化 |
| **imports** | 外部ファイルの取り込み | 共通設定のプロジェクト間共有 |
| **global CLAUDE.md** | 全プロジェクト共通設定 | ユーザー全体の好み・ルール |

> この6つが連携して、AIに「文脈」を与える

<!--
CLAUDE.mdは「メインの説明書」でした。でもAIには、もっとたくさんの「説明書」があります。この表の6つが、Claude Codeの.md設定ファイル群の全体像です。以降のスライドで1つずつ解説します。まずは「6つある」という全体像を頭に入れてください。
-->

---

# CLAUDE.md — すべての基盤（復習）

前章で学んだ **プロジェクト固有のルールファイル**:

```
# プロジェクトの技術スタック
- 言語: TypeScript
- フレームワーク: Next.js
- テスト: Jest

# コーディング規約
- インデント: 2スペース
- 命名: camelCase
```

- プロジェクトルートに配置 → AIが **自動読み込み**
- 「このプロジェクトではどうするか」を **永続化** する

> CLAUDE.mdは土台。残り5機構はこの土台を拡張する

<!--
CLAUDE.mdは前章で詳しく学びました。プロジェクトルートに置くだけでAIが自動的に読み込む、プロジェクト固有のルールファイル。6機構のうち最も重要で、すべての基盤になります。残り5つは、このCLAUDE.mdを拡張する仲間たちです。
-->

---

# agents.md — エージェントの行動指針

**1つのプロジェクトで、AIの「役割」を切り替える仕組み**:

同じチャット画面で、呼び出し方によってAIの動きが変わります:

```
/agent frontend    → 「フロントエンド専門」として回答
/agent backend     → 「バックエンド専門」として回答
/agent reviewer    → 「レビュー専門」として回答
```

配置場所: `.claude/agents.md`（前章で出てきた `.claude/` フォルダの中 — 第2章参照）

> 1つのCLAUDE.md + 複数のagents.md = 役割分担

<!--
agents.mdは、1つのプロジェクトの中でAIの役割を切り替える仕組みです。同じチャット画面でスラッシュコマンドのように切り替えます。フロントエンド専門のAI、バックエンド専門のAI、コードレビュー専門のAI。それぞれに異なる行動指針を与えることで、1つのプロジェクトで複数の役割を持たせられます。ただし初級編では「そういう仕組みがある」という理解で十分です。
-->

---

# commands — ワンクリックコマンド

**よく使う操作を「定型文」として保存する仕組み**:

```
.claude/commands/
  ├── review.md      → /review で起動
  ├── test.md        → /test で起動
  └── deploy.md      → /deploy で起動
```

メリット:
- **何度も同じ指示を書かなくていい**
- チーム内で **指示を共有** できる
- スラッシュ (`/`) で **1クリック実行**

> 「毎回同じプロンプトをコピペしている」なら commands にすべきサイン

<!--
commandsは、よく使う指示をテンプレート化する仕組みです。「このファイルをレビューして」を毎回手入力する代わりに、/reviewと打つだけで実行できるようになります。チーム開発では特に強力で、定型操作をファイルとして共有できるからです。「毎回同じプロンプトをコピペしている」なら、commandsにするタイミングです。
-->

---

# commands の具体例

**review.md の中身**:

```markdown
以下のファイルのコードレビューをお願いします。
- セキュリティ上の問題がないか確認
- パフォーマンスの改善点があれば指摘
- 可読性についてコメント
```

使い方: `/review` と入力するだけ

- チーム全員が **同じ基準でレビュー** を依頼できる
- プロンプトの品質が **ブレない**
- 新しいメンバーも **即座に同じ品質** の指示を出せる

<!--
実際のcommandsファイルの中身を見てみましょう。例えばreview.mdなら、このようにレビューの基準を書いておきます。使う時はスラッシュreviewと入力するだけ。チーム全員が同じ基準でレビューを依頼できるので、プロンプトの品質がブレません。
-->

---

# skills — 再利用可能なワークフロー

**複数ステップの作業を1コマンドにまとめる仕組み**:

| 特徴 | commands との違い |
|------|-----------------|
| **複数ステップ** を定義可能 | commandsは1回の指示 |
| **条件分岐** を含める | commandsは固定内容 |
| **ワークフロー全体** を自動化 | commandsは単発操作 |

配置場所: `.claude/skills/`

> commands = 定型文 / skills = 定型ワークフロー

---

# skills の具体例

**deploy.md の中身イメージ**:

```markdown
1. テストを実行する
2. テストが成功したらビルドする
3. ビルドが成功したらデプロイする
4. 失敗したらエラー内容を報告する
```

使い方: `/deploy` と入力するだけ

- commandsの review.md は「レビューして」の **1回きり**
- skillsの deploy.md は「テスト→ビルド→デプロイ」の **流れを丸ごと自動化**
- 失敗時の対応まで **自動で判断** するのが違い

<!--
skillsはcommandsの進化版です。commandsが「1回の指示」なら、skillsは「複数ステップからなるワークフロー」を定義できます。条件分岐も含められるので、「まずテストを実行し、成功したらデプロイ、失敗したらエラー報告」といった自動化が可能です。初級編では「commandsより高度な自動化ができる」という理解で十分です。
-->

---

# imports — 外部ファイルの取り込み

**共通設定をプロジェクト間で共有する仕組み**:

CLAUDE.md の中に `@path` と書くと、そのファイルの中身が自動的に読み込まれます:

```markdown
# CLAUDE.md の中身
@shared/coding_rules.md
@shared/test_rules.md
```

メリット:
- **共通ルールを1箇所で管理**
- 複数プロジェクトで **同じルールを使い回し**
- ルール変更は **1ファイルの修正で全プロジェクトに反映**

> 「5プロジェクトで同じルールをコピペしている」なら imports で統合

<!--
importsは、CLAUDE.mdの中から外部ファイルを取り込む仕組みです。CLAUDE.mdに @パス と書くだけで、そのファイルの中身が展開されます。例えば5つのプロジェクトで共通のコーディング規約がある場合、1箇所に置いてimportsで読み込めば、各プロジェクトのCLAUDE.mdに同じ内容をコピペする必要がありません。ルールの変更も1ファイル直すだけで全プロジェクトに反映されます。
-->

---

# global CLAUDE.md — 全プロジェクト共通設定

**あなたのPC全体で共有する「AIの好み」**:

配置場所: `~/.claude/CLAUDE.md`

```
# 全プロジェクト共通の好み
- 回答は日本語で
- コメントは最小限に
- テストは必ず書く
```

- すべてのプロジェクトで **自動的に読み込まれる**
- プロジェクトのCLAUDE.mdが **上書き（優先）** される構造
- 「このPCのユーザーの好み」を **一元管理**

> global = 全体の好み / CLAUDE.md = プロジェクト固有のルール

<!--
global CLAUDE.mdは、あなたのPC全体に適用される設定です。ホームディレクトリの下の.claudeフォルダに置きます。例えば「回答は日本語で」「コメントは最小限に」といった、すべてのプロジェクトに共通する好みを書いておくと、どのプロジェクトを開いてもAIがその好みを反映します。プロジェクト固有のCLAUDE.mdが優先されるので、上書きも可能です。
-->

---

# 6機構の関係性 — レイヤー構造

| レイヤー | 対象 | 機構 |
|---------|------|------|
| **Global** | 全プロジェクト | global CLAUDE.md |
| **Project** | プロジェクト全体 | CLAUDE.md |
| **Role** | 役割ごとの設定 | agents.md, imports |
| **Operation** | 定型操作 | commands, skills |

- 上位レイヤー → **広い範囲に適用**
- 下位レイヤー → **具体的な操作の自動化**
- プロジェクト固有ルールが **global を上書き**

<!--
6機構をレイヤー構造で整理するとこのようになります。一番上が全プロジェクトに適用されるglobal CLAUDE.md。その下がプロジェクト固有のCLAUDE.md。さらに下にチームや役割の設定、そして一番下が具体的な操作の自動化。上位ほど広い範囲、下位ほど具体的。この階層構造を理解しておくと、どこに何を書くべきか迷わなくなります。
-->

---

# 初心者はどの順番で導入すべきか

**3段階の拡張パス**:

| 段階 | 導入する機構 | タイミング |
|------|------------|-----------|
| **Step 1** | CLAUDE.md | 最初から（必須） |
| **Step 2** | commands | 同じ指示を3回以上書いたら |
| **Step 3** | skills, imports, agents.md | チーム開発や複雑化したら |

> global CLAUDE.md はPC設定時に1回書くだけ

<!--
「全部書かないといけないの？」と不安になる必要はありません。最初はCLAUDE.mdだけ。それで十分です。同じ指示を3回以上書いたらcommandsに。チーム開発が始まったり、プロジェクトが複雑になったら残りの機構を導入する。この順番で無理なく拡張してください。
-->

---

# まとめ — .md仲間たちの全体像

| 機構 | 一言で言うと | 導入タイミング |
|------|------------|---------------|
| CLAUDE.md | プロジェクトの説明書 | **Step 1: 最初から（必須）** |
| commands | 定型指示のテンプレート | **Step 2: 同じ指示を3回書いたら（推奨）** |
| global CLAUDE.md | 全体の好み設定 | **Step 2: PC設定時に1回（推奨）** |
| agents.md | AIの役割別マニュアル | Step 3: 役割を分けたくなったら（任意） |
| skills | 複数ステップの自動化 | Step 3: 作業を自動化したくなったら（任意） |
| imports | 共通設定の共有 | Step 3: 複数プロジェクトで同じルールを使うなら（任意） |

**ポイント**: まず CLAUDE.md だけ書けばOK。必要になってから Step 2、Step 3 と増やしていけばよい

<!--
6機構をまとめました。CLAUDE.mdだけが必須。残り5つは「あったら便利」な拡張機能です。最初はCLAUDE.mdだけ書いて、必要に応じてcommandsやglobal CLAUDE.mdを追加していく。この順番で無理なく拡張していきましょう。
-->

---

# 確認問題

**Q1**: AIにプロジェクト固有のルールを教えるファイルは何か？

<details><summary>回答</summary>CLAUDE.md（プロジェクトルートに配置）</details>

**Q2**: 「同じレビュー指示を毎回手入力している」→ どの機構を使うべきか？

<details><summary>回答</summary>commands（`.claude/commands/` にテンプレートを配置）</details>

**Q3**: 5つのプロジェクトで共通のコーディング規約を1箇所で管理するには？

<details><summary>回答</summary>imports（プロジェクト固有のルールを共有する場合）または global CLAUDE.md（あなたの好みを全プロジェクトに適用する場合）。どちらも「1箇所に書いて使い回す」仕組みですが、**imports はプロジェクトのルール**、**global はあなた個人の好み**という違いがあります</details>

<!--
3問の確認問題です。Q1はCLAUDE.md。プロジェクトルートに置くだけでAIが自動読み込みします。Q2はcommands。同じ指示を3回以上書いたらテンプレート化するサインです。Q3はimportsかglobal CLAUDE.md。どちらも「1箇所に書いて使い回す」仕組みですが、importsはプロジェクトのルール共有、globalはユーザー個人の好みという違いがあります。
-->

---

<!-- _class: cover -->

# 第3章 完了

## 次は 第4章「歴史と意義 — なぜ3階層なのか」

<div class="meta">
✅ 6つの.md設定機構の全体像を理解<br>
✅ CLAUDE.md / agents.md / commands / skills / imports / global の使い分け<br>
✅ 初心者の導入順序（CLAUDE.md → commands → skills）を把握<br>
✅ 各機構が「なくても動くが、あると変わる」ことを理解<br><br>
<b>続けて 第4章 をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章では、CLAUDE.md以外の5つの.md仲間たちを学びました。agents.md、commands、skills、imports、global CLAUDE.md。全部覚える必要はありません。「CLAUDE.md以外にも5つの拡張がある」ということと、「必要になったら段階的に導入する」という2点を押さえておいてください。次の第4章では、なぜ3階層（プロンプト・コンテキスト・ハーネス）という構造が必要なのか、歴史的な背景から解説します。
-->
