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

# 「コピペ地獄」を抜ける — .md 仲間 4 つの使い分け早見表
## CLAUDE.md だけでは届かない領域を埋める — agents / commands / skills / imports と 2026 年 1 月の公式マージ

<div class="meta">
第3章 (約 30 min)<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
</div>

<!--
スピーカーノート:
こんにちは。第3章「.md 仲間たち」を始めます。質問させてください — 前章で書いた CLAUDE.md だけで、本当に AI を使いこなせていますか? 同じプロジェクトで AI に「フロントエンド専門家」と「コードレビュアー」を切り替えて動かしたいとき、毎回 1000 字のレビュー指示文をコピペしている定型操作をスラッシュ一発で起動したいとき、「テスト→ビルド→失敗時に止まる」のような条件分岐を含む自動化をしたいとき — CLAUDE.md だけでは届きません。さらに Claude Code は 2026 年 1 月に「カスタムコマンドはスキルにマージされました」という重要な仕様変更を公式アナウンスしました。本章はこのマージの実像も含め、CLAUDE.md の周りにある 4 つの仲間 — agents / commands / skills / imports — を 30 分で押さえます。本章の最大のポイントは、これら設定ファイルを **皆さんが手書きで書く必要はない** ということ。実装は Claude に任せ、皆さんは「こう作って」と頼むプロンプト例を覚えてください。
-->

---

# 🗺️ 前章の復習 → 本章で広げる範囲 + ゴール

**前章 (第 2 章) で身に付けたこと**:
- CLAUDE.md = AI に読ませるプロジェクトの説明書 (3 階層モデルの **L2 コンテキスト**)
- **4 階層構造** (管理 / ユーザー / プロジェクト / ローカル) を **「連結」して読込**
- **5 セクション 30 行** ミニマムで始める
- **新しい会話/セッション開始時に自動読込** (`/clear`・`/compact` 後も再読込)

**本章 (第 3 章) で広げること**: CLAUDE.md の周りにある **.md 仲間 4 つ** = **agents / commands / skills / imports**

> 📌 **本章で押さえる 4 つの名前**: agents / commands / skills / imports。このうち **commands と skills は同じ機能の旧形式 / 新形式** (2026 年 1 月公式マージ・後ほど詳解) なので、機能としては **3 つ** ですが、書き方が別なので **本章では 4 つの名前を別個に覚える**

**🎯 30 分のゴール**: ① 4 つの仲間の役割を 1 行で説明できる ② **commands と skills が「同じ機能の 2 つの書き方」(2026 年 1 月公式マージ)** であることを理解 ③ **各機構を「Claude にこう頼めば作ってくれる」プロンプト例で導入できる**

<!--
前章では CLAUDE.md の役割と、4 階層構造で連結読み込みされる仕組みを学びました。本章はその周りにある仲間たちを広げます。最初に数の整理をしておきます — 本章で押さえる名前は agents / commands / skills / imports の 4 つ。このうち commands と skills は実は「同じ機能の旧/新形式」なので、機能としては 3 つ、書き方は 4 つです。本章全体を通じて、ずっとこの「4 つの仲間」という言い方で進めますので、最初に頭に入れておいてください。3 つのゴールのうち最も重要なのが ② の commands と skills の関係、そして ③ の「皆さんが手書きしない・Claude に作らせる」というスタンスです。
-->

---

# 🎯 本章のスタンス — 実装は Claude に書かせる前提

> 📌 **重要な前提**: agents / commands / skills / imports の **実装ファイルは、皆さんが手書きで書きません**

| 従来の発想 | 本講座の発想 |
|----------|------------|
| YAML フロントマターの書式を覚えて手で書く | **Claude に「こう作って」と頼む** |
| SKILL.md の構造を写経して練習 | **Claude が生成・受講者は確認するだけ** |
| シェルスクリプト / Markdown の文法に詰まる | **文法は Claude の担当・受講者は要件を伝える** |

