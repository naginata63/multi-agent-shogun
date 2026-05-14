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

# 第3章 .md仲間たち
## commands / skills / agents / imports — コンテキストを深める設定ファイル群

<div class="meta">
初級編 — 第3章 (約 30 min)<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
こんにちは。第3章「.md仲間たち」を始めます。前章では CLAUDE.md を学びました。プロジェクトルートに 30 行の説明書を置けば、新しい会話を始めるたびに AI が自動でルールを読んでくれる、L2 コンテキストエンジニアリングの土台です。今日はその CLAUDE.md の周りにある「.md 仲間たち」を見ていきます。具体的には、サブエージェントを定義する `.claude/agents/`、定型操作を保存する `.claude/commands/`、ワークフローをオンデマンドで読み込ませる `.claude/skills/`、そして CLAUDE.md 内から他のファイルを取り込む `@path` imports。これらは CLAUDE.md がプロジェクト全体の説明書なら、特定用途の補強パッケージという位置付けです。30 分かけて全体像と使い分け、そして初心者がどの順番で導入すべきかを確認しましょう。
-->

---

# 🗺️ 前章の復習 — CLAUDE.md と L2 の続き

**前章 (第2章) で身につけたこと**:
- CLAUDE.md = AI に読ませるプロジェクトの説明書 (3階層モデルの **L2 コンテキスト**)
- **4階層構造**（管理 / ユーザー / プロジェクト / ローカル）を「**連結**」して読込
- **5セクション30行** ミニマムで始める
- **新しい会話/セッション開始時に自動読み込み**（`/clear`・`/compact` 後も再読込）

**本章 (第3章) で広げること**: CLAUDE.md の周りにある **.md 仲間たち** = commands / skills / agents / imports。CLAUDE.md がプロジェクト全体の説明書なら、これらは **特定用途の補強パッケージ**

<!--
前章の復習からです。CLAUDE.md はプロジェクトルートに置いて自動読み込みされる説明書で、4階層構造で連結されて AI に渡される、ということを学びました。5セクション30行のミニマム構成から始めれば十分というのもポイントでした。本章はその CLAUDE.md の周りにある仲間たち、commands・skills・agents・imports を見ていきます。これらは全部書く必要はなく、必要に応じて段階的に導入するものですが、それぞれの役割を「名前と1行」で説明できるようになるのが本章のゴールです。
-->

---

## この章で出てくる用語

> 📝 まず名前だけ覚えておきましょう。後ほど詳しく解説します

> **結論**: **必須は CLAUDE.md だけ**。残り 5 つは Step 2・Step 3 で段階的に導入する拡張機能です

