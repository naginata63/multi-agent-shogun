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

# セッション再起動耐性 (Compress戦略)
## LangChainの「圧縮戦略」でセッション断絶から復旧する

<div class="meta">
中級編 v4 — 第7章 (約 40 min)<br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第7章へようこそ。テーマは「セッション再起動耐性」です。LangChainの4戦略のうち、Compress戦略を深く掘り下げます。セッションが切れても、重要な情報を圧縮して保存し、新セッションで復旧する仕組みを解説します。昨日の作業を今日再開したらAIが何も覚えていない、この絶望感を解消する技術です。なぎなたと申します。40分間よろしくお願いします。
-->

---

## この章で学ぶこと [L2: Evaluate + Create]

1. LangChain **Compress戦略** の概念を説明できる
2. セッション断絶の **3パターン** を分類できる
3. **SessionStart hook** の4段階復旧フローを理解する
4. **PreCompact hook** で保存すべき情報を特定できる
5. **handoff** によるセッション状態の保存を理解する
6. 復旧失敗の **典型パターンと対策** を説明できる

> この章のゴール: Compress戦略を使い、セッション断絶を「無かったこと」にできる

<!--
この章では6つの到達点を目指します。まずLangChainのCompress戦略の概念を理解します。次にセッション断絶の3パターンを分類します。SessionStart hookによる4段階復旧と、PreCompact hookによる保存対象の特定を学びます。handoffによる明示的な状態保存を理解し、最後に復旧失敗のパターンと対策を身につけます。Compress戦略は「情報を圧縮して保持する」ことで、限られたコンテキスト領域を最大限に活用する手法です。
-->

---

# LangChain コンテキスト4戦略 — 復習

| 戦略 | 目的 | 対応章 |
|------|------|--------|
| **Write** | AIに正しい情報を書き込む | 第5章 |
| **Select** | 必要な情報だけを選択して取り出す | 第6章 |
| **Compress** | 情報を圧縮して容量を節約する | **本章 (第7章)** |
| **Isolate** | 情報を分離して干渉を防ぐ | 第8章 |

**Compress戦略の本質**:
- コンテキストウィンドウは有限 → 容量を節約する必要がある
- 古い情報を **要約・圧縮** して重要な情報だけを残す
- セッション断絶時にも **圧縮済みの状態** から復旧できる

> Compress = 「情報を捨てる」のではなく「重要な情報だけを残す」

<!--
前章までに学んだLangChainの4戦略をおさらいします。Writeは情報の書き込み、Selectは選択的取り出し、Compressは圧縮による節約、Isolateは分離による干渉防止です。本章ではCompress戦略を深く扱います。Compress戦略の本質は、有限のコンテキストウィンドウで容量を節約しつつ、重要な情報を失わないことです。「捨てる」のではなく「重要なものだけを残す」のがCompressです。
-->

---

# 「AIが初めまして」と言ってきた絶望感

> 昨日の作業を今日再開したら、AIが**何も覚えていない**。
> 「さっきまで一緒に作業していたのに」

**失われるもの**:
- どのファイルを編集中だったか
- 何をテストして、何が残っているか
- なぜその設計判断をしたか

**根本原因**: セッションの断絶。AIの記憶は **1セッション限り** がデフォルト。

> Compress戦略は、この断絶を **「圧縮→保存→復元」** の3段階で解決する

<!--
まずつかみです。昨日の作業を今日再開したら、AIが何も覚えていない。失われるのは、編集中のファイル、テストの進捗、設計判断の理由です。セッションが切れると、AIの記憶はリセットされます。Compress戦略は、この断絶を圧縮と保存と復元の3段階で解決します。重要な情報を圧縮して保存しておけば、新セッションで完全に復旧できます。
-->

---

# セッション断絶の3パターン

| パターン | トリガー | 失われるもの | Compress対応 |
|----------|----------|-------------|-------------|
| **`/clear`** | 明示的リセット | 会話履歴全て | handoffで事前保存 |
| **Compaction** | コンテキスト上限到達 | 古い会話の詳細 | PreCompactで事前保存 |
| **新規起動** | CLI再起動 | セッション全体 | SessionStartで自動復旧 |

**共通点**: どれもコンテキストの一部または全部が消える。

**Compress戦略の対応**:
- 断絶 **前**: 重要情報を圧縮して保存 (PreCompact / handoff)
- 断絶 **後**: 圧縮済み情報から復旧 (SessionStart / rehydrate)

<!--
セッション断絶の3パターンを整理します。スラッシュclearは明示的なリセットで会話履歴が全て消えます。Compactionはコンテキスト上限到達で古い詳細が失われます。新規起動はセッション全体が消えます。Compress戦略の対応は2段階です。断絶前はPreCompact hookとhandoffで重要情報を圧縮保存します。断絶後はSessionStart hookとrehydrateで圧縮済み情報から復旧します。
-->

---

# SessionStart hook — 4段階自動復旧

> 新セッション開始と同時に、圧縮済みの状態から自動復元する仕組み

**4段階のフロー**:

