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

# セッション再起動耐性
## SessionStart / PreCompact / rehydrate — AIに「おかえりなさい」と言わせる仕組み

<div class="meta">
中級編 v4 — 第7章 (約 40 min)<br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第7章へようこそ。テーマは「セッション再起動耐性」です。昨日の作業を今日再開したら、AIが「初めまして」と言ってきた。この絶望感を味わったことがありますか。この章では、AIに「おかえりなさい」と言わせる仕組みを解説します。SessionStart hook、PreCompact hook、そしてrehydrateコマンドの3つの仕組みを理解し、セッションが断絶しても完全に復旧できるようになります。Bloom分類のL5 EvaluateとL6 Createにまたがる内容で、40分かけてしっかり学んでいきましょう。
-->

---

## この章で学ぶこと [L2: Evaluate + Create]

1. セッション断絶の **3パターン** を説明できる
2. **SessionStart hook** の4段階復旧フローを理解する
3. **PreCompact hook** で保存すべき情報を特定できる
4. **rehydrate** による引き継ぎファイル復元の仕組みを理解する
5. 復旧失敗の **典型パターンと対策** を説明できる

> この章のゴール: セッション断絶しても「元の状態に戻る」仕組みを設計できる

<!--
この章では5つの到達点を目指します。まずセッションが切れる3つのパターンを理解します。次にSessionStart hookによる4段階の復旧フローを学びます。PreCompact hookで圧縮前に何を保存すべきかを特定し、rehydrateコマンドによる引き継ぎ復元の仕組みを理解します。最後に、復旧が失敗する典型的なパターンとその対策を学びます。この章を終えると、セッションが切れても元の状態に確実に戻る仕組みを設計できるようになります。
-->

---

# 「AIが初めまして」と言ってきた絶望感 — Emotional Hook

> 昨日の作業を今日再開したら、AIが**何も覚えていない**。
> 「さっきまで一緒に作業していたのに」— この感覚、ありませんか？

**失われるもの**:
- 「どのファイルを編集中だったか」
- 「何をテストして、何が残っているか」
- 「なぜその設計判断をしたか」

**原因**: セッションの断絶。AIの記憶は **1セッション限り** なのがデフォルト。

> この章では、断絶しても**完全に復旧する**仕組みを解説します。

<!--
まずつかみです。昨日の作業を今日再開したら、AIが何も覚えていない。さっきまで一緒に作業していたのに。失われるのは、どのファイルを編集中だったか、何をテストして何が残っているか、なぜその設計判断をしたか。これらが全部消えます。原因はセッションの断絶です。AIの記憶はデフォルトでは1セッション限りです。でも大丈夫。この章では、断絶しても完全に復旧する仕組みを3つ解説します。SessionStart、PreCompact、rehydrateの3本柱です。
-->

---

# セッション断絶の3パターン

| パターン | トリガー | 失われるもの | 復旧の必要性 |
|----------|----------|-------------|-------------|
| **`/clear`** | ユーザーが明示的にセッションをリセット | セッション内の会話履歴全て | 高 — 作業途中なら致命的 |
| **Compaction** | コンテキスト上限到達で自動圧縮 | 古い会話の詳細（要約は残る） | 中 — 要約から再開可能 |
| **新規起動** | CLIを閉じて再度開く | セッション全体 | 高 — 毎日起こり得る |

**共通点**: どれも**コンテキストの一部または全部が消える**。

<!--
セッションが断絶するパターンは3つあります。1つ目はスラッシュclear。ユーザーが明示的にセッションをリセットするコマンドで、セッション内の会話履歴が全て消えます。作業途中なら致命的です。2つ目はCompaction。コンテキストウィンドウの上限に達すると、古い会話が自動的に圧縮されます。要約は残るものの、詳細は失われます。3つ目は新規起動。CLIを閉じて再度開くと、前のセッションは完全に消えています。毎日の開発で日常的に起こり得る状況です。共通点は、どれもコンテキストの一部または全部が消えることです。
-->

---

# 断絶で失われる情報 — 4カテゴリ

