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

# 自分専用の Skill を作る
## — 3 層統合の到達点

<div class="meta">
中級編 — 第11章 (約 30 min)<span class="free">FREE</span><br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

---

# ch11. 自分専用の Skill を作る — 3 層統合の到達点

> これまでの 3 層をすべて組み合わせて、
> **AI が自律判断で呼び出す「自分専用の常駐道具」** を完成させます。

---

## この章で解決する「困りごと」

> **「3 層は理解したが、自分の業務に常駐する AI 道具がまだ 1 つも完成していない」**

- ch01 で `/command` を覚えた — でも**毎回自分で呼び出す**必要がある
- ch07 で hook を覚えた — でもこれは**発動タイミングの制御**であって**処理の中身**ではない
- **「プロンプトの資産化」と「自動化の仕組み」を統合する、もう一段上の仕組み**が必要

---

## 本章のゴール

**持ち帰り** (章末で言える 1 文):

> 「自分の業務知識を Skill に書き込み、
> AI が文脈で自律的に呼び出す常駐道具を完成させた」

**できるようになること**:
- `.claude/skills/` に自分専用の Skill ファイルを作成できる
- Skill 内で 3 層 (プロンプト / コンテキスト / ハーネス) を統合していることを説明できる
- Skill と hook を連携させて自動発動する構想を立てられる

---

## Skills の縦糸 — 講座全体での繋がり

```
ch01 [布石]    「/command でプロンプトを資産化」
               → 「/command の先にあるもの」として Skill を予告

ch07 [発展]    「hook と Skill の連携」
               → hook = いつ動くか / Skill = 何を呼ぶか

ch11 [完成]    ★ 今ここ ★
               → 自分専用の Skill を完成させる (3 層統合の到達点)
```

---

## `/command` から Skill へ — なぜもう一段上が必要か

**具体例**: 「毎週月曜に議事録を要約して日報を作る」業務

| やり方 | 手順 | 問題点 |
|--------|------|--------|
| 毎回ゼロから書く | プロンプトを毎週新規作成 | 非効率・品質バラつき |
| `/command` 化 | 日報プロンプトを資産化 | まだ**自分で呼び出す**必要がある |
| **Skill 化** ★ | 業務知識を Skill に書き込む | **AI が文脈を読み取って自律的に呼び出す** |

> `/command` = 人が意図的に呼び出す
> **Skill** = AI が文脈を読み取って自律的に呼び出す

---

## Skill の構造 — たった 1 つのファイル

```
.claude/skills/
└── weekly_report.md    ← これ 1 つで「常駐道具」になる
```

**Skill ファイルの中身**:

```yaml
---
name: weekly-report
description: 週次業務日報を半自動生成する。
  議事録要約 + 過去記憶検索 + ドラフト出力。
---
```

```markdown
## この Skill がやること
1. 今週の議事録ファイル (.md) を読み込む
2. 「決定事項」「宿題」「次週の予定」を抽出
3. 過去の週報 (memory) を検索し、継続中タスクを参照
4. 指定フォーマットで週報ドラフトを出力

## 出力フォーマット
### 今週のハイライト (3 行以内)
### 決定事項
### 宿題 (担当・期限付き)
### 来週の予定

## 注意事項
- 推測で補完せず、議事録にない情報は「未記載」と明記
- 前週からの継続タスクは必ず参照
```

---

## Skill を作る手順 (4 ステップ)

### Step 1: 自分の「繰り返し作業」を 1 つ選ぶ (5 分)

> 「毎週 / 毎日 / 毎月、同じ手順でやっていること」を 1 つ見つける

具体例:
- 営業: 商談メモから提案書ドラフトを作る
- PM サポート: ミーティング議事録からタスク管理表を更新する
- データ分析: 分析レポートの定型フォーマットを生成する

### Step 2: 「何を読み込み → 何を出力するか」に分解 (10 分)

> 入力 (何を読むか) → 処理 (どう変換するか) → 出力 (何を作るか)

### Step 3: `.claude/skills/` に frontmatter + 本文を書く (10 分)

> 上記の構造テンプレートに当てはめるだけ