1. **自己識別** — 環境変数から自分の役割を確認
2. **永続記憶の読込** — `memory/*.md` / MCP memory を読み込む
3. **指示ファイルの読込** — `CLAUDE.md` / `instructions/*.md` を読み込む
4. **タスク状態の復元** — YAMLファイルから未完了タスクを特定

**設定方法** (`settings.json`):
```json
{
  "hooks": {
    "SessionStart": [{
      "type": "command",
      "command": "bash scripts/session_start.sh"
    }]
  }
}
```

> この4段階が自動で走ることで、新セッションでも「昨日の続き」が始まる

<!--
SessionStart hookの仕組みです。Claude Codeのセッション開始時に自動実行される処理で、圧縮済みの状態から4段階で復元します。まず環境変数から自己識別し、永続記憶を読み込み、指示ファイルを読み込み、最後にYAMLからタスク状態を復元します。settings.jsonに登録するだけで、毎回のセッション開始時にこの復旧が自動実行されます。Compress戦略の「復元」フェーズを担う仕組みです。
-->

---

# PreCompact hook — 圧縮前に何を保存するか

> Compactionが走る直前に、**失われては困る情報**を圧縮保存する

**保存すべき情報** (Compress戦略の観点):

| 情報 | 理由 | 保存先 |
|------|------|--------|
| 進行中のタスク | 復旧後に再開するため | task YAML |
| 重要な設計判断 | 「なぜそう決めたか」を残す | `memory/*.md` |
| 未コミットの変更 | 変更内容を忘れるため | task YAML |
| コンテキスト使用率 | 次セッションの予算計画 | レポート |

**PreCompact hook の設定**:
```json
{
  "hooks": {
    "PreCompact": [{
      "type": "command",
      "command": "bash scripts/pre_compact.sh"
    }]
  }
}
```

<!--
PreCompact hookはCompress戦略の「圧縮」フェーズを担います。Compactionが走る直前に、失われては困る情報を自動保存します。保存すべき情報は4つ。進行中のタスクは復旧後の再開用にYAMLに保存。設計判断の理由はmemoryに保存。未コミットの変更もYAMLに。コンテキスト使用率はレポートに保存します。SessionStartとPreCompactの2つの公式hookを組み合わせることで、圧縮と復元のサイクルを自動化できます。
-->

---

# handoff設計 — セッション状態の明示的保存

> 「今の状態を保存して、あとで続きから始めたい」— そのためのカスタムコマンド

**handoff がやること**:
1. 現在のセッション状態を収集 (進捗・判断・残作業)
2. YAML形式の引き継ぎファイルを生成
3. 保存先パスをコンソールに表示

**引き継ぎファイルの構造**:

```yaml
task_id: cmd_042
status: in_progress
progress:
  completed: ["src/auth.ts", "src/utils.ts"]
  remaining: ["src/api.ts", "tests/"]
  current_approach: "JWT認証からSession認証へ移行中"
blockers: ["API仕様未確定"]
context_advice: "コンテキスト使用率65%。次回はAPI層から再開"
```

> **機械可読 + 人間可読** のYAML形式。AIも人間も同じファイルを読める

<!--
handoffはCompress戦略の「保存」を明示的に行うカスタムコマンドです。現在のセッション状態を収集し、YAML形式の引き継ぎファイルを生成します。このファイルにはタスクID、ステータス、完了・残作業、現在のアプローチ、ブロッカー、次セッションへの助言が含まれます。機械可読であり人間可読でもあるため、AIも人間も同じファイルから状況を把握できます。圧縮の効果として、長時間のセッション文脈を1つのYAMLに凝縮できます。
-->

---

# 自プロ実例 — PreCompact hook と handoff の実装

> 本講座の制作環境で実際に使っているCompress戦略の実装例

**実例1: PreCompact hook による自動保存** 『本講座サンプル実装』

- Compaction直前に `task YAML` の `status` と `progress` を更新
- 設計判断は `memory/*.md` に自動書込
- 次セッションで `SessionStart` が即座に復旧

**実例2: handoff コマンドによる明示的保存** 『本講座サンプル実装』

- `/clear` 前に handoff 実行 → 引き継ぎYAMLを生成
- 新セッションで `/rehydrate` → 引き継ぎから詳細復元
- 復旧成功率: **ファイル品質に依存** — 保存品質 = 復旧品質

> 公式hook (SessionStart/PreCompact) とカスタム実装 (handoff/rehydrate) の組み合わせが、完全なCompress戦略を実現する

<!--
本講座の制作環境での実装例を2つ紹介します。1つ目はPreCompact hookによる自動保存です。Compaction直前にタスクYAMLのステータスと進捗を更新し、設計判断をmemoryファイルに書き込みます。次セッションでSessionStartが即座に復旧します。2つ目はhandoffコマンドです。clearの前にhandoffを実行して引き継ぎYAMLを生成し、新セッションでrehydrateで復元します。重要な注意点として、復旧成功率は保存品質に依存します。ゴミを保存すればゴミが復元されます。公式hookとカスタム実装の組み合わせが完全なCompress戦略を実現します。
-->

---

# 復旧失敗の3パターンと対策

