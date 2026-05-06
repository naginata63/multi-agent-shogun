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

# プロンプトを資産にする
## — `/command` と Skill 布石（プロンプト層の第一歩）

<div class="meta">
中級編 — 第1章 (約 30 min)<span class="free">FREE</span><br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

---

# ch01. プロンプトを資産にする — `/command` と Skill 布石

---

## この章で解決する「困りごと」

> **① 既にあるものを確認せず新規作成してしまう**
> **② 同じ作業を毎回手動で繰り返している**

- 先週も似たプロンプトを書いた気がする…
- 議事録要約のプロンプト、どこに保存したっけ？
- 毎回ゼロからプロンプトを書いている。書くたびに品質がブレる

> プロンプトが「使い捨て」だから、同じ労力を何度も払っている

<!-- Speaker note: 第0章で触れた困りごと①「確認せず新規作成」と②「同じ作業を毎回手動」の具体例を示します。「先週も似たプロンプト書いた気がする」という感覚は多くの人が持っているはず。ここで「自分のことだ」と思ってもらいます。 -->

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

<!-- Speaker note: 使い捨てと資産の対比表を解説します。ここで伝えたいのは「書く回数・品質・探す手間・改善」の4軸すべてで資産化が有利ということ。特に「改善が蓄積される」は重要で、使い捨てでは毎回ゼロリセットですが、資産化すれば一度の改善が永続します。 -->

---

## `/command` — プロンプトを資産にする仕組み

```
.claude/commands/
  └── summarize-meeting.md   ← このファイルがプロンプト本体
```

- `.claude/commands/` フォルダに Markdown ファイルを置くだけ
- ファイル名がそのままコマンド名になる
- 例: `summarize-meeting.md` → `/summarize-meeting` で呼び出し

<!-- Speaker note: /commandの仕組みを初めて紹介するスライドです。仕組みはシンプル：Markdownファイルを置くだけ。フォルダ名は.claude/commands/固定。ファイル名＝コマンド名という直感的な対応関係を強調してください。「プログラミング不要」であることも安心材料として伝えます。 -->

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

<!-- Speaker note: 実演のStep1とStep2です。ここでは実際にVS Codeかターミナルを開いてデモすることを推奨。mkdir -p .claude/commands を実行し、summarize-meeting.md をその場で作ることで、受講者に「これだけ？」という驚きを与えます。$ARGUMENTSの概念は次のスライドで詳しく説明します。 -->

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

<!-- Speaker note: Step3の実演です。実際に/summarize-meeting @meeting-2026-05-06.mdと入力してAIがどう動くかを見せます。ポイントは「プロンプトの中身は一切書いていない」こと。コマンド名とファイル参照だけで、あらかじめ用意したフォーマット通りの出力が得られる驚きを伝えてください。 -->

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

<!-- Speaker note: $ARGUMENTSの仕組みを図解します。「テンプレートの穴埋め」というイメージで伝えると分かりやすい。プロンプトの中身(出力形式や指示)は固定で、対象ファイルだけ差し替える。これが「資産化」の核心です。プログラミングの関数に慣れている人は「引数のようなもの」と説明してもよいです。 -->

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

<!-- Speaker note: 3つの道具のざっくりとした説明です。ここで重要なのは「段階的に学ぶ」というメッセージ。まずScript(手動)→Slash Command(半自動)→Skill(自律)と進む流れを強調。受講者が「Skillまで行かないと意味ない？」と不安にならないよう、「/commandだけでも十分に実用的」であることを伝えてください。 -->

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

<!-- Speaker note: 3つの職種(営業・PM・データ分析)ごとの具体例を紹介します。受講者が自分の職種に近いものを見つけられるように。「これ、まさに自分が毎回やっていることだ」と気づくのがゴール。もし受講者の職種がこれらと違えば、次のスライドで自分の業務に置き換えてもらいます。 -->

---

## あなたの業務で 3 つ挙げてみよう

> **動画を止めて**、自分の業務で「毎回ゼロから書いているプロンプト」を 3 つ挙げてください。

1. _______________ → `/command` 名: _________
2. _______________ → `/command` 名: _________
3. _______________ → `/command` 名: _________

> この 3 つが、あなたの最初の資産になります。

<!-- Speaker note: ここで動画を止めてもらうアクティビティです。「毎回ゼロから書いているプロンプト」を3つ挙げる演習。受講者が自分の業務に当てはめることで理解度が跳ね上がります。演習後に「どんな/commandを作りそうですか？」と問いかけると参加度が上がります。 -->

---

## Skill 布石 — 次の段階への预告

> `/command` は**人間が呼ぶ**道具です。
> **Skill** は AI が**自律判断で呼ぶ**道具です。

**例:**
- `/command` 版: `/proposal-email` と手動で呼ぶ
- **Skill** 版: 商談メモを渡すと、AI が**勝手に**過去の提案パターンを参照してメールを作る

> Skill の詳細は **ch11** で。まずは `/command` で土台を固めましょう。

<!-- Speaker note: Skillは「AIが自律判断で呼ぶ道具」という布石のスライドです。ch11で詳しくやる予告ですが、ここでは「/commandをマスターすれば自然とSkillへの道が開ける」という安心感を与えます。「今は/commandに集中すればOK」というメッセージを忘れずに。 -->

---

## 章のまとめ

- プロンプトは**使い捨て**から**資産**に変えられる
- `.claude/commands/` に置くだけで `/command` になる
- 引数 (`$ARGUMENTS`) で対象だけ変えられる
- Script / Slash Command / Skill の使い分けができる
- **自分の業務の `/command` 化候補を 3 つ挙げた**

<!-- Speaker note: 章のまとめです。5つのポイントを振り返ります。「使い捨て→資産」の意識変化がこの章の最大の成果です。次章(ch02)では「プロンプトの書き方が悪くて失敗する3パターン」を扱います。この章で資産化の土台を作った上で、次章で品質の診断方法を学びます。 -->

---

## 持ち帰り

**言える 1 文:**
> プロンプトを `/command` として保存すれば、次から 1 コマンドで同じ品質の結果を得られる。さらに Skill に進めば、AI が自律的に呼んでくれるようになる

**できる 1 動作:**
> 1 つの `/command` を作って動かせる。自分の業務で `/command` 化候補を 3 件挙げられる

---

> 強化した層：プロンプト層 (L1) — プロンプトを資産化する第一歩。

---

<!-- _class: cover -->

# 第1章 完了
## 次は 第2章「よくある失敗 3 パターンの診断」

<div class="meta">
✅ プロンプトを使い捨てから資産に変えられる<br>
✅ `/command` を作って動かせる<br>
✅ Script / Slash Command / Skill の使い分け<br>
✅ 自分の業務の `/command` 化候補を 3 件挙げた<br><br>
<b>続けて第2章をお楽しみください</b>
</div>
