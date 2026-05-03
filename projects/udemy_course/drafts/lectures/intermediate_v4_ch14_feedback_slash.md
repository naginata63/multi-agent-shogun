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

# PostToolUse Supervisor
## フィードバック自動化パターン

<div class="meta">
中級編 v4 — 第14章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第14章へようこそ。この章ではPostToolUse Supervisorパターンを解説します。AIのツール実行後に自動でフィードバックを収集し、構造化された学習データに変換する仕組みです。ステークホルダーの感情を客観的な改善データに変える方法を学びます。なぎなたと申します。
-->

---

## この章で学ぶこと [L3: Evaluate + Create]

1. **Supervisor Pattern** の概念を説明できる
2. **PostToolUse hook** によるフィードバック自動化を設計できる
3. **カスタムslash command** の作成方法を習得する
4. **感情→構造化変換パイプライン** の仕組みを理解する
5. **チーム運用** の方法を設計できる

<!--
この章では5つの到達点を目指します。Supervisor Patternの概念、PostToolUse hookによるフィードバック自動化の設計、カスタムslash commandの作成、感情から構造化データへの変換パイプライン、チーム運用の設計方法を学びます。
-->

---

# ステークホルダーの不満 = 最高の品質改善データ

> 「なんでこんな簡単なこともできないんだ！」
> — この発言の中に **3つの改善ヒント** が埋まっています。

- **何が期待されていたか** = 品質基準の再定義
- **何が期待を裏切ったか** = 改善ポイントの特定
- **どうすべきだったか** = 具体的な修正方向

> ほとんどの場合、この情報は口頭で消え、再発防止に活かされません

<!--
このスライドがつかみです。ステークホルダーの怒りや不満の裏には、品質改善のヒントが隠れています。しかし残念なことに、ほとんどの場合この情報は口頭で消えてしまい、二度と活用されません。この章では、消えてしまう情報を自動的に永続化する仕組みを解説します。
-->

---

# Supervisor Pattern — ツール実行後の監督者

**Supervisor Pattern** = AIのツール実行結果を監視し、必要に応じて介入するパターン

- **PostToolUse hook** で実現: ツール実行後に自動で監視処理を実行
- **介入の3レベル**:
  - **Log**: 結果を記録するだけ（低コスト）
  - **Validate**: 結果が基準を満たすか検証（中コスト）
  - **Block**: 基準違反の場合に実行を取り消し（高コスト）

| レベル | 用途 | 例 |
|-------|------|-----|
| Log | フィードバック蓄積 | ユーザーの反応を記録 |
| Validate | 品質確認 | 出力フォーマットの検証 |
| Block | 安全確保 | 危険な出力の阻止 |

<!--
Supervisor Patternの概念です。PostToolUse hookを使ってAIのツール実行結果を監視します。介入は3つのレベルに分かれます。Logは結果を記録するだけ、Validateは基準を満たすか検証、Blockは基準違反の場合に実行を取り消します。フィードバック自動化では主にLogレベルを使います。
-->

---

# フィードバック変換パイプライン

**4段階のパイプライン**で感情を構造化データに変換:

| 段階 | 入力 | 出力 |
|------|------|------|
| **Capture** | ステークホルダーの生の発言 | テキスト |
| **Analyze** | 感情・文脈・改善ヒントの抽出 | 構造化データ |
| **Draft** | フィードバック文書の自動作成 | .mdファイル |
| **Review** | 人間による承認・修正・破棄 | 最終版 |

- **なぜ自動化するか**: 手動では感情が先立ち、客観的な記録が困難
- **なぜAIにやらせるか**: 感情を除去し、事実ベースの構造化が得意

<!--
フィードバック変換パイプラインの全体像です。Capture、Analyze、Draft、Reviewの4段階で構成されます。Captureで生の発言を受け取り、Analyzeで感情と改善ヒントを抽出し、Draftで文書を自動生成し、Reviewで人間が判定します。AIは感情を除去して事実ベースの構造化が得意なので、この変換に適しています。
-->

---

# Stage 1-2: Capture → Analyze

### Capture: 発言の受け取り
```
/feedback-capture
「またテスト落ちてるじゃないか！マージ前に確認しろって
何度も言ったのに！」
```

