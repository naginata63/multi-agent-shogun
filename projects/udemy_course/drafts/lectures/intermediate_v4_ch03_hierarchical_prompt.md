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

# 階層的プロンプト
## プロンプトを「3つの層」に整理する設計思想

<div class="meta">
中級編 — 第3章 (約 30 min)<br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネスエンジニアリング完全解説」<br>
<span style="font-size:0.9em">（※ハーネスエンジニアリング = AIを動かす枠組みの設計。後半の章で詳説）</span><br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
こんにちは。このレクチャーでは「階層的プロンプト」を解説します。初級編ではCLAUDE.mdの書き方を学びましたが、中級編では1つのファイルに全部詰め込むのではなく、複数のファイルに「役割分担」させる設計思想を理解していただきます。CLAUDE.md、instructions、task YAMLの3層がどう連携しているのか、なぜ分ける必要があるのかを30分でしっかり解説します。
-->

---

## この章で出てくる用語

> この章で初めて出てくる言葉を先にまとめておきます。安心して読み進めてください。

| 用語 | 意味 |
|------|------|
| **CLAUDE.md** | AI（Claude Code）に常時読ませる設定ファイル。プロジェクトの「憲法」のようなもの |
| **YAML** | 階層構造を持ったデータ形式。`.yaml` 拡張子のファイル。インデントで構造を表す |
| **queue** | 「順番待ち」の意。この講座では、タスクを順番に管理するフォルダ名として使います |
| **instructions** | 「指示書」の意。役割ごとのルールを書いたファイル群 |
| **tmux** | ターミナル画面を分割・管理するツール。複数のAIエージェントを同時に動かす時に使います |
| **agent_id** | 各AIエージェントに割り当てられた「名札」。tmuxで管理されます |

---

## この 30 分で得られること

1. **3層の分類基準** を「変更頻度 × 適用範囲」で説明できる
2. **CLAUDE.md / instructions / task YAML** の役割分担を設計できる
3. **肥大化したCLAUDE.mdをスリム化** する手順を理解する
4. **新セッションで正しく動作する仕組み** を説明できる

<!--
この章のゴールは4つです。中級編の第3章では、プロンプトを「階層」に分ける設計思想を深く理解します。1つのCLAUDE.mdに全部書くのではなく、3つの層に分けることで、保守性と再利用性が劇的に向上します。30分後に、あなたのプロジェクトのコンテキストを3層に整理できるようになりましょう。
-->

---

# 「全部入り」の罠 — Emotional Hook

> CLAUDE.md に全部書いていませんか？
> それは「引っ越し荷物を全部リビングに放り込む」状態です。

**起きること**:
- AIが **重要なルールを見落とす** (AIが一度に読める量には上限があるため、長いと後ろの行を読み飛ばす)
- **エージェント別のルール** が混在して矛盾
- **タスク固有の指示** が消えていく (古いタスクの指示が残る)

> 解決策: 荷物を「3つの部屋」に整理する

<!--
CLAUDE.mdにプロジェクトのルール、エージェントの行動指針、タスクの指示、すべてを書いていませんか？ それは引っ越しした荷物を全部リビングに放り込むような状態です。何がどこにあるか分からなくなり、重要なものが埋もれてしまいます。この章では、荷物を3つの部屋に整理する方法を学びます。CLAUDE.md、instructions、task YAMLの3層に分けることで、AIが確実に必要な情報にアクセスできるようになります。
-->

---

# 3層分類の基準 — 変更頻度 × 適用範囲

| | 低い変更頻度 | 高い変更頻度 |
|------|:-----------:|:-----------:|
| **広い適用範囲** | CLAUDE.md | — |
| **狭い適用範囲** | instructions | task YAML |

**読解のポイント**:
- **CLAUDE.md** — 全セッションで不変の「憲法」
- **instructions** — 役割ごとに固定の「業務マニュアル」
- **task YAML** — タスクごとに変わる「個別の指示書」
- 右上の「—」= 広い範囲かつ高頻度に変わるルールは、**プロジェクトの基盤が不安定**というサイン。実務ではほぼ存在しません

> 変わるものと変わらないものを分ける — これが階層設計の本質

<!--
3層を分類する基準は「変更頻度」と「適用範囲」の2軸です。CLAUDE.mdは全セッションに適用され、かつめったに変更されない「憲法」のような位置づけ。instructionsは特定の役割に適用され、やはり変更頻度は低い「業務マニュアル」。task YAMLはタスクごとに内容が変わり、適用範囲もそのタスクだけ。変わるものと変わらないものを分けることが、階層設計の本質です。
-->