| 用語 | 一言でいうと |
|------|------------|
| **.claude/agents/** | AIに特定の役割を与える設定ファイル（サブエージェント定義） |
| **commands** | よく使う指示をテンプレート化したもの（`/<名前>` で起動） |
| **skills** | ワークフロー定義。**必要時にオンデマンドで読み込まれる**（例：テスト→ビルド→デプロイを一発で） |
| **imports** | CLAUDE.md 内の `@path` 構文で他ファイルを取り込む機能 |
| **global CLAUDE.md** | 前章の 4 階層のうち **ユーザー層** (`~/.claude/CLAUDE.md`) |

<!--
このスライドは用語の予告編です。「.claude/agents/ ってなんだろう」「commands と skills の違いは?」と思いながら、まず名前だけ頭に入れてください。後のスライドで 1 つずつ詳しく解説します。global CLAUDE.md は前章で扱った 4 階層構造のうち、ユーザー層に当たるファイルだということだけ押さえておいてください。
-->

---

## この 30 分で得られること

1. **6つの設定機構** を名前と役割で挙げられる
2. **CLAUDE.md / .claude/agents/ / commands / skills / imports / global** の使い分けを説明できる
3. **初心者がどの順番で導入すべきか** 判断できる
4. 各機構が **「なくても動くが、あると劇的に変わる」** 理由を理解する

<!--
この章のゴールは4つです。CLAUDE.mdだけだと思っていた設定が、実は6つ以上のファイル群で支えられていることに気づくのが第一歩。そして「全部書かないといけないの？」という不安を「いいえ、必要なものだけ」という安心感に変えていただきます。
-->

---

# .mdファイル群の全体像

> 🪞 「CLAUDE.md以外にも、AIが読む説明書がある？」
>
> **結論**: 必須は CLAUDE.md だけ。残り5つは Step 2 以降で段階的に導入する拡張機能です

| 機構 | 役割 | 例 |
|------|------|-----|
| **CLAUDE.md** | プロジェクト固有ルール | コーディング規約・使用技術 |
| **.claude/agents/** | 役割別の行動指針（サブエージェント定義） | 専門分野ごとの切り替え |
| **commands/** | スラッシュコマンドのテンプレート | 定型操作の保存 |
| **skills/** | 再利用ワークフロー（オンデマンド読込） | 複数ステップの自動化 |
| **imports** | CLAUDE.md 内の `@path` 構文 | 共通設定のプロジェクト間共有 |
| **global CLAUDE.md** | 前章 4 階層の **ユーザー層** | ユーザー全体の好み・ルール |

> この6つが連携して、AIに「文脈」を与える

<!--
CLAUDE.mdは「メインの説明書」でした。でもAIには、もっとたくさんの「説明書」があります。この表の6つが、Claude Codeの.md設定ファイル群の全体像です。以降のスライドで1つずつ解説します。まずは「6つある」という全体像を頭に入れてください。global CLAUDE.md は前章で扱った 4 階層構造のユーザー層に当たるので、新しいファイルというより「前章の振り返り」の位置付けです。
-->

---

# CLAUDE.md — すべての基盤（前章復習）

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

- プロジェクトルートに配置 → **新しい会話/セッションの開始時に自動読み込み**
- 4 階層 (管理 / ユーザー / プロジェクト / ローカル) を **「連結」して読込**
- 「このプロジェクトではどうするか」を **永続化** する

> CLAUDE.mdは土台。残り5機構はこの土台を拡張する仲間たち

<!--
CLAUDE.mdは前章で詳しく学びました。プロジェクトルートに置くだけで、新しい会話やセッションを開始するたびに自動で読み込まれる、プロジェクト固有のルールファイルです。4 階層構造で連結読み込みされるという挙動も思い出してください。6機構のうち最も重要で、すべての基盤になります。残り5つは、このCLAUDE.mdを拡張する仲間たちです。
-->

---

# agents/ — エージェントの行動指針

**1つのプロジェクトで、AIの「役割」を切り替える仕組み**:

イメージ: 1つの会社に「営業部」「開発部」「品質管理部」があるように、同じAIに役割別のマニュアルを用意します。

```
「フロントエンド専門エージェントを使って、このボタンの色を変えて」
  → Claude が .claude/agents/frontend.md の指針に従って回答

「コードレビュアー エージェントでこの PR を見て」
  → Claude が .claude/agents/reviewer.md の指針に従って回答
```

配置場所: `.claude/agents/<name>.md` (プロジェクト) / `~/.claude/agents/<name>.md` (ユーザー) — **ディレクトリ内に 1ファイル=1エージェント** (YAML フロントマター付き Markdown)

> 1つのCLAUDE.md + 複数の `.claude/agents/*.md` = 役割分担

<!--
agents/ は、1つのプロジェクトの中でAIの役割を切り替える仕組みです。1ファイル1エージェントで `.claude/agents/<名前>.md` に配置し、YAML フロントマターで description などを記述します。フロントエンド専門のAI、バックエンド専門のAI、コードレビュー専門のAI。それぞれに異なる行動指針を与えることで、1つのプロジェクトで複数の役割を持たせられます。次のスライドで呼び出し方を整理します。
-->

---

# agents/ の呼び出し方 — 5 方式と注意点

**呼び出しの 5 方式（Claude Code 公式）**:

| # | 方式 | 例 |
|---|------|-----|
| 1 | **description ベースの自動委譲** | Claude が状況判断して自動委譲 |
| 2 | **自然言語でサブエージェント名を指定** | 「フロントエンドエージェントを使って」 |
| 3 | **@-mention** | `@"frontend (agent)"` |
| 4 | **CLI フラグ** | `claude --agent frontend "..."` |
| 5 | **Agent (旧 Task) ツール経由** | コード/別エージェントから呼び出し |

**注意 (混同しやすい点)**:
- `/agents` コマンドはエージェントの **管理** (作成・編集・削除) 用で、**呼び出しには使いません**
- `/agent <name>` のような **個別呼び出しコマンドは存在しません**
- 初級では **①description ベースの自動委譲** と **②自然言語での名指し** を覚えれば十分

<!--
呼び出し方は公式で 5 通りあります。description ベースの自動委譲、自然言語でのサブエージェント名指定、@-mention、CLI フラグ --agent、そして Agent ツール経由。初級編では「○○エージェントを使って」と自然言語で頼む、または description マッチで Claude に自動委譲してもらう、この 2 つを覚えれば十分です。@-mention や --agent や Agent ツール経由は中級編で扱います。注意点として、`/agents` というスラッシュコマンドはエージェントの管理（作成・編集・削除）用であって呼び出し用ではありません。`/agent <name>` のような個別呼び出しコマンドは存在しないので、これも混同しないようにしてください。
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
commandsは、よく使う指示をテンプレート化する仕組みです。「このファイルをレビューして」を毎回手入力する代わりに、/reviewと打つだけで実行できるようになります。チーム開発では特に強力で、定型操作をファイルとして共有できるからです。「毎回同じプロンプトをコピペしている」なら、commandsにするタイミングです。次のスライドでもう少し細かく中身を見てみましょう。
-->

---

# commands の具体例

**`.claude/commands/review.md` の中身**:

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

# skills の具体例 — `.claude/skills/deploy/SKILL.md`

**複数ステップの作業を1コマンドにまとめる仕組み**:

```markdown
1. テストを実行する
2. テストが成功したらビルドする
3. ビルドが成功したらデプロイする
4. 失敗したらエラー内容を報告する
```

使い方: `/deploy` と入力するだけ（Claude が **必要時にオンデマンドで読み込む**）

- commandsの review.md は **毎回同じ指示** を出す（条件分岐なし）
- skillsの deploy.md は **結果を見て次の行動を変える**（成功→次へ、失敗→報告）
- この「**条件によって動きを変える**」のが最大の違い

<!--
これは skills の具体例です。実際のファイルは `.claude/skills/deploy/SKILL.md` という形で、deploy という名前のディレクトリの中に SKILL.md というエントリポイントファイルを置きます。中身は複数ステップのワークフローで、結果を見て次の行動を変える条件分岐が含められます。commands の review.md が毎回同じ指示を出すのに対し、skills の deploy.md は「成功したら次へ・失敗したら報告」のように結果に応じて分岐する点が最大の違いです。
-->

---

# skills — 再利用可能なワークフロー

commands と skills の違いを整理しましょう:

| 特徴 | commands | skills |
|------|----------|--------|
| 指示の出し方 | 毎回 **同じ内容を固定** で出す | 結果を見て **次の行動を変える** |
| 条件による分岐 | できない | できる（成功→次、失敗→報告など） |
| 自動化の範囲 | 単発操作 | **ワークフロー全体** |
| 配置形式 | `.claude/commands/<name>.md` (単一ファイル) | **`.claude/skills/<name>/SKILL.md`**（**ディレクトリ + SKILL.md エントリポイント**） |
| 読込挙動 | スラッシュ実行時にロード | **description のみ常駐・本体はオンデマンド読込** |
| 自律発動 | しない | **description のキーワードマッチで Claude が自動起動** |

> commands = 定型文 / skills = 定型ワークフロー（オンデマンド読込）

<!--
skillsはcommandsの進化版です。commandsが「1回の指示」なら、skillsは「複数ステップからなるワークフロー」を定義できます。配置形式が大事で、commands は単一の .md ファイル、skills はディレクトリの中に SKILL.md というエントリポイントを置く形式です。Claude Code 公式ドキュメントでも、各スキルは SKILL.md をエントリポイントとするディレクトリ、と明記されています。skills のもう 1 つの特徴は、description のキーワードマッチで Claude が自動起動してくれることです。例えば「漫画ショート作って」と書けば、`.claude/skills/manga-short/SKILL.md` の description にマッチして自動で発動します。本体は使う瞬間にだけ読み込まれる「オンデマンド読込」なので、書いたスキルが何個あっても起動時のコンテキストを圧迫しません。初級編では「commandsより高度な自動化ができる、ディレクトリ形式で配置する」という理解で十分です。
-->

---

# imports — CLAUDE.md 内の `@path` 構文

**共通設定をプロジェクト間で共有する仕組み**:

CLAUDE.md の中に `@path`（`@` は「このファイルを読み込んで」という意味の記号）と書くと、そのファイルの中身が **CLAUDE.md と一緒に起動時にコンテキストに読み込まれます**:

```markdown
# CLAUDE.md の中身
@shared/coding_rules.md
@shared/test_rules.md
```

**仕様 (Claude Code 公式)**:
- **相対パスはインポート元ファイル基準**・絶対パスも可
- **再帰的インポート可・最大 5 ホップ**まで辿る
- imports は **CLAUDE.md 内部の構文機能** であり、独立した .md ファイル種別ではない

> 「5プロジェクトで同じルールをコピペしている」なら imports で統合

<!--
importsは、CLAUDE.mdの中から外部ファイルを取り込む仕組みです。CLAUDE.mdに @パス と書くだけで、そのファイルの中身が展開されて、CLAUDE.md と一緒にコンテキストに読み込まれます。相対パスはインポート元ファイル基準で、絶対パスも使えます。再帰的なインポートも可能で、@で読み込まれたファイルが更に @ で別ファイルを呼ぶ、というのを最大 5 ホップまで辿ってくれます。注意点として、imports は CLAUDE.md 内部の構文機能であって、commands や skills のような独立した「.md ファイル種別」ではありません。例えば5つのプロジェクトで共通のコーディング規約がある場合、1箇所に置いてimportsで読み込めば、各プロジェクトのCLAUDE.mdに同じ内容をコピペする必要がありません。ルールの変更も1ファイル直すだけで全プロジェクトに反映されます。
-->

---

# global CLAUDE.md — 全プロジェクト共通設定

**あなたのPC全体で共有する「AIの好み」**:

配置場所: `~/.claude/CLAUDE.md` ＝ 前章 第2章で扱った **4 階層構造のうちユーザー層**

```
# 全プロジェクト共通の好み
- 回答は日本語で
- コメントは最小限に
- テストは必ず書く
```

- すべてのプロジェクトで **自動的に読み込まれる**
- プロジェクトの CLAUDE.md と **「上書き」ではなく「連結」** されて AI に渡される
- 矛盾する記述がある場合、**プロジェクト指示が後に読まれるため、Claude はそちらに従う傾向**（「**後勝ち**」)
- 「このPCのユーザーの好み」を **一元管理**

> global = 全体の好み / プロジェクト CLAUDE.md = 固有のルール（**両者は連結**）

<!--
global CLAUDE.mdは、あなたのPC全体に適用される設定です。前章で 4 階層構造を学んだとき、ユーザー層として紹介したのがまさにこのファイルです。ホームディレクトリの下の.claudeフォルダに置きます。例えば「回答は日本語で」「コメントは最小限に」といった、すべてのプロジェクトに共通する好みを書いておくと、どのプロジェクトを開いてもAIがその好みを反映します。ここで重要なのは、global とプロジェクト CLAUDE.md の関係です。「プロジェクトがglobalを上書きする」のではなく、両者は連結されて AI に渡されます。ただし矛盾する記述があった場合、プロジェクト指示が後に読まれるため、Claude はそちらに従う傾向があります。これを「後勝ち」と呼びます。上書きではなく、後に読まれた方が優先される、という挙動です。
-->

---

# 6機構の関係性 — レイヤー構造

| レイヤー | 対象 | 機構 |
|---------|------|------|
| **Global** | 全プロジェクト | global CLAUDE.md（前章 4 階層のユーザー層） |
| **Project** | プロジェクト全体 | CLAUDE.md |
| **Role** | 役割・共通設定 | .claude/agents/, imports |
| **Operation** | 定型操作 | commands, skills |

- 上位レイヤー → **広い範囲に適用**
- 下位レイヤー → **具体的な操作の自動化**
- すべての層は「**連結**」されて AI に渡され、矛盾時は **後に読まれたもの (＝より具体的なもの) が従われやすい**

<!--
6機構をレイヤー構造で整理するとこのようになります。一番上が全プロジェクトに適用されるglobal CLAUDE.md、これは前章の4階層構造のユーザー層に当たります。その下がプロジェクト固有のCLAUDE.md。さらに下に役割や共通設定、そして一番下が具体的な操作の自動化。上位ほど広い範囲、下位ほど具体的。すべての層は連結されて AI に渡されて、矛盾があった場合は後に読まれた方、つまりより具体的な指示が従われやすい、という構造です。この階層構造を理解しておくと、どこに何を書くべきか迷わなくなります。
-->

---

# 初心者はどの順番で導入すべきか

**3段階の拡張パス**:

| 段階 | 導入する機構 | タイミング |
|------|------------|-----------|
| **Step 1** | CLAUDE.md | 最初から（必須） |
| **Step 2** | commands | 同じ指示を3回以上書いたら |
| **Step 3** | skills, imports, .claude/agents/ | チーム開発や複雑化したら |

> global CLAUDE.md はPC設定時に1回書くだけ

<!--
「全部書かないといけないの？」と不安になる必要はありません。最初はCLAUDE.mdだけ。それで十分です。同じ指示を3回以上書いたらcommandsに。チーム開発が始まったり、プロジェクトが複雑になったら残りの機構を導入する。この順番で無理なく拡張してください。
-->

---

# まとめ — .md仲間たちの全体像

| 機構 | 一言で言うと | 導入タイミング |
|------|------------|---------------|
| CLAUDE.md | プロジェクトの説明書 | **Step 1: 最初から（必須）** |
| commands | 定型指示のテンプレート（`.claude/commands/<name>.md`） | **Step 2: 同じ指示を3回書いたら（推奨）** |
| global CLAUDE.md | 全体の好み設定（`~/.claude/CLAUDE.md`） | **Step 2: PC設定時に1回（推奨）** |
| .claude/agents/ | AIの役割別マニュアル（サブエージェント） | Step 3: 役割を分けたくなったら（任意） |
| skills | ワークフローのオンデマンド読込（`.claude/skills/<name>/SKILL.md`） | Step 3: 作業を自動化したくなったら（任意） |
| imports | CLAUDE.md 内の `@path` 構文 | Step 3: 複数プロジェクトで同じルールを使うなら（任意） |

**ポイント**: まず CLAUDE.md だけ書けばOK。必要になってから Step 2、Step 3 と増やしていけばよい

<!--
6機構をまとめました。CLAUDE.mdだけが必須。残り5つは「あったら便利」な拡張機能です。配置場所を正確に覚えておくのも大事です。commands は単一ファイル `.claude/commands/<name>.md`、skills はディレクトリ形式 `.claude/skills/<name>/SKILL.md`、agents は `.claude/agents/<name>.md`、imports は CLAUDE.md 内の @path 構文です。最初はCLAUDE.mdだけ書いて、必要に応じてcommandsやglobal CLAUDE.mdを追加していく。この順番で無理なく拡張していきましょう。
-->

---

# 確認問題

**Q1**: AIにプロジェクト固有のルールを教えるファイルは何か？

<details><summary>回答</summary>CLAUDE.md（プロジェクトルートに配置・新しい会話/セッション開始時に自動読込）</details>

**Q2**: 「同じレビュー指示を毎回手入力している」→ どの機構を使うべきか？

<details><summary>回答</summary>commands（`.claude/commands/review.md` のように単一ファイルでテンプレートを配置・`/review` で起動）</details>

**Q3**: 5つのプロジェクトで共通のコーディング規約を1箇所で管理するには？

<details><summary>回答</summary>imports または global CLAUDE.md。どちらも「1箇所に書いて使い回す」仕組みです。使い分けの基準: **imports** はプロジェクトのルール（CLAUDE.md 内で `@path` 構文・チーム共有向け）、**global CLAUDE.md** はあなた個人の好み（`~/.claude/CLAUDE.md`・1人で使う設定）</details>

<!--
3問の確認問題です。Q1はCLAUDE.md。プロジェクトルートに置くだけで新しいセッション開始時に自動読み込みされます。Q2はcommands。同じ指示を3回以上書いたらテンプレート化するサインで、`.claude/commands/<名前>.md` の単一ファイル形式で配置します。Q3はimportsかglobal CLAUDE.md。どちらも「1箇所に書いて使い回す」仕組みですが、importsはプロジェクトのルール共有、globalはユーザー個人の好みという違いがあります。
-->

---

<!-- _class: cover -->

# 第3章 完了

## 次は 第4章「歴史と意義 — なぜ3階層なのか」

<div class="meta">
✅ 6つの.md設定機構の全体像を理解<br>
✅ CLAUDE.md / .claude/agents/ / commands / skills / imports / global の使い分け<br>
✅ サブエージェント呼び出しの 5 方式（自動委譲・自然言語・@-mention・CLI フラグ・Agent ツール）<br>
✅ skills は <code>.claude/skills/&lt;name&gt;/SKILL.md</code> ディレクトリ形式 (オンデマンド読込)<br>
✅ imports は CLAUDE.md 内の <code>@path</code> 構文（最大 5 ホップ）<br>
✅ global とプロジェクト CLAUDE.md は「上書き」ではなく「連結」（後勝ち）<br>
✅ 初心者の導入順序（CLAUDE.md → commands → skills/agents/imports）を把握<br><br>
<b>続けて 第4章 をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章では、CLAUDE.md以外の5つの.md仲間たちを学びました。.claude/agents/、commands、skills、imports、global CLAUDE.md。全部覚える必要はありません。「CLAUDE.md以外にも5つの拡張がある」ということと、「必要になったら段階的に導入する」という2点を押さえておいてください。配置場所のポイント — commands は単一 .md ファイル、skills は SKILL.md エントリポイントを持つディレクトリ、agents は .claude/agents/<name>.md、imports は CLAUDE.md 内の @path 構文 — も今後の章で繰り返し出てくるので、ここで一度整理できたのは大きな収穫です。次の第4章では、なぜ3階層（プロンプト・コンテキスト・ハーネス）という構造が必要なのか、歴史的な背景から解説します。
-->