| カテゴリ | 内容 | 復旧手段 |
|----------|------|----------|
| **プロジェクト指示** | CLAUDE.md / instructions/*.md | 自動読込 (SessionStart) |
| **永続記憶** | memory/*.md / MCP memory | 自動読込 (SessionStart) |
| **タスク状態** | 進行中の作業・未完了項目 | YAMLファイル (SessionStart) |
| **会話コンテキスト** | 直近の判断・方針 | rehydrate / PreCompact |

**重要な違い**:
- 上位3行 = **ファイルに保存されていれば自動復旧可能**
- 下位1行 = **明示的な保存が必要** — これがPreCompactとrehydrateの役割

<!--
断絶で失われる情報を4つのカテゴリに分類します。プロジェクト指示はCLAUDE.mdやinstructionsディレクトリのファイル。永続記憶はmemoryディレクトリやMCP memory。タスク状態は進行中の作業や未完了項目。そして会話コンテキストは直近の判断や方針です。重要な違いは、上位3つはファイルに保存されていれば新セッションで自動的に読み込まれること。一方、会話コンテキストは明示的に保存しないと失われます。この保存を担うのがPreCompact hookとrehydrateコマンドです。
-->

---

# SessionStart hook — 4段階復旧フロー

> 新しいセッションが始まると同時に、自動的に状態を復元する仕組み

**4段階のフロー**:

1. **自己識別** — 自分がどの役割で動いているかを確認
2. **永続記憶の読込** — memory/*.md や MCP memory を読み込む
3. **指示ファイルの読込** — CLAUDE.md / instructions/*.md を読み込む
4. **タスク状態の復元** — YAMLファイルから未完了タスクを特定

> この4段階が自動で走ることで、新セッションでも「昨日の続き」が始まる

<!--
SessionStart hookの仕組みを解説します。これはClaude Codeのセッション開始時に自動的に実行される処理です。4段階のフローがあります。まず自己識別。自分がどの役割で動いているかをtmuxなどの環境変数から確認します。次に永続記憶の読込。memoryディレクトリやMCP memoryを読み込みます。3番目に指示ファイルの読込。CLAUDE.mdとinstructionsディレクトリのファイルを読み込みます。最後にタスク状態の復元。YAMLファイルから未完了のタスクを特定します。この4段階が自動で走ることで、新しいセッションでも昨日の続きから始められます。
-->

---

# SessionStart の設定 — settings.json

`settings.json` で SessionStart hook を登録:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "bash scripts/session_start.sh"
      }
    ]
  }
}
```

**`session_start.sh` の役割**:
- 自分の役割を環境変数から特定
- memory / instructions / task YAML を順次読込
- 読込結果をコンテキストに注入

> hook = 「セッション開始時に自動実行されるスクリプト」— L3ハーネスの入口

<!--
具体的な設定方法です。settings.jsonのhooksセクションにSessionStartを登録します。commandタイプでbashスクリプトを指定します。このsession_start.shが、先ほどの4段階の復旧フローを実行します。自分の役割を環境変数から特定し、memory、instructions、task YAMLを順次読み込み、結果をコンテキストに注入します。このhookが、L3ハーネスの入口にあたります。AIの動作を自動制御する仕組みの1つ目がこのSessionStart hookです。
-->

---

# PreCompact hook — 圧縮前に何を保存するか

> Compactionが走る直前に、**失われては困る情報**を自動保存する仕組み

**保存すべき情報**:

| 情報 | 理由 | 保存先 |
|------|------|--------|
| 進行中のタスク | 復旧後に再開するため | task YAML |
| 未コミットの変更 | 変更内容を忘れるため | task YAML |
| 重要な設計判断 | 「なぜそう決めたか」を残す | memory/*.md |
| コンテキスト使用率 | 次セッションの予算計画 | レポート |

**PreCompact hook の設定**:
```json
{
  "hooks": {
    "PreCompact": [
      {
        "type": "command",
        "command": "bash scripts/pre_compact.sh"
      }
    ]
  }
}
```

<!--
PreCompact hookの仕組みです。Compactionが走る直前に、失われては困る情報を自動保存します。保存すべき情報は4つ。進行中のタスクは復旧後に再開するためにtask YAMLに保存。未コミットの変更は変更内容を忘れないために同じくtask YAMLに。重要な設計判断は「なぜそう決めたか」を残すためにmemoryディレクトリに。コンテキスト使用率は次セッションの予算計画のためにレポートに保存します。SessionStartと同様にsettings.jsonで登録します。この2つのhookを組み合わせることで、断絶前の保存と断絶後の復旧を自動化できます。
-->

---

# rehydrate — 引き継ぎファイルからの状態復元

> 「セッションを引き継ぐ」という明示的なコマンド

**rehydrate の仕組み**:
1. 引き継ぎファイル (handoff YAML) を読み込む
2. 進行中タスク・完了タスク・未解決課題を復元
3. コンテキストに注入して「続き」のセッションを開始

**いつ使うか**:
- Compaction後に「続きから再開したい」時
- `/clear` 後に「昨日の状態に戻りたい」時
- セッションをまたぐ大規模タスクの継続

**引き継ぎファイルに含まれる情報**:
- タスクID・ステータス・進捗
- 残作業リスト
- 注意点・方針

<!--
3つ目の仕組みがrehydrateです。引き継ぎファイルから状態を復元する明示的なコマンドです。仕組みはシンプルで、引き継ぎファイルのhandoff YAMLを読み込み、進行中タスク、完了タスク、未解決課題を復元し、コンテキストに注入します。いつ使うかというと、Compaction後に続きから再開したい時、clear後に昨日の状態に戻りたい時、セッションをまたぐ大規模なタスクを継続する時です。引き継ぎファイルにはタスクID、ステータス、進捗、残作業リスト、注意点や方針が含まれます。SessionStartとPreCompactが自動的な仕組みなのに対し、rehydrateはユーザーが意図的に使う手動の仕組みです。
-->

---

# /clear → 完全復旧の全体フロー

**復旧プロセス (自動)**:

1. `/clear` 実行 → セッションがリセットされる
2. **SessionStart hook 発動** → 4段階復旧が自動実行
3. memory / instructions / task YAML が読み込まれる
4. 未完了タスクが特定され、作業が再開される

**復旧プロセス (手動)**:

5. `/rehydrate` 実行 → 引き継ぎファイルから詳細復元
6. 進捗・残作業・方針がコンテキストに注入される
7. 「昨日の続き」が完全に再開される

> **自動 + 手動** の組み合わせで、セッション断絶を「無かったこと」にできる

<!--
/clearから完全復旧までの全体フローを解説します。まずユーザーがclearを実行するとセッションがリセットされます。するとSessionStart hookが発動し、4段階の復旧が自動実行されます。memory、instructions、task YAMLが読み込まれ、未完了タスクが特定されます。ここまでは自動です。さらに手動でrehydrateコマンドを実行すると、引き継ぎファイルから詳細が復元されます。進捗、残作業、方針がコンテキストに注入され、昨日の続きが完全に再開されます。自動のSessionStartと手動のrehydrateを組み合わせることで、セッション断絶を無かったことにできます。
-->

---

# 復旧失敗の3パターンと対策

| パターン | 症状 | 原因 | 対策 |
|----------|------|------|------|
| **指示の欠落** | 役割やルールを忘れる | instructions/*.md の未読 | 読込リストの硬直化 |
| **記憶の陳腐化** | 古いファイルパスを参照 | memoryの未更新 | 定期検証cron |
| **YAML不整合** | 完了済みタスクが「未完了」に | statusの書き換え漏レ | 完了時の即時更新 |

**根本原因**: 復旧プロセスは **保存された情報の品質に依存する**

> ゴミを保存すればゴミが復元される — 保存品質の管理こそが真の課題

<!--
復旧が失敗する典型的なパターンを3つ紹介します。1つ目は指示の欠落。役割やルールを忘れる症状で、原因はinstructionsディレクトリのファイルが読み込まれていないこと。対策は読込リストを固定化することです。2つ目は記憶の陳腐化。古いファイルパスを参照する症状で、原因はmemoryファイルの未更新。対策は定期検証のcronを設定することです。3つ目はYAML不整合。完了済みタスクが未完了として復元される症状で、原因はstatusの書き換え漏れ。対策はタスク完了時に即座にstatusを更新することです。根本原因は、復旧プロセスが保存された情報の品質に依存していることです。ゴミを保存すればゴミが復元されます。保存品質の管理こそが真の課題です。
-->

---

# まとめ — セッション再起動耐性の復習

**この章で学んだこと**:

1. セッション断絶は **3パターン** (`/clear` / compaction / 新規起動)
2. **SessionStart hook** が4段階で自動復旧する
3. **PreCompact hook** が圧縮前に重要情報を自動保存する
4. **rehydrate** が引き継ぎファイルから詳細復元する
5. 復旧品質は **保存品質に依存** — 継続的な管理が不可欠

```
自動: SessionStart (復旧) + PreCompact (保存)
手動: rehydrate (詳細復元)
組み合わせ → セッション断絶を「無かったこと」に
```

> 3つの仕組みを組み合わせれば、「AIが初めまして」という絶望感とはおさらば

<!--
まとめです。この章では5つのことを学びました。セッション断絶は3パターンあること。SessionStart hookが4段階で自動復旧すること。PreCompact hookが圧縮前に重要情報を自動保存すること。rehydrateが引き継ぎファイルから詳細復元すること。そして復旧品質は保存品質に依存すること。自動のSessionStartとPreCompact、手動のrehydrateを組み合わせることで、セッション断絶を無かったことにできます。「AIが初めまして」という絶望感とはおさらばです。この3つの仕組みがL2コンテキスト層の重要な要素です。
-->

---

# 確認問題

**Q1**: セッション断絶の3パターンを挙げ、それぞれの特徴を説明せよ。

**Q2**: SessionStart hook の4段階復旧フローを、順番に説明せよ。

**Q3**: 「ゴミを保存すればゴミが復元される」という言葉の意味と、その対策を述べよ。

**解答**:

**A1**: (1) `/clear` — ユーザーの明示的リセットで会話履歴全消失。(2) Compaction — コンテキスト上限到達で自動圧縮、古い会話の詳細消失。(3) 新規起動 — CLI終了でセッション全体消失。いずれもコンテキストの一部または全部が消える。

**A2**: (1) 自己識別: 環境変数から自分の役割を確認。(2) 永続記憶読込: memory/*.mdを読み込む。(3) 指示ファイル読込: CLAUDE.md / instructions/*.mdを読み込む。(4) タスク状態復元: YAMLファイルから未完了タスクを特定。

**A3**: 復旧プロセスは保存された情報の品質に依存するため、古い・不正確な情報を保存していれば、復旧後もその状態が引き継がれる。対策は、memoryの定期検証、YAML statusの即時更新、読込リストの固定化。

<!--
確認問題です。動画を一時停止して自分で答えを考えてから解答を開いてください。Q1はセッション断絶の3パターンを問う問題です。Q2はSessionStartの4段階復旧フローの理解を確認する問題。Q3は保存品質と復旧品質の関係についての理解を問う問題です。3問とも正解できれば、この章の内容はしっかり身についています。
-->

---

<!-- _class: cover -->

# 第7章 完了
## 次は 第8章「コンテキスト運用ベストプラクティス」

<div class="meta">
✅ セッション断絶の3パターンの理解<br>
✅ SessionStart hook による自動復旧<br>
✅ PreCompact hook による自動保存<br>
✅ rehydrate による引き継ぎ復元<br>
✅ 復旧失敗の対策と保存品質管理<br><br>
<b>続けて第8章をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章では、セッションが断絶しても完全に復旧する3つの仕組みを学びました。SessionStart hookによる自動復旧、PreCompact hookによる自動保存、rehydrateによる引き継ぎ復元。これらを組み合わせることで、AIとの作業を途切れさせることなく継続できます。次の第8章では、コンテキストを日々の開発でどう運用するかのベストプラクティスを学びます。それでは続けてご覧ください。
-->