---

# 3層の全体像 — ファイル配置と読込タイミング

| 層 | ファイル | 読込タイミング | 役割 |
|----|---------|--------------|------|
| **Layer 1** | `CLAUDE.md` | セッション開始時 | 全体方針・禁止事項 |
| **Layer 2** | `instructions/*.md` | セッション開始時 | 役割別の詳細ルール |
| **Layer 3** | `queue/tasks/*.yaml` | タスク割り当て時 | 個別タスクの指示書 |

**特徴**:
- 上位の層ほど **適用範囲が広い**
- 下位の層ほど **具体性が高い**
- 各層は **独立して更新可能**

<!--
3層の全体像を整理します。Layer 1のCLAUDE.mdはセッション開始時に自動読込される全体方針。Layer 2のinstructionsは役割ごとの詳細ルールで、同じくセッション開始時に読まれます。Layer 3のtask YAMLは、タスクが割り当てられた時に初めて読み込まれる個別の指示書です。上位ほど広い範囲、下位ほど具体的。そして各層は独立して更新できるので、タスクを変えるたびにCLAUDE.mdを書き換える必要がありません。
-->

---

# CLAUDE.mdの役割 — 30行の「憲法」

**CLAUDE.mdに書くべきもの**:
- プロジェクトの **全体方針**
- **禁止事項** (絶対にやってはいけないこと)
- **技術スタック** の宣言
- **共通手順** (セッション開始・終了時の処理)

**CLAUDE.mdに書くべきでないもの**:
- 役割別の詳細ルール → instructions へ
- 個別タスクの指示 → task YAML へ
- 一時的な設定 → task YAML の params へ

> CLAUDE.mdは「何を守るか」を宣言する場所。具体的な手順は下位層へ。
> 「30行」の理由: AIは30行程度までなら確実に全行を読む。それ以上になると、後ろの行を読み飛ばす確率が上がるから。

<!--
CLAUDE.mdの役割を再定義します。CLAUDE.mdに書くべきは、全体方針、禁止事項、技術スタック、共通手順です。これは「憲法」に相当し、めったに変わらないルールです。逆に、役割別の詳細ルールはinstructionsに、個別タスクの指示はtask YAMLに書きます。CLAUDE.mdを30行以内に保つことで、AIが確実に全体方針を理解し、遵守するようになります。
-->

---

# instructions/*.md の役割 — 役割別の業務マニュアル

**1つの役割 = 1つのファイル**:

| ファイル | 役割 | 内容例 |
|---------|------|--------|
| `orchestrator.md` | オーケストレータ | コマンド発行ルール・ダッシュボード方針 |
| `manager.md` | タスクマネージャ | タスク配分・QC判定基準 |
| `executor.md` | 実行担当 | 実装手順・報告フォーマット |
| `reviewer.md` | 品質検査 | QC手順・検査項目 |

**メリット**:
- 役割ごとに **独立して更新** できる
- 不要なルールが **AIのコンテキスト（一度に覚えられる情報の量）を圧迫しない**
- 新しい役割の追加が **1ファイルで済む**

<!--
instructionsディレクトリには、役割ごとに1つのmdファイルを配置します。オーケストレータのorchestrator.md、タスクマネージャのmanager.md、実行担当のexecutor.md、品質検査のreviewer.md。このように役割ごとに分けることで、各エージェントは自分のルールだけを読み込みます。不要なルールがコンテキストを圧迫せず、新しい役割の追加も1ファイル作るだけで済みます。初級編ではCLAUDE.mdだけで十分でしたが、中級編ではこの役割別ファイルの設計が重要になります。
-->

---

# task YAML の役割 — 個別の指示書

**1つのタスク = 1つのYAMLファイル**:

```yaml
task_id: subtask_155b
status: assigned
description: "ログインAPIのバグ修正"
target_path: src/auth/login.py
steps: |
  1) バグの原因を特定
  2) 修正を実装
  3) テストを追加
acceptance_criteria:
  - ログインが成功すること
  - テストが全て通ること
```

**特徴**:
- **タスクごとに作成・完了後に参照しない**
- **ステータス管理** ができる (assigned / in_progress / done)
- **acceptance_criteria** で完了条件を明示

