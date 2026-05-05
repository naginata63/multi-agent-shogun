---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 0.85em; }
  h1 { font-size: 1.4em; color: #c8102e; border-bottom: 3px solid #c8102e; padding-bottom: 0.2em; }
  h2 { font-size: 1.15em; color: #2563eb; }
  h3 { font-size: 1.0em; color: #4b5563; }
  table { font-size: 0.75em; }
  code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
  pre { background: #2b2b2b; color: #f8f8f2; padding: 8px; font-size: 0.7em; }
  blockquote { font-size: 0.85em; font-style: italic; border-left: 4px solid #2563eb; padding-left: 0.5em; }
---

# ch01. プロンプトを資産にする — `/command` と Skill 布石

## プロンプト層の第一歩

---

## この章で解決する「困りごと」

> **① 既にあるものを確認せず新規作成してしまう**
> **② 同じ作業を毎回手動で繰り返している**

- 先週も似たプロンプトを書いた気がする…
- 議事録要約のプロンプト、どこに保存したっけ？
- 毎回ゼロからプロンプトを書いている。書くたびに品質がブレる

> プロンプトが「使い捨て」だから、同じ労力を何度も払っている

---

## 章のゴール

**言える 1 文:**
> プロンプトを `/command` として保存すれば、次から 1 コマンドで同じ品質の結果を得られる

**できる 1 動作:**
> 1 つの `/command` を作って動かせる。自分の業務で `/command` 化候補を 3 件挙げられる

---

## 「使い捨て」と「資産」の違い

| | 使い捨てプロンプト | 資産化プロンプト |
|---|---|---|
| 書く回数 | 毎回ゼロから | **1 回だけ** |
| 品質 | 毎回ブレる | **安定** |
| 探す手間 | 「どこに書いたっけ?」 | **コマンド 1 つ** |
| 改善 | 毎回一から直す | **蓄積される** |

> 1 回書いて何度でも使える = **資産**

---

## `/command` — プロンプトを資産にする仕組み

```
.claude/commands/
  └── summarize-meeting.md   ← このファイルがプロンプト本体
```

- `.claude/commands/` フォルダに Markdown ファイルを置くだけ
- ファイル名がそのままコマンド名になる
- 例: `summarize-meeting.md` → `/summarize-meeting` で呼び出し

---

## 実演: `/command` を作ってみよう

### Step 1 — フォルダを作る

プロジェクトのルートに `.claude/commands` フォルダを作ります:

```bash
mkdir -p .claude/commands
```

> ※ VS Code のエクスプローラーから「新しいフォルダー」で作っても OK です

### Step 2 — プロンプトファイルを書く

```markdown
<!-- .claude/commands/summarize-meeting.md -->
以下の議事録を読み、要点を 3 つにまとめてください。

## 出力形式
- 決定事項
- 次回のアクション
- 未解決の課題

## 対象ファイル
$ARGUMENTS
```

> `$ARGUMENTS` には、コマンド呼び出し時に渡した内容が入ります。
> 後ほど実演します。

---

## 実演: `/command` を呼び出す

### Step 3 — 使う

プロンプト欄にこう入力するだけ:

```
/summarize-meeting @meeting-2026-05-06.md
```

- `/summarize-meeting` = コマンド名
- `@meeting-2026-05-06.md` = 対象ファイル (引数)
  - `@ファイル名` で AI にそのファイルを読み込ませます

> **毎回プロンプトを書く必要がなくなりました**

---

## 引数付き呼出の仕組み

```markdown
<!-- .claude/commands/weekly-report.md -->
以下の進捗データから、週次レポートを作成してください。

## フォーマット
1. 今週の成果 (3 行以内)
2. 課題と対応状況
3. 来週の予定

## 対象
$ARGUMENTS
```

```
/weekly-report @progress.md
```

- `$ARGUMENTS` の位置に `@progress.md` の中身が差し込まれるイメージ
- **プロンプトの中身は変えずに、対象だけ変えられる**

---

## Script / Slash Command / Skill — 3 つの道具の使い分け

| 観点 | Script (Bash 等) | Slash Command (`/name`) | Skill |
|------|------------------|------------------------|-------|
| 起動 | コマンドライン手動 | プロンプト中で AI が呼ぶ | **AI が自律判断で呼ぶ** |
| 配置 | 任意のフォルダ | `.claude/commands/*.md` | `.claude/skills/*.md` |
| 引数 | CLI 引数 | `@file` 等の参照 | AI がプロンプトから抽出 |
| 学習負荷 | 低 | 中 | やや高 (但し再利用最大) |
| 用途 | 手動繰り返し作業 | 定型プロンプトの資産化 | **業務領域知識の常駐化** |
| 本講座での位置 | 補助 | **← 今ここ (ch01)** | 到達点 (ch11) |

---

## 3 つの道具 — ざっくり言うと

- **Script**: シェルスクリプトと同じ。手動で叩く
- **Slash Command**: `/名前` で呼び出す定型プロンプト。**本章の主役**
- **Skill**: AI が文脈を判断して**勝手に呼び出す**。ch11 で作る

> まずは `/command` をマスターして、最後に Skill に到達する。

---

## 業務 3 例 — `/command` 化候補あぶり出し

### 営業パーソンの例
- 毎回やっている: 顧客への提案メールをゼロからプロンプトで書く
- `/command` 化: `.claude/commands/proposal-email.md`
  - 「顧客名・商談内容・条件を入力して提案メールを作成」
  - 次から `/proposal-email` で 1 発

### PM サポートの例
- 毎回やっている: 進捗レポートのフォーマットから毎回作り直す
- `/command` 化: `.claude/commands/weekly-report.md`
  - `/weekly-report @進捗.md` で即座に生成

### データ分析者の例
- 毎回やっている: 「このデータの傾向を教えて」と毎回手動で書く
- `/command` 化: `.claude/commands/analyze-trend.md`
  - `/analyze-trend @sales.csv` で 1 発

---

## あなたの業務で 3 つ挙げてみよう

> **動画を止めて**、自分の業務で「毎回ゼロから書いているプロンプト」を 3 つ挙げてください。

1. _______________ → `/command` 名: _________
2. _______________ → `/command` 名: _________
3. _______________ → `/command` 名: _________

> この 3 つが、あなたの最初の資産になります。

---

## Skill 布石 — 次の段階への预告

> `/command` は**人間が呼ぶ**道具です。
> **Skill** は AI が**自律判断で呼ぶ**道具です。

**例:**
- `/command` 版: `/proposal-email` と手動で呼ぶ
- **Skill** 版: 商談メモを渡すと、AI が**勝手に**過去の提案パターンを参照してメールを作る

> Skill の詳細は **ch11** で。まずは `/command` で土台を固めましょう。

---

## 章のまとめ

- プロンプトは**使い捨て**から**資産**に変えられる
- `.claude/commands/` に置くだけで `/command` になる
- 引数 (`$ARGUMENTS`) で対象だけ変えられる
- Script / Slash Command / Skill の使い分けができる
- **自分の業務の `/command` 化候補を 3 つ挙げた**

---

## 持ち帰り

**言える 1 文:**
> プロンプトを `/command` として保存すれば、次から 1 コマンドで同じ品質の結果を得られる。さらに Skill に進めば、AI が自律的に呼んでくれるようになる

**できる 1 動作:**
> 1 つの `/command` を作って動かせる。自分の業務で `/command` 化候補を 3 件挙げられる

---

> 強化した層：プロンプト層 (L1) — プロンプトを資産化する第一歩。