### Analyze: AIによる分析
- **感情ラベル**: 怒り (強)
- **本質**: マージ前のテスト実行が漏れている
- **改善ヒント**: PostToolUse hook でテスト実行を強制
- **影響度**: 高 — リリース品質に直結

<!--
CaptureとAnalyzeの詳細です。Captureではステークホルダーの発言をそのまま入力します。カギカッコや感嘆符が含まれていてもそのまま渡します。AnalyzeでAIが分析します。感情のラベリング、本質の抽出、改善ヒントの提案、影響度の評価を自動で行います。この例では、怒りの背後にある本質はマージ前のテスト実行漏れです。
-->

---

# Stage 3-4: Draft → Review

### Draft: 構造化フィードバックの自動生成

> `feedback_merge_testing.md`
> - **What**: マージ前のテスト実行が漏れていた
> - **Impact**: マージ後にテストが失敗し、リリースが遅延
> - **Fix**: PostToolUse hookでマージ前テストを強制
> - **Prevention**: CIパイプラインにテスト必須チェックを追加

### Review: 人間による判定

| アクション | 意味 | 次のステップ |
|-----------|------|-------------|
| **y** (承認) | 内容で確定 | `memory/` に保存 |
| **e** (修正) | 調整したい | AIに修正指示 → 再生成 |
| **n** (破棄) | 不要 | 破棄して終了 |

<!--
DraftとReviewの詳細です。DraftではWhat、Impact、Fix、Preventionの4要素で構造化されたフィードバックを自動生成します。Reviewでは人間がy、e、nの3つのアクションから選択します。すべてのフィードバックを保存する必要はなく、取捨選択を人間が行うことが品質の鍵です。
-->

---

# カスタム Slash Command の作成

Claude Codeのslash command = `.claude/commands/` に置いた `.md` ファイル

```
.claude/
  commands/
    feedback-capture.md    ← /feedback-capture で呼び出せる
```

**ファイルの中身** = プロンプトテンプレート:
```markdown
# Feedback Capture

以下のステークホルダー発言を分析し、
構造化フィードバックの草案を作成せよ。

発言内容: $ARGUMENTS
```

- `$ARGUMENTS` = コマンド後に続くテキストが自動挿入
- ファイル名 = コマンド名
- 複数階層も可能: `commands/team/feedback.md` → `/team feedback`

<!--
カスタムslash commandの作成方法です。.claude/commands/ディレクトリに.mdファイルを置くだけでslash commandとして認識されます。$ARGUMENTSという変数にコマンド後のテキストが自動挿入されます。ファイル名がコマンド名になり、複数階層のディレクトリ構造もサポートされています。
-->

---

# 変換実例: コード品質への不満

**入力**:
> 「この関数、引数の型すら書いてない。プロとしてどうなの？」

**AI分析結果**:
- **感情**: 呆れ (中)
- **本質**: 型アノテーションの欠如
- **改善**: 型ヒント追加のルール化

**生成されたフィードバック**:
> `feedback_type_annotations.md`
> - **What**: 型アノテーションが欠如していた
> - **Impact**: コードの可読性と保守性が低下
> - **Fix**: 全関数に型ヒントを追加するルールを設定
> - **Prevention**: `ruff` や `mypy` による自動チェック

<!--
変換の実例です。コード品質に対する不満を入力すると、AIは呆れの感情を検出し、本質が型アノテーションの欠如であることを抽出します。生成されるフィードバックはWhat、Impact、Fix、Preventionの4要素で構造化されます。これがyで承認されればmemoryディレクトリに保存されます。
-->

---

# 変換実例: スコープ逸脱への不満

**入力**:
> 「要件書いてあるでしょ？ なんで勝手にUI変えてるの？」

**AI分析結果**:
- **感情**: 不信感 (中)
- **本質**: AIの自律的な変更と要件の乖離
- **改善**: 変更前の確認プロセス

**生成されたフィードバック**:
> `feedback_scope_control.md`
> - **What**: 要件外の変更が無断で行われていた
> - **Impact**: ステークホルダーの意図との乖離
> - **Fix**: スコープ外変更の禁止ルールを明文化
> - **Prevention**: 実装前にadvisorで要件適合性を確認