<!--
task YAMLは個別のタスクの指示書です。1つのタスクにつき1つのYAMLファイルを作成します。タスクID、ステータス、説明、対象パス、手順、完了条件を構造化して記述します。タスクごとに作成され、完了後は基本的に参照されません。ステータス管理ができるので、どのタスクが進行中か一目で分かります。またacceptance_criteriaで完了条件を明示することで、「完了したつもり」を防ぎます。
-->

---

# スリム化の実例 — Before (100行のCLAUDE.md)

> **トラブル事例**: ある日、AIが「CLAUDE.mdの19行目に『テストは必須』とあるのでテストを実行しました」と報告。しかし、そのルールは別の担当者向けで、今のタスクには不要だった。原因は、100行のCLAUDE.mdに全部入りだったこと。

```
# 全体方針
Python 3.12 / FastAPI ...
コーディング規約 ...
テストコマンド ...

# executor1のルール (← 役割別ルールが混入)
実装時は必ずテストを実行 ...
報告はYAML形式で ...

# executor2のルール (← 別役割のルールも混入)
デザイン確認はスクショ必須 ...
Figmaのリンクを参照 ...

# 今日のタスク (← 個別タスクの指示が混入)
ログインAPIのバグ修正 ...
優先度: 高 ...
```

**問題点**:
- 100行のうち **今のタスクに関係ない部分が大半**
- 役割別ルールと全体ルールが **混在**
- タスク指示が **古いまま残る** 可能性

<!--
Beforeの例です。CLAUDE.mdに全体方針だけでなく、executor1のルール、executor2のルール、今日のタスクまで全部書いてあります。100行のうち、今のタスクに関係あるのは一部だけ。残りはノイズです。役割別のルールと全体ルールが混在しているので、AIがどれを守るべきか迷います。また、タスク指示が完了後も残り続け、古い情報が混ざる原因になります。
-->

---

# スリム化の実例 — After (30行 + 2ファイル)

**CLAUDE.md (30行)**:
```
# 全体方針
Python 3.12 / FastAPI
コーディング規約 ...
禁止事項 ...
```

**instructions/executor.md (役割別)**:
```
実装時は必ずテストを実行
報告はYAML形式で ...
```

**tasks/executor1.yaml (タスク別)**:
```yaml
description: "ログインAPIのバグ修正"
target_path: src/auth/login.py
```

**結果**: 各ファイルが **役割ごとに独立**。AIは必要なものだけを読む。

<!--
Afterの例です。CLAUDE.mdは30行にスリム化され、全体方針だけが残りました。役割別のルールはinstructions/executor.mdに移動し、タスクの指示はtasks/executor1.yamlに移動しました。各ファイルが独立しているので、AIは自分に必要なものだけを読み込みます。結果として、コンテキストの消費を大幅に削減しつつ、必要な情報に確実にアクセスできるようになります。
-->

---

# 正しく動作する仕組み — セッション開始からタスク完了まで

**Step 1: セッション開始**
- CLAUDE.md を自動読込 → 全体方針を理解
- 自分の instructions を読込 → 役割を理解

**Step 2: タスク受領**
- task YAML を読込 → 個別指示を理解

**Step 3: 実行中**
- CLAUDE.md: 「禁止事項」に抵触したら **即座に停止**
- instructions: 「報告フォーマット」に従って出力
- task YAML: 「acceptance_criteria」を確認しながら作業

**Step 4: 完了**
- 3層すべてのルールを満たしたか **自己検証**

<!--
3層が実際にどう連携するかを、セッション開始からタスク完了まで追ってみます。セッション開始時にCLAUDE.mdと自分のinstructionsが読み込まれ、全体方針と役割を理解します。タスクが割り当てられるとtask YAMLを読み込み、個別指示を理解します。実行中は、CLAUDE.mdで禁止事項に触れたら即座に停止し、instructionsの報告フォーマットに従って出力し、task YAMLの完了条件を確認しながら作業します。3層が連携することで、安全で品質の高い作業が実現します。
-->

---

# エージェントに名前をつける — CLAUDE.md と instructions 設定

> 📌 **発展内容** — まずは基本の3層設計（CLAUDE.md / instructions / task YAML）をマスターしてから読み返してください。

**Claude Code CLI でのエージェント設定方法**:

1. **CLAUDE.md に Session Start 手順を書く**:
   ```
   ## Session Start
   1. tmux display-message → 自分の agent_id を確認
   2. Read instructions/{自分の役割}.md
   3. Read queue/tasks/{自分のID}.yaml
   ```
   → エージェント起動時に **自分が誰か** を自己識別