| パターン | 症状 | 原因 | 対策 |
|----------|------|------|------|
| **指示の欠落** | 役割やルールを忘れる | `instructions/*.md` の未読 | 読込リストの固定化 |
| **記憶の陳腐化** | 古いパスを参照 | memoryの未更新 | 定期検証cron |
| **YAML不整合** | 完了済みタスクが「未完了」に | statusの書き換え漏れ | 完了時の即時更新 |

**根本原因**: 復旧プロセスは **圧縮済み情報の品質に依存する**

> 圧縮段階でゴミを保存すれば、復元段階でゴミが復元される。Compress戦略の成否は「何を残すか」で決まる

<!--
復旧が失敗する典型的なパターンを3つ紹介します。1つ目は指示の欠落。instructionsが読み込まれずに役割やルールを忘れます。対策は読込リストの固定化です。2つ目は記憶の陳腐化。古いファイルパスを参照してしまいます。対策は定期検証のcron設定です。3つ目はYAML不整合。完了済みタスクが未完了として復元されます。対策は完了時の即時更新です。Compress戦略の根本的な注意点は、復旧が圧縮済み情報の品質に依存することです。圧縮段階で何を残すかの判断が、戦略全体の成否を決めます。
-->

---

# まとめ — Compress戦略の全体像

**この章で学んだこと**:

1. **Compress戦略** = 情報を圧縮して重要なものだけを残す LangChain の体系的手法
2. セッション断絶は **3パターン** (`/clear` / Compaction / 新規起動)
3. **SessionStart hook** が4段階で自動復旧 (公式機能)
4. **PreCompact hook** が圧縮前に重要情報を自動保存 (公式機能)
5. **handoff** がセッション状態を明示的に保存 (カスタム実装)
6. 復旧品質は **圧縮品質に依存** — 何を残すかの判断が鍵

```
Compress戦略の3フェーズ:
  圧縮 → PreCompact (自動) / handoff (手動)
  保存 → YAML / memory/*.md
  復元 → SessionStart (自動) / rehydrate (手動)
```

> 3フェーズで、セッション断絶を「無かったこと」にできる

<!--
まとめです。Compress戦略はLangChainが体系化した情報圧縮の手法で、セッション断絶を3フェーズで解決します。圧縮フェーズではPreCompact hookによる自動保存とhandoffによる手動保存を行います。保存先はYAMLファイルとmemoryディレクトリです。復元フェーズではSessionStart hookによる自動復旧とrehydrateによる手動復元を行います。重要なのは、復旧品質が圧縮品質に依存することです。何を残すかの判断が、Compress戦略全体の成否を決めます。次章ではIsolate戦略を学びます。
-->

---

# 確認問題

**Q1**: LangChainのCompress戦略の目的を、他の3戦略と対比して説明せよ。

**Q2**: SessionStart hook の4段階復旧フローを順番に説明せよ。

**Q3**: 「圧縮段階でゴミを保存すれば、復元段階でゴミが復元される」という言葉の意味と、その対策を述べよ。

**解答**:

**A1**: Compress戦略は「情報を圧縮して容量を節約する」戦略。Write(書き込み)やSelect(選択)とは異なり、すでに存在する情報を要約・圧縮して重要なものだけを残す点が特徴。Isolate(分離)が情報間の干渉防止なのに対し、Compressは情報量そのものの削減に焦点を当てる。

**A2**: (1) 自己識別: 環境変数から役割を確認。(2) 永続記憶読込: `memory/*.md`を読み込む。(3) 指示ファイル読込: `CLAUDE.md` / `instructions/*.md`を読み込む。(4) タスク状態復元: YAMLから未完了タスクを特定。

**A3**: 復旧プロセスは保存された情報の品質に依存する。古い・不正確な情報を圧縮保存していれば、復旧後もその状態が引き継がれる。対策は、memoryの定期検証、YAML statusの即時更新、読込リストの固定化。

<!--
確認問題です。Q1はCompress戦略の位置づけを問います。WriteやSelect、Isolateとの違いを理解していることが重要です。Q2はSessionStartの4段階復旧フローの理解を確認します。Q3は圧縮品質と復旧品質の関係についての深い理解を問います。3問とも正解できれば、Compress戦略の本質をしっかり理解できています。
-->

---

<!-- _class: cover -->

# 第7章 完了
## 次は 第8章「コンテキスト運用ベストプラクティス (Isolate戦略)」

<div class="meta">
✅ LangChain Compress戦略の理解<br>
✅ セッション断絶3パターンの分類<br>
✅ SessionStart hook による自動復旧<br>
✅ PreCompact hook による自動保存<br>
✅ handoff による明示的状態保存<br>
✅ 圧縮品質と復旧品質の関係<br><br>
<b>続けて第8章をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章ではLangChainのCompress戦略を、セッション再起動耐性の観点から解説しました。SessionStart hookによる自動復旧、PreCompact hookによる自動保存、handoffによる明示的保存。この3つの仕組みを組み合わせることで、セッション断絶を「無かったこと」にできます。次の第8章では、Isolate戦略としてコンテキストの運用ベストプラクティスを解説します。
-->