### Step 4: 実際に呼び出して動作確認 (5 分)

> AI に「週報作って」と伝えるだけで Skill が発動する

---

## 3 層統合 — Skill が 3 つの層を統合する仕組み

**Skill 1 つの中に、講座で学んだ 3 層がすべて入っている**:

| 層 | Skill 内での役割 | 対応箇所 |
|----|-----------------|---------|
| **プロンプト層** | 日報フォーマット・抽出ルールの指示 | Skill 本文の「やること」「フォーマット」「注意事項」 |
| **コンテキスト層** | 過去の週報を memory から自動検索 | 「過去の週報を検索」ステップ |
| **ハーネス層** | hook 連携で議事録更新時に自動発動 | ch07 で学んだ hook と連携 (構想レベル) |

> Skill = **3 層を 1 つにまとめた「自分専用の常駐道具」**

---

## 演習: 自分の業務 Skill を作ってみよう

### 演習の流れ

1. **自分の業務で「毎週繰り返している手作業」を 1 つ選ぶ** (5 分)
2. **その手作業を「入力 → 処理 → 出力」に分解する** (10 分)
3. **`.claude/skills/` に frontmatter + 本文を書く** (10 分)
4. **実際に呼び出して動作確認** (5 分)

### 受講者の現場に置き換えたバリエーション

| 業務 | Skill 名 | 入力 | 出力 |
|------|---------|------|------|
| 営業 | `proposal-draft` | 商談メモ | 提案書ドラフト |
| PM サポート | `task-update` | 議事録 | タスク管理表 |
| データ分析 | `report-gen` | クエリ結果 | 定型レポート |

---

## Skill と hook の連携 — さらに先へ

ch07 で学んだ hook と Skill を組み合わせると、**完全な自動化**が実現する:

```
┌───────────────────┐
│  議事録が更新された │ ← タイミング (hook が検知)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Skill が発動する   │ ← 業務知識 (Skill が実行)
│  「週報作成」       │
│  1. 議事録を読む    │
│  2. memory を検索  │
│  3. ドラフトを出力  │
└───────────────────┘
```

> **hook = 「いつ動くか」の引き金**
> **Skill = 「何を呼ぶか」の業務知識セット**
> **hook + Skill = 完全な自動化**

---

## 講座の到達点 — ここまでの旅の振り返り

### 3 層を順に強化してきた軌跡

```
ch01-02  プロンプト層  → 指示を資産化・診断する
ch03-04  コンテキスト層 → 長文を作らない・必要なものを呼び戻す
ch05-08  ハーネス層    → 分業・レビュー・自動化・安全装置
ch09     3 層統合       → 業務に組み込む型
ch10     逆引き辞典     → 困った時の罗針盤
ch11     ★ Skill 完成  → 自分専用の常駐道具
```

### 次の一手

> 自分の現場で **「週に 1 回使う Skill」** を 1 つ作り、
> **1 ヶ月運用**してみる

### 発展: hook 連携で自動化

> ch07 の hook と連携して「ファイル更新で自動発動」を実現する

---

## まとめ

- **Skill** = `.claude/skills/{name}.md` に業務知識を書き込む仕組み
- Skill は **3 層 (プロンプト / コンテキスト / ハーネス) を統合**する
- `/command` は「人が呼ぶ」→ **Skill は「AI が自律的に呼ぶ」**
- hook と Skill を連携させれば、**完全な自動化**が実現する
- 講座の到達点は **「自分専用の常駐 AI 道具」を 1 つ完成させる** こと

> **強化した層: ハーネス層 (L3) — Skill で自分専用の常駐道具を作り上げる。3 層統合の到達点。**

---

<!-- _class: cover -->

# 第11章 完了
## — 中級編 完結

<div class="meta">
✅ Skill の構造と作成手順を理解した<br>
✅ 3 層統合の仕組みを説明できる<br>
✅ 自分の業務 Skill を 1 つ作成した<br>
✅ hook + Skill の連携構想を立てた<br><br>
<b>中級編 全章完結、お疲れさまでした</b>
</div>