**理由**:
- 本講座は **L1 プロンプト + L2 コンテキスト + L3 ハーネス** が学習対象
- YAML / Markdown frontmatter の文法習得は L1〜L3 と直接関係なし
- AI 時代の正しいスキルは「**AI に正確に指示できる力**」 — 実装は AI に任せる
- Claude Code は SKILL.md・hook・commands を **プロンプト 1 つで生成可能** (公式仕様)

> **本章で覚えるもの**: 各機構が何をするか / Claude にどう頼めば作ってくれるか / 出来上がりをどう確認するか

<!--
本章の重要な前提を最初に置きます。agents / commands / skills / imports の実装ファイルを、皆さんが手書きで書く必要は一切ありません。従来の発想では YAML フロントマターの書式を暗記したり SKILL.md の構造を写経したりしますが、本講座は違います。実装は Claude に依頼して生成させ、皆さんは Claude に「こう作って」と頼むプロンプトを覚える、そして出来上がりを確認する — このスタイルです。理由はシンプルで、本講座のメインテーマは L1 プロンプトエンジニアリング、L2 コンテキストエンジニアリング、L3 ハーネスエンジニアリングの 3 階層であって、YAML や Markdown frontmatter の文法習得は直接関係ないからです。AI 時代の正しいスキルは「AI に正確に指示できる力」。実装は AI に任せ、受講者はプロンプトと検証のループだけを回す。これが本章のスタンスです。
-->

---

# .md 仲間 4 つの全体像 — 本章で学ぶ範囲

> 🪞 「CLAUDE.md 以外にも、AI が読む説明書がある?」
>
> **結論**: 必須は CLAUDE.md だけ。仲間 4 つは Step 2・Step 3 で段階的に導入する拡張機能

**本章で新規に学ぶ 4 つの仲間**:

| 仲間 | 一言で言うと | 配置場所 |
|------|------------|---------|
| **.claude/agents/** | AI に役割を与えるサブエージェント定義 | `.claude/agents/<name>.md` |
| **.claude/commands/** (旧形式) | カスタムスラッシュコマンド単独定義 | `.claude/commands/<name>.md` |
| **.claude/skills/** (新形式・推奨) | カスタムスラッシュコマンド + ワークフロー (= 複数手順の一連の作業) | `.claude/skills/<name>/SKILL.md` |
| **imports** | CLAUDE.md 内の `@path` 構文 | CLAUDE.md 内部の記法 |

> 📌 **重要**: 上の **commands と skills は同じ機能の旧形式 / 新形式** (2026 年 1 月公式マージ)。書き方は 2 つ・機能は 1 つ。前章で学んだ CLAUDE.md と global CLAUDE.md は本章では復習扱い

<!--
.md 仲間 4 つの全体像です。本章で新規に学ぶのは agents / commands / skills / imports の 4 つ。表の 2 行目と 3 行目に注目してください — commands と skills は同じ機能を実現する 2 つの書き方で、commands が旧形式、skills が新形式です。本章で最重要のポイントなので、後ほど専用スライドで詳解します。ワークフローは「複数の手順を順番に実行する一連の作業」のことです。前章で学んだ CLAUDE.md (プロジェクトの説明書) と global CLAUDE.md (全プロジェクト共通の好み) は本章では復習扱いで、新しい話としては出てきません。
-->

---

# .claude/agents/ — AI に「役割」を与えるサブエージェント定義

**1 つのプロジェクトで AI の「役割」を切り替える仕組み**:

イメージ: 1 つの会社に「営業部」「開発部」「品質管理部」があるように、同じ AI に役割別マニュアルを用意

```
「フロントエンド専門エージェントを使って、このボタンの色を変えて」
  → Claude が .claude/agents/frontend.md の指針に従って回答

「コードレビュアー エージェントでこの PR を見て」
  → Claude が .claude/agents/reviewer.md の指針に従って回答
```

**配置場所**: `.claude/agents/<name>.md` (プロジェクト) / `~/.claude/agents/<name>.md` (ユーザー)
**1 ファイル = 1 エージェント**・**ファイルの中身は Claude に作らせる** (次スライドでプロンプト例)

> 1 つの CLAUDE.md + 複数のサブエージェント定義 = プロジェクト内の役割分担

<!--
agents は AI に役割を切り替えさせる仕組みです。1 ファイル 1 エージェントで `.claude/agents/<名前>.md` に配置します。配置パスと「これが何をするか」だけ押さえてください。ファイル中身は Claude に作らせるので、皆さんが手で書くことはありません。次のスライドで、Claude にこういうプロンプトを投げれば agents を作ってくれる、という具体例を示します。
-->

---

# .claude/agents/ — Claude にこう頼めば作ってくれる

**プロンプト例 1: フロントエンド専門エージェント**:

```
「フロントエンド専門のサブエージェントを作って:
 - 名前: frontend
 - 役割: React / CSS / アクセシビリティを優先する専門家
 - 口調: 丁寧な日本語で・コード例は TypeScript で
 - .claude/agents/frontend.md に保存して」
```

**プロンプト例 2: コードレビュアー**:

```
「コードレビュアーのサブエージェントを作って:
 - 名前: reviewer
 - 着眼点: セキュリティ・パフォーマンス・可読性の 3 軸
 - 出力: 各軸ごとに「OK / 改善余地あり / 致命」の 3 段階評価
 - .claude/agents/reviewer.md に保存して」
```

**受講者がやること**: ① 上記プロンプトを Claude に投げる ② Claude が生成したファイルの中身を確認 ③ 不足があれば「○○の指針も追加して」と追加依頼

> **要件を日本語で伝えるだけ・YAML 文法は覚えない**

<!--
agents 作成のプロンプト例 2 つを並べました。注目してほしいのは、皆さんが書くのはこの「依頼文」だけだということ。YAML フロントマターの書式・項目名・改行ルール — どれも覚える必要なし。Claude が公式仕様に従って生成してくれます。受講者の仕事は ① 要件を日本語で伝える ② 出来たファイルを確認 ③ 不足を追加依頼する — この 3 ステップだけ。プロンプト例 1 では「役割」「口調」「コード例の言語」を、プロンプト例 2 では「着眼点」「出力形式」を伝えています。要件を漏れなく伝える、これが L1 プロンプトエンジニアリングです。
-->

---

# .claude/agents/ の呼び出し方 — 5 方式と注意点

**呼び出しの 5 方式 (Claude Code 公式)**:

| # | 方式 | 例 |
|---|------|-----|
| 1 | **description ベースの自動委譲** | Claude が状況判断して自動委譲 |
| 2 | **自然言語でサブエージェント名を指定** | 「フロントエンドエージェントを使って」 |
| 3 | **@-mention** (= `@名前` で名指しする記法) | `@"frontend (agent)"` |
| 4 | **CLI フラグ** (= コマンドライン起動時の追加引数) | `claude --agent frontend "..."` |
| 5 | **Agent ツール経由** | コード/別エージェントから呼出 |

**注意 (混同しやすい点)**:
- `/agents` コマンドはエージェントの **管理** (作成・編集・削除) 用で、**呼出には使わない**
- `/agent <name>` のような **個別呼出コマンドは存在しない**
- 初級では **① description ベースの自動委譲** と **② 自然言語での名指し** を覚えれば十分

<!--
呼び出し方は公式で 5 通り。description ベースの自動委譲、自然言語でのサブエージェント名指定、@-mention、CLI フラグ --agent、Agent ツール経由。初級編では ① と ② を覚えれば十分です。@-mention や --agent や Agent ツール経由は後の章で扱います。注意点として、`/agents` というスラッシュコマンドはエージェントの管理用であって呼び出し用ではありません。`/agent <name>` のような個別呼び出しコマンドは存在しないので、これも混同しないでください。
-->

---

# 🔄 commands と skills は「同じ機能の 2 つの書き方」

**Claude Code 公式の重要仕様 (2026 年 1 月)**:

> 公式 docs ja/skills に明記: 「**カスタムコマンドはスキルにマージされました**」

両者は **カスタムスラッシュコマンドを定義する同じ機能** の **旧形式 / 新形式** です。比較表を読む前に、後ほど何度も出てくる「**description**」という用語をひとつ押さえます:

> 📘 **description とは**: スキル本体ファイル冒頭の **「このスキルは何をするか」を 1-2 行で説明したテキスト**。例: `description: テスト → ビルド → デプロイを順番に実行する`。Claude はユーザー発話とこの description を照合して、「今この skill を起動すべきか」を判断する (= **キーワードマッチ**)

| 項目 | 旧形式: commands | **新形式: skills (推奨)** |
|------|----------------|-----------------------|
| 配置形式 | `.claude/commands/<name>.md` **単一ファイル** | **`.claude/skills/<name>/SKILL.md`** ディレクトリ + エントリポイント (= 起点ファイル) |
| 起動 | `/<name>` スラッシュコマンド | `/<name>` スラッシュコマンド + **description (説明文) マッチで自律発動** |
| 読込挙動 | スラッシュ実行時にロード | **description (説明文) だけ事前にリスト化・本体の手順書は呼ばれた時に開く (= オンデマンド読込)** |
| サポートファイル | なし (単独 .md) | **あり** (ディレクトリ内に補助ファイル配置可) |
| 同名衝突時 | — | **Skills が優先** (Commands は legacy 互換維持) |

> **新規は skills 推奨**・既存 commands は legacy として動作し続ける

<!--
本章で最重要のスライドです。公式 docs の ja/skills ページに「カスタムコマンドはスキルにマージされました」と明記されています。意味するのは、commands と skills は別機能ではなく「カスタムスラッシュコマンドを定義する」同じ機能の旧形式と新形式だということです。比較表を読む前に description という用語を 1 つ押さえます。description は SKILL.md の冒頭に書く 1-2 行の説明文で、「テスト→ビルド→デプロイを順番に実行する」のような短い説明です。Claude はユーザーの発話と各 skill の description を照合して「今この skill を起動すべきか」をキーワードマッチで判断します。これが分かれば表が読めます。旧形式 commands は単一の .md ファイル、新形式 skills はディレクトリの中に SKILL.md という起点ファイルを置く形式。skills が便利なのは、起動時に全 skills の description だけを事前にリスト化しておき、本体の手順書はそのスキルが呼ばれた時に初めて開くから — 「常駐」と言われるとピンと来ませんが、「説明文の一覧だけ持っておいて中身は使う時に開く」と理解してください。同名のスラッシュが両方にあれば Skills 側が優先。とはいえ既存 commands は legacy 互換で動作し続けるので、急に書き直す必要はありません。新規に作るときは skills、と覚えてください。
-->

---

# skills を作る — Claude にこう頼めば作ってくれる

**プロンプト例 1: メール文面起草スキル**:

```
「`/email-draft` という Skill を作って:
 - description: 「メール文面を起草する Skill。メール作成・返信時に使用」
 - 本体: 簡潔なビジネス日本語で・敬語・件名・宛名・本文の構造で
 - .claude/skills/email-draft/SKILL.md に保存して」
```

**プロンプト例 2: デプロイ ワークフロー**:

```
「`/deploy` という Skill を作って:
 - description: 「テスト→ビルド→デプロイを順番に実行する」
 - 本体:
   1. テストを実行
   2. テストが成功したらビルド
   3. ビルドが成功したらデプロイ
   4. 失敗したらエラー内容を報告
 - 失敗時はその場で停止・エラーをユーザーに見せる
 - .claude/skills/deploy/SKILL.md に保存して」
```

> 💡 **条件分岐 (「失敗したら」「成功したら」) は自然言語で書けば Claude が解釈・実行** — スクリプトを別途書く必要なし

<!--
skills を作るプロンプト例 2 つです。最初の例はメール文面起草、2 つ目はデプロイ用ワークフロー。重要ポイント 2 つあります。1 つ目は、皆さんが書くのは「依頼文」だけだということ。SKILL.md の YAML frontmatter の書式や、Markdown のヘッダー階層 — どれも覚える必要なし。Claude が公式仕様に従って生成してくれます。2 つ目は、ワークフローの条件分岐 (「失敗したら止まる」「成功したらビルド」) は自然言語で書けば Claude が解釈して実行してくれるという点。皆さんがシェルスクリプトや if-else を書く必要は一切ありません。日本語で要件を伝える、それだけで動くワークフローが手に入る — これが新しい時代のソフトウェア作りです。
-->

---

# 既存の commands を skills に置き換える — Claude に頼む

**プロンプト例 3: 旧形式 commands を skills に変換**:

```
「`.claude/commands/review.md` の中身を読んで、
 それを新形式の Skill に変換して:
 - 同じ機能を維持
 - .claude/skills/review/SKILL.md に保存
 - description は元の commands の用途から自動推測して書いて
 - 変換後、旧ファイルは削除せず残しておいて (legacy 互換確認用)」
```

**チェックポイント (Claude 生成後の受講者の確認)**:
1. `.claude/skills/review/SKILL.md` が出来ているか
2. description が「ユーザーがコードレビューを依頼したとき自動発動する」内容になっているか
3. `/review` で起動できるか (Claude Code を再起動して確認)

> **commands と skills の同名衝突時は Skills 優先** — 旧 commands を残しても新 skills が動作する

<!--
既存の commands を新形式の skills に置き換えるときも、Claude に依頼するだけです。「このファイルを読んで・新形式に変換して・保存して」と頼めば、旧ファイルの中身を読み取り、SKILL.md の構造に従って書き直してくれます。受講者の仕事は ① 新ファイルが正しい場所に出来ているか確認 ② description が適切な発動条件になっているか確認 ③ 実際にスラッシュコマンドで起動して動くか検証 — この 3 つだけ。Claude Code を一度終了して起動し直すと新ファイルが読み込まれます。前のスライドで触れた「同名衝突時は Skills 優先」のおかげで、旧ファイルを残したまま安全に検証できます。
-->

---

# imports — CLAUDE.md 内の `@path` 構文

**共通設定を複数プロジェクトで共有する仕組み**:

CLAUDE.md の中に `@パス` (= 「このファイルを読み込んで」という記号) と書くと、そのファイルの中身が CLAUDE.md と一緒に起動時にコンテキストへ読み込まれる:

```markdown
# CLAUDE.md の中身
@shared/coding_rules.md
@shared/test_rules.md
```

**仕様 (Claude Code 公式)**:
- **相対パスはインポート元ファイル基準**・絶対パスも可
- **再帰的インポート可・最大 5 ホップ** (= `@` で読まれたファイルから更に `@` で別ファイルを呼べる回数の上限)
- imports は **CLAUDE.md 内部の構文機能** であり、agents や skills のような独立した「ファイル種別」ではない

**Claude にこう頼めば設定してくれる**:
```
「複数プロジェクトで同じコーディング規約を使いたい。
 ~/shared/coding_rules.md に規約を書いて、
 各プロジェクトの CLAUDE.md から @~/shared/coding_rules.md で読み込む構成にして」
```

> 「5 プロジェクトで同じルールをコピペしている」なら imports で統合せよ

<!--
imports は CLAUDE.md の中から外部ファイルを取り込む仕組みです。`@パス` と書くだけで、そのファイルの中身が展開されて CLAUDE.md と一緒にコンテキストに読み込まれます。相対パスはインポート元ファイル基準、絶対パスも可、最大 5 ホップまで再帰的に辿れます。重要な注意点として、imports は CLAUDE.md 内部の構文機能であって、agents や skills のような独立したファイル種別ではありません。「ファイル仲間」ではなく「CLAUDE.md の書き方の 1 つ」と理解してください。設定するときも Claude に「こういう構成にして」と頼めば、共通ルールファイルの配置と各プロジェクトの CLAUDE.md からの参照を一括で設定してくれます。
-->

---

# 前章復習 — global CLAUDE.md と本章 4 仲間の関係

**前章で学んだ global CLAUDE.md** (= 4 階層構造のユーザー層):

配置場所: `~/.claude/CLAUDE.md`

```markdown
# 全プロジェクト共通の好み
- 回答は日本語で
- コメントは最小限に
- テストは必ず書く
```

**global と project CLAUDE.md の関係 (前章復習)**:
- すべてのプロジェクトで自動読込
- project の CLAUDE.md と **「上書き」ではなく「連結」** されて AI に渡される
- 矛盾時は **project が後に読まれるため Claude はそちらに従う傾向** (= 「後勝ち」)

**本章 4 仲間との関係**: agents / skills / imports は **project スコープ** で動く (`.claude/` 配下) ・global CLAUDE.md は **全プロジェクト横断** で動く。両者は重複せず役割分担

> global = 全体の好み / project CLAUDE.md = 固有のルール / 本章 4 仲間 = project 固有の拡張機能

<!--
global CLAUDE.md は前章で学んだ 4 階層構造のユーザー層に当たるファイルで、本章では新しい話としては出てきません。ホームディレクトリ下の .claude フォルダに置いて、「回答は日本語で」「コメントは最小限に」といった、すべてのプロジェクトに共通する好みを書いておくと、どのプロジェクトを開いても AI がその好みを反映します。前章の復習として、global と project CLAUDE.md は「上書き」ではなく「連結」されて AI に渡される点、矛盾時は project が後に読まれるため Claude はそちらに従う傾向 (= 後勝ち) を再度押さえてください。本章で学んだ 4 仲間 (agents / commands / skills / imports) はすべて project スコープで動くので、global CLAUDE.md とは役割分担になります。
-->

---

# レイヤー構造 (= 層になった重なり構造) と 導入順序

**本章 4 仲間 + 前章既習 2 つを「適用範囲が広い順」に並べた構造**:

| レイヤー | 機構 | 適用範囲 |
|---------|------|---------|
| **Global** | global CLAUDE.md (前章) | 全プロジェクト |
| **Project** | CLAUDE.md (前章) | 1 プロジェクト全体 |
| **Role** | .claude/agents/ / imports (本章) | プロジェクト内の役割・共通設定 |
| **Operation** | skills (新) / commands (旧) (本章) | 定型操作・ワークフロー |

**初心者の 3 段階拡張パス**:

| 段階 | 導入する機構 | タイミング | 受講者がやること |
|------|------------|-----------|---------------|
| **Step 1** | CLAUDE.md | 最初から (必須) | Claude に「30 行 ミニマムで作って」と依頼 |
| **Step 2** | skills (or commands) / global CLAUDE.md | 同じ指示を 3 回以上書いたら | Claude に「/○○ という Skill を作って」と依頼 |
| **Step 3** | .claude/agents/ / imports | チーム開発・複雑化したら | Claude に「○○専門エージェントを作って」と依頼 |

<!--
レイヤー構造 — 層になった重なり構造 — として整理しました。上位ほど適用範囲が広く、下位ほど具体的な操作の自動化です。すべての層は前章で学んだ通り「連結」されて AI に渡されます。導入順序は 3 段階。Step 1 は CLAUDE.md だけ、Step 2 で skills と global CLAUDE.md、Step 3 で agents と imports。表の右端列に「受講者がやること」を追加しました — どの段階でも皆さんがやるのは「Claude にこう作ってと頼む」プロンプトを投げることだけ。同じ指示を 3 回以上書いたら skills 化するサイン、という具体的な判断基準を持ってください。
-->

---

# 📚 まとめ + 確認問題

**この章で学んだこと**:
1. **.md 仲間 4 つ**: agents / commands / skills / imports — これだけ覚える
2. **commands と skills は同じ機能の旧/新 2 書き方** — 公式 2026 年 1 月マージ・**新規は skills 推奨**・既存 commands は legacy 互換・同名衝突は Skills 優先
3. skills 配置は **`.claude/skills/<name>/SKILL.md`** ディレクトリ + エントリポイント (= 起点ファイル) 形式・**description (説明文) マッチで自律発動**・description だけ事前リスト化し本体はオンデマンド (必要時) 読込
4. .claude/agents/ 呼出は **5 方式** (自動委譲・自然言語・@-mention・CLI フラグ・Agent ツール)・`/agent <name>` は存在しない
5. imports は **CLAUDE.md 内の `@path` 構文** (最大 5 ホップ・独立ファイル種別ではない)
6. **実装は Claude に書かせる前提** — 受講者は「こう作って」と頼むプロンプトを覚えるだけ

**確認問題**:
- **Q1**: commands と skills の関係は? <details><summary>解答</summary>同じカスタムスラッシュコマンド機能の旧形式・新形式 (2026 年 1 月公式マージ)。新規は skills 推奨・既存 commands は legacy 互換。同名衝突時は Skills 優先。</details>
- **Q2**: skills の配置形式と読込挙動は? <details><summary>解答</summary>`.claude/skills/<name>/SKILL.md` ディレクトリ + エントリポイント形式。description (説明文) だけ事前リスト化・本体の手順書はオンデマンド (呼ばれた時に開く) 読込。description キーワードマッチで自律発動。</details>
- **Q3**: 「メール文面起草の Skill」を作りたい。受講者が書くのは? <details><summary>解答</summary>Claude への依頼プロンプト 1 つ。例: 「`/email-draft` という Skill を作って・description は『メール文面起草』・本体は丁寧な日本語で・`.claude/skills/email-draft/SKILL.md` に保存して」。SKILL.md 自体は Claude が生成する。受講者は出来上がりを確認・不足を追加依頼するだけ。</details>

<!--
まとめと確認問題です。最重要は 2 つ。1 つ目は、本章で覚えるのは agents / commands / skills / imports の 4 つの名前だけ、そして commands と skills が「同じ機能の 2 つの書き方」であること。これさえ押さえれば、Claude Code 解説記事や OSS のリポジトリを読む時に「commands と skills どっち使うんだろう」と迷わなくなります。新規は skills、既存 commands は legacy として動作継続。2 つ目は本章の最重要スタンス — 実装は Claude に書かせる前提。皆さんが学ぶのは YAML や Markdown の文法ではなく、「Claude にこう作ってと頼む」プロンプトの書き方。3 問の確認問題に答えられれば本章マスターです。
-->

---

<!-- _class: cover -->

# 第 3 章 完了
## 次は第 4 章「歴史と意義 — なぜ 3 階層なのか」

<div class="meta">
✅ .md 仲間 4 つ (agents / commands / skills / imports) を覚えた<br>
✅ <b>commands と skills は同じ機能の旧/新 2 書き方</b> (2026 年 1 月公式マージ)<br>
✅ skills 配置: <code>.claude/skills/&lt;name&gt;/SKILL.md</code> ディレクトリ + エントリポイント<br>
✅ description (説明文) だけ事前リスト化・本体はオンデマンド読込<br>
✅ .claude/agents/ 呼出 5 方式 (自動委譲・自然言語・@-mention・CLI フラグ・Agent ツール)<br>
✅ imports は CLAUDE.md 内の <code>@path</code> 構文 (最大 5 ホップ)<br>
✅ <b>実装は Claude に書かせる前提</b> — 受講者はプロンプトを書くだけ<br><br>
🚀 <b>次章は 3 階層モデル (プロンプト/コンテキスト/ハーネス) の歴史と意義を学びます</b><br><br>
<b>続けて第 4 章をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章では .md 仲間 4 つを学びました — agents / commands / skills / imports。最重要は commands と skills が「同じ機能の 2 つの書き方」であるという公式仕様。これを知っているだけで Claude Code の解説記事や OSS リポジトリを読む時に迷いがなくなります。そして本章のもう 1 つの柱は、実装は Claude に書かせる前提。皆さんは YAML や Markdown の文法を覚えるのではなく、「Claude にこう作ってと頼むプロンプト」を覚えました。次の第 4 章では、なぜ 3 階層 (プロンプト・コンテキスト・ハーネス) という構造が必要なのか、歴史的な背景から解説します。
-->
