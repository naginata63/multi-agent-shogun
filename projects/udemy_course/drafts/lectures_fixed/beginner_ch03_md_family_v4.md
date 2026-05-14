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

# 「コピペ地獄」を抜ける — 設定ファイル6機構の使い分け早見表
## CLAUDE.md だけでは届かない領域を埋める — agents / commands / skills / imports と 2026 年 1 月の公式マージ

<div class="meta">
第3章 (約 30 min)<br><br>
「Claude Code はじめての一歩 — AI開発の基礎を1日で習得」<br><br>
</div>

<!--
スピーカーノート:
こんにちは。第3章「.md 仲間たち」を始めます。質問させてください — 前章で書いた CLAUDE.md だけで、本当に AI を使いこなせていますか? 同じプロジェクトで AI に「フロントエンド専門家」と「コードレビュアー」を切り替えて動かしたいとき、毎回 1000 字のレビュー指示文をコピペしている定型操作をスラッシュ一発で起動したいとき、「テスト→ビルド→失敗時に止まる」のような条件分岐を含む自動化をしたいとき — CLAUDE.md だけでは届きません。さらに Claude Code は 2026 年 1 月に「カスタムコマンドはスキルにマージされました」という重要な仕様変更を公式アナウンスしました。本章はこのマージの実像も含め、CLAUDE.md を支える 4 つの仲間たち — agents / commands / skills / imports — を 30 分で押さえます。
-->

---

# 🗺️ 前章の復習 → 本章で広げる範囲 + ゴール

**前章 (第 2 章) で身に付けたこと**:
- CLAUDE.md = AI に読ませるプロジェクトの説明書 (3 階層モデルの **L2 コンテキスト**)
- **4 階層構造** (管理 / ユーザー / プロジェクト / ローカル) を **「連結」して読込**
- **5 セクション 30 行** ミニマムで始める
- **新しい会話/セッション開始時に自動読込** (`/clear`・`/compact` 後も再読込)

**本章 (第 3 章) で広げること**: CLAUDE.md の周りにある **.md 仲間たち** = **agents / commands / skills / imports**。CLAUDE.md が「プロジェクト全体の説明書」なら、これらは「特定用途の補強パッケージ」

**🎯 30 分のゴール**: ① 4 つの仲間の役割を 1 行で説明できる ② **commands と skills が「同じ機能の 2 つの書き方」(2026 年 1 月公式マージ)** であることを理解 ③ 初心者がどの順番で導入すべきか判断できる

<!--
前章では CLAUDE.md の役割と、4 階層構造で連結読み込みされる仕組みを学びました。本章はその周りにある仲間たちを広げます。3 つのゴールのうち最も重要なのが ② の commands と skills の関係です。公式ドキュメントに「カスタムコマンドはスキルにマージされました」と明記された重要な仕様変更で、後ほど詳しく扱います。
-->

---

# .md 仲間たちの全体像 — 4 つの仲間 + (前章復習) global

> 🪞 「CLAUDE.md 以外にも、AI が読む説明書がある?」
>
> **結論**: 必須は CLAUDE.md だけ。仲間たちは Step 2・Step 3 で段階的に導入する拡張機能