<!--
2つ目の実例です。スコープ逸脱に対する不満の変換例です。「要件書いてあるでしょ？なんで勝手にUI変えてるの？」という発言から、AIは不信感を検出します。本質はAIが自律的に要件外の変更を行ったことです。生成されるフィードバックではスコープ外変更の禁止と、実装前の要件適合性確認を推奨しています。
-->

---

# チームでの運用方法

### ロール分担

| ロール | 担当 | 頻度 |
|-------|------|------|
| **入力者** | 全メンバー | 不満発生時いつでも |
| **レビュー者** | テックリード / PM | 週次 |
| **蓄積先** | `memory/` (Claude Code) | 自動 |

### 運用サイクル

1. **Capture**: メンバーが `/feedback-capture` で入力
2. **Review**: テックリードが y/e/n で判定
3. **Store**: 承認されたものを `memory/` に保存
4. **Act**: 週次で蓄積されたフィードバックを確認し、改善策を実行

> **ポイント**: フィードバックは「誰が言ったか」ではなく「何が課題か」に焦点を当てる

<!--
チームでの運用方法です。入力者は全メンバー、レビュー者はテックリードやPMが週次で担当します。運用サイクルはCapture、Review、Store、Actの4ステップです。重要なのはフィードバックを誰が言ったかではなく何が課題かに焦点を当てることです。個人の攻撃ではなくプロセス改善に繋げるのが目的です。
-->

---

# この章のまとめ

- **Supervisor Pattern** = PostToolUse hookでツール実行結果を監視するパターン
- **フィードバック変換パイプライン** = Capture → Analyze → Draft → Review の4段階
- **カスタムslash command** = `.claude/commands/` に `.md` を置くだけで作成可能
- **y/e/n レビュー** = 人間が取捨選択し、品質を担保する仕組み
- **チーム運用** = 入力者全員、レビュー者週次、蓄積は自動

<!--
この章のまとめです。Supervisor PatternはPostToolUse hookでツール実行結果を監視するパターンです。フィードバック変換パイプラインは4段階で感情を構造化データに変換します。カスタムslash commandは簡単に作成でき、y/e/nレビューで人間が品質を担保します。チーム運用では全メンバーが入力し、テックリードが週次レビューします。
-->

---

# 確認問題

**Q1**: Supervisor Patternで「Block」レベルの介入は何をするか？
- A: 結果を記録するだけ
- B: 基準違反の場合に実行を取り消す
- C: 新しいセッションを開始する

**Q2**: カスタムslash commandを作成する際、ファイルを配置するディレクトリは？
- A: `.claude/skills/`
- B: `.claude/commands/`
- C: `instructions/`

**Q3**: フィードバック蓄積時に最も重要な原則は？
- A: すべての発言を無条件で保存する
- B: 「誰が言ったか」を明記する
- C: 「何が課題か」に焦点を当て、人間が取捨選択する

<!--
確認問題です。Q1、Blockレベルは基準違反の場合に実行を取り消します。正解はBです。Q2、カスタムslash commandのディレクトリは.claude/commands/です。正解はBです。Q3、最も重要な原則は何が課題かに焦点を当て人間が取捨選択することです。正解はCです。
-->

---

<!-- _class: cover -->

# 第14章 完了!
## PostToolUse Supervisorパターンを理解したか?

**到達点チェック**:
- ✅ Supervisor Patternの概念を説明できる
- ✅ PostToolUse hookによるフィードバック自動化を設計できる
- ✅ カスタムslash commandの作成方法を習得した
- ✅ 感情→構造化変換パイプラインを理解している
- ✅ チーム運用の方法を設計できる

**次章**: 3 Guardrail分類とHarness選定フレームワーク

<div class="meta">
講師: なぎなた
</div>

<!--
第14章完了です。PostToolUse Supervisorパターンを理解できましたか。到達点を振り返りましょう。Supervisor Pattern、PostToolUse hook、カスタムslash command、変換パイプライン、チーム運用の5つを理解できていれば完璧です。次章ではGuardrail分類とHarness選定フレームワークを解説します。
-->