2. **instructions/*.md で役割を定義**:
   - `orchestrator.md` / `manager.md` / `executor.md` / `reviewer.md`
   - 各ファイルに **役割・禁止事項・報告フォーマット** を記述

3. **命名は自由 — CLI標準機能のみ使用**:
   - `advisor()` は Claude Code 標準の品質チェック機能（出力を第三者視点でレビューしてくれる）
   - 役割名は `.md` ファイル名で決まる
   - 外部プラグイン不要

> 設定ファイルを書くだけで、CLIが自動的にエージェントを読み分ける

<!--
このスライドでは、エージェントに名前をつけて設定する方法を解説します。重要なのは、特別なツールは不要でClaude Code CLIの標準機能だけで実現できることです。まずCLAUDE.mdにセッション開始時の手順を書きます。エージェントが起動したら自分のIDを確認し、対応するinstructionsを読み込みます。これで自己識別ができます。instructionsディレクトリには各役割のファイルを置きます。orchestrator.md、manager.md、executor.md、reviewer.mdなど、名前は自由につけられます。各ファイルに役割、禁止事項、報告フォーマットを書けば、CLIが起動時に自動的に適切なファイルを読み分けます。
-->

---

# まとめ — 階層的プロンプトの設計思想

1. **3層の分類基準** = 変更頻度 × 適用範囲
2. **CLAUDE.md** = 30行の「憲法」(全体方針・禁止事項)
3. **instructions** = 役割別の「業務マニュアル」
4. **task YAML** = タスクごとの「個別指示書」
5. 分けることで **保守性・再利用性・安全性** が向上

> 「全部入り」は1つのファイルを壊す。
> 「3層分け」は3つのファイルを健全に保つ。

<!--
この章のまとめです。階層的プロンプトの本質は「変わるものと変わらないものを分ける」こと。変更頻度と適用範囲の2軸で分類し、CLAUDE.md、instructions、task YAMLの3層に整理します。全部入りは1つのファイルを肥大化させ、やがて壊れます。3層分けは各ファイルを健全に保ちます。次の章では、この3層の品質を保証する仕組みを解説します。
-->

---

# 確認問題

**Q1**: CLAUDE.mdに「executorの実装ルール」を書くべきでない理由は何か？

<details><summary>回答</summary>役割別のルールは変更頻度・適用範囲が異なるため。CLAUDE.mdは「全セッション共通・不変」の全体方針に留め、役割別ルールはinstructions/*.mdに分離すべき。</details>

---

**Q2**: 3層を分類する2つの軸を挙げよ。

<details><summary>回答</summary>「変更頻度」と「適用範囲」の2軸。CLAUDE.mdは低頻度・広範囲、instructionsは低頻度・狭範囲、task YAMLは高頻度・狭範囲に位置する。</details>

**Q3**: task YAMLのacceptance_criteriaはなぜ重要か？

<details><summary>回答</summary>完了条件を明示することで「完了したつもり」を防ぐため。AIはacceptance_criteriaを自己検証の基準として使い、全条件を満たした場合のみ完了報告を行う。</details>

<!--
確認問題です。動画を一時停止して、自分で答えを考えてから解答を開いてみてください。Q1は3層分けの本質を問う問題です。Q2は分類基準の2軸を覚えているかの確認。Q3はtask YAMLの実践的な価値を理解しているかを問う問題です。3問とも正解できれば、この章の内容はしっかり身についています。
-->

---

<!-- _class: cover -->

# 第3章 完了

## 次は 第4章「プロンプト品質 Gate: advisor() と QC template」

<div class="meta">
✅ 3層分類基準（変更頻度×適用範囲）の理解<br>
✅ CLAUDE.md / instructions / task YAML の役割分担<br>
✅ 肥大化CLAUDE.mdのスリム化手順<br>
✅ 3層連携の動作メカニズムの理解<br><br>
<b>続けて 第4章 をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章では、CLAUDE.mdに全部詰め込む「全部入り」の罠と、3層に分ける「階層的プロンプト」の設計思想を解説しました。CLAUDE.mdは30行の憲法、instructionsは役割別の業務マニュアル、task YAMLは個別の指示書。この3層に分けることで、保守性も再利用性も安全性も向上します。次の第4章では、この3層の品質を保証する仕組み、advisorとQC templateを解説します。
-->