| 機構 | 一言で言うと | 配置場所 |
|------|------------|---------|
| **CLAUDE.md** (前章) | プロジェクトの説明書 | `./CLAUDE.md` |
| **.claude/agents/** | AI に役割を与えるサブエージェント定義 | `.claude/agents/<name>.md` |
| **commands / skills** | カスタムスラッシュコマンド・ワークフロー (= 複数手順の一連の作業) — **同じ機能の 2 つの書き方** | 次スライドで詳解 |
| **imports** | CLAUDE.md 内の `@path` 構文 | CLAUDE.md 内部 |
| **global CLAUDE.md** (前章 4 階層のユーザー層) | 全プロジェクト共通の好み | `~/.claude/CLAUDE.md` |

> commands と skills は別機能ではなく、**同じ機能の旧形式・新形式** (詳細は後ほど)

<!--
.md 仲間たちの全体像です。CLAUDE.md は前章で学びましたから、本章は agents / commands / skills / imports の 4 つが新しい話。global CLAUDE.md は前章 4 階層構造のユーザー層に当たるので、新しいファイルというより前章の振り返り扱いです。表の 3 行目「commands と skills」が本章で最も重要なポイント — 別機能ではなく「同じ機能の旧形式・新形式」だという点を、ここでまず認識してください。ワークフローは「複数の手順を順番に実行する一連の作業」のことです。
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
**ファイル形式**: YAML フロントマター (= ファイル冒頭にメタ情報を書く領域) 付き Markdown・**1 ファイル = 1 エージェント**

> 1 つの CLAUDE.md + 複数の `.claude/agents/*.md` = プロジェクト内の役割分担

<!--
agents は AI に役割を切り替えさせる仕組みです。1 ファイル 1 エージェントで `.claude/agents/<名前>.md` に配置します。ファイル冒頭の YAML フロントマター — メタ情報を書く領域 — に description などを記述します。フロントエンド専門、バックエンド専門、コードレビュー専門と役割別マニュアルを置けば、同じプロジェクト内で複数の専門家として動かせます。次のスライドで呼び出し方を整理します。
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
| 5 | **Agent (旧 Task) ツール経由** | コード/別エージェントから呼出 |

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

両者は **カスタムスラッシュコマンドを定義する同じ機能** の **旧形式 / 新形式** です:

| 項目 | 旧形式: commands | **新形式: skills (推奨)** |
|------|----------------|-----------------------|
| 配置形式 | `.claude/commands/<name>.md` **単一ファイル** | **`.claude/skills/<name>/SKILL.md`** ディレクトリ + エントリポイント (= 起点ファイル) |
| 起動 | `/<name>` スラッシュコマンド | `/<name>` スラッシュコマンド + **description マッチで自律発動** |
| 読込挙動 | スラッシュ実行時にロード | **description のみ常駐・本体はオンデマンド (= 必要時) 読込** |
| サポートファイル | なし (単独 .md) | **あり** (ディレクトリ内に補助ファイル配置可) |
| 同名衝突時 | — | **Skills が優先** (Commands は legacy 互換維持) |

> **新規は skills 推奨**・既存 commands は legacy として動作し続ける

<!--
本章で最重要のスライドです。公式 docs の ja/skills ページに「カスタムコマンドはスキルにマージされました」と明記されています。意味するのは、commands と skills は別機能ではなく「カスタムスラッシュコマンドを定義する」同じ機能の旧形式と新形式だということです。旧形式 commands は単一の .md ファイル、新形式 skills はディレクトリの中に SKILL.md という起点ファイルを置く形式です。skills は description キーワードマッチで Claude が自動発動・本体を必要時にだけ読み込むオンデマンド方式・ディレクトリ内に補助ファイルを置けるなどの利点があります。同名のスラッシュが両方にあれば Skills 側が優先。とはいえ既存 commands は legacy 互換で動作し続けるので、急に書き直す必要はありません。新規に作るときは skills、と覚えてください。
-->

---

# commands / skills の具体例 — 旧形式 vs 新形式

**旧形式 commands** — `.claude/commands/review.md` (単一ファイル):

```markdown
以下のファイルのコードレビューをお願いします。
- セキュリティ上の問題がないか確認
- パフォーマンスの改善点
- 可読性
```

→ `/review` と入力すると定型プロンプトが起動

**新形式 skills** — `.claude/skills/deploy/SKILL.md` (ディレクトリ + エントリポイント):

```markdown
1. テストを実行
2. テストが成功したらビルド
3. ビルドが成功したらデプロイ
4. 失敗したらエラー内容を報告
```

→ `/deploy` 起動 + 「デプロイして」の自然言語でも description マッチで自律発動

> **本質的差**: skills は **条件分岐 (= 結果に応じて次の処理を変える書き方) を含むワークフロー**、補助ファイル、自律発動が使える上位互換

<!--
旧形式と新形式の具体例を並べました。commands は 1 つの .md ファイルに定型プロンプトを書くだけ。skills は <name> というディレクトリの中に SKILL.md を置き、中身は複数ステップのワークフロー、結果に応じて次の処理を変える条件分岐を含められます。例えばテスト→ビルド→デプロイで「失敗したらここで止まる」というのが条件分岐です。さらに「デプロイして」のような自然言語でも description マッチで自律発動できるのが skills の強み。本質的に skills は commands の上位互換と理解してください。
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
- imports は **CLAUDE.md 内部の構文機能** であり、commands や skills のような独立した「.md ファイル種別」ではない

> 「5 プロジェクトで同じルールをコピペしている」なら imports で統合せよ

<!--
imports は CLAUDE.md の中から外部ファイルを取り込む仕組みです。`@パス` と書くだけで、そのファイルの中身が展開されて CLAUDE.md と一緒にコンテキストに読み込まれます。相対パスはインポート元ファイル基準、絶対パスも可、最大 5 ホップまで再帰的に辿れます。重要な注意点として、imports は CLAUDE.md 内部の構文機能であって、commands や skills のような独立したファイル種別ではありません。「ファイル仲間」ではなく「CLAUDE.md の書き方の 1 つ」と理解してください。
-->

---

# global CLAUDE.md — 全プロジェクト共通設定 (前章 4 階層のユーザー層)

**あなたの PC 全体で共有する「AI の好み」**:

配置場所: `~/.claude/CLAUDE.md` = 前章 4 階層構造の **ユーザー層**

```markdown
# 全プロジェクト共通の好み
- 回答は日本語で
- コメントは最小限に
- テストは必ず書く
```

**前章の復習 — global と project CLAUDE.md の関係**:
- すべてのプロジェクトで自動読込
- project の CLAUDE.md と **「上書き」ではなく「連結」** されて AI に渡される
- 矛盾時は **project が後に読まれるため Claude はそちらに従う傾向** (= 「後勝ち」)

> global = 全体の好み / project CLAUDE.md = 固有のルール (両者は連結)

<!--
global CLAUDE.md は前章 4 階層構造のユーザー層に当たるファイルです。ホームディレクトリ下の .claude フォルダに置きます。「回答は日本語で」「コメントは最小限に」といった、すべてのプロジェクトに共通する好みを書いておくと、どのプロジェクトを開いても AI がその好みを反映します。前章の復習として、global と project CLAUDE.md は「上書き」ではなく「連結」されて AI に渡される点を再度押さえてください。矛盾時は project が後に読まれるため Claude はそちらに従う傾向、これを「後勝ち」と呼びます。
-->

---

# レイヤー構造 (= 層になった重なり構造) と 導入順序

**5 機構を「適用範囲が広い順」に並べた構造**:

| レイヤー | 機構 | 適用範囲 |
|---------|------|---------|
| **Global** | global CLAUDE.md | 全プロジェクト |
| **Project** | CLAUDE.md | 1 プロジェクト全体 |
| **Role** | .claude/agents/ / imports | プロジェクト内の役割・共通設定 |
| **Operation** | skills (新) / commands (旧) | 定型操作・ワークフロー |

**初心者の 3 段階拡張パス**:

| 段階 | 導入する機構 | タイミング |
|------|------------|-----------|
| **Step 1** | CLAUDE.md | 最初から (必須) |
| **Step 2** | skills (or commands) / global CLAUDE.md | 同じ指示を 3 回以上書いたら / PC 設定時に 1 回 |
| **Step 3** | .claude/agents/ / imports | チーム開発・複雑化したら |

<!--
レイヤー構造 — 層になった重なり構造 — として整理しました。上位ほど適用範囲が広く、下位ほど具体的な操作の自動化です。すべての層は前章で学んだ通り「連結」されて AI に渡されます。導入順序は 3 段階。Step 1 は CLAUDE.md だけ。Step 2 で skills (または legacy の commands) と global CLAUDE.md。Step 3 で agents と imports。「全部書かないといけないの?」という不安は無用です。同じ指示を 3 回以上書いたら skills 化するサイン、という具体的な判断基準を持ってください。
-->

---

# 📚 まとめ + 確認問題

**この章で学んだこと**:
1. **.md 仲間たち**は 4 つ: agents / commands / skills / imports + (前章復習の) global
2. **commands と skills は同じ機能の旧/新 2 書き方** — 公式 2026 年 1 月マージ・**新規は skills 推奨**・既存 commands は legacy 互換・同名衝突は Skills 優先
3. skills 配置は **`.claude/skills/<name>/SKILL.md`** ディレクトリ + エントリポイント (= 起点ファイル) 形式・description マッチで自律発動・本体オンデマンド読込
4. .claude/agents/ 呼出は **5 方式** (自動委譲・自然言語・@-mention・CLI フラグ・Agent ツール)・`/agent <name>` は存在しない
5. imports は **CLAUDE.md 内の `@path` 構文** (最大 5 ホップ・独立ファイル種別ではない)
6. 導入は **Step 1: CLAUDE.md → Step 2: skills/global → Step 3: agents/imports** の順

**確認問題**:
- **Q1**: commands と skills の関係は? <details><summary>解答</summary>同じカスタムスラッシュコマンド機能の旧形式・新形式 (2026 年 1 月公式マージ)。新規は skills 推奨・既存 commands は legacy 互換。同名衝突時は Skills 優先。</details>
- **Q2**: skills の配置形式と読込挙動は? <details><summary>解答</summary>`.claude/skills/<name>/SKILL.md` ディレクトリ + エントリポイント形式。description のみ常駐・本体はオンデマンド読込。description マッチで自律発動。</details>
- **Q3**: 5 プロジェクトで共通のコーディング規約を 1 箇所管理するには? <details><summary>解答</summary>imports または global CLAUDE.md。imports は CLAUDE.md 内 `@path` 構文・チーム共有向け / global は `~/.claude/CLAUDE.md`・個人の好み。</details>

<!--
まとめと確認問題です。最重要は、commands と skills が「同じ機能の 2 つの書き方」であること。これさえ押さえれば、Claude Code 解説記事や OSS のリポジトリを読む時に「commands と skills どっち使うんだろう」と迷わなくなります。新規は skills、既存 commands は legacy として動作継続、と覚えてください。3 問の確認問題に答えられれば本章マスターです。
-->

---

<!-- _class: cover -->

# 第 3 章 完了
## 次は第 4 章「歴史と意義 — なぜ 3 階層なのか」

<div class="meta">
✅ .md 仲間たち 4 つ + (前章復習) global の全体像<br>
✅ <b>commands と skills は同じ機能の旧/新 2 書き方</b> (2026 年 1 月公式マージ)<br>
✅ skills 配置: <code>.claude/skills/&lt;name&gt;/SKILL.md</code> ディレクトリ + エントリポイント<br>
✅ .claude/agents/ 呼出 5 方式 (自動委譲・自然言語・@-mention・CLI フラグ・Agent ツール)<br>
✅ imports は CLAUDE.md 内の <code>@path</code> 構文 (最大 5 ホップ)<br>
✅ レイヤー構造と 3 段階導入順序<br><br>
🚀 <b>次章は 3 階層モデル (プロンプト/コンテキスト/ハーネス) の歴史と意義を学びます</b><br><br>
<b>続けて第 4 章をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章では .md 仲間たち 4 つを学びました。最重要は commands と skills が「同じ機能の 2 つの書き方」であるという公式仕様。これを知っているだけで Claude Code の解説記事や OSS リポジトリを読む時に迷いがなくなります。新規は skills、既存 commands は legacy として動作継続。次の第 4 章では、なぜ 3 階層 (プロンプト・コンテキスト・ハーネス) という構造が必要なのか、歴史的な背景から解説します。
-->
