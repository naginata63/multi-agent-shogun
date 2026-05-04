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

# Guardrail カタログと選定フレームワーク
## 12種類の道具から、自分に必要な3つを選ぶ

<div class="meta">
中級編 v4 — 第15章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第15章へようこそ。この章では3つのGuardrail分類と、Harness選定フレームワークを解説します。これまでの章で多くのGuardrailを学んできました。この章では、すべてを体系的に分類し、あなたのプロジェクトに必要なものだけを選ぶ方法を学びます。なぎなたと申します。
-->

---

## この章で学ぶこと

1. **3 Guardrail categories** を説明できる
2. **12種類のHarness** を比較表で把握できる
3. **選定判断フレームワーク** を使って必要最小限を選べる
4. **実装ロードマップ** を1週間単位で計画できる
5. **よくある選定ミス** を回避できる

---

## この章で出てくる用語

> この章で初めて出てくる言葉を先にまとめておきます。

| 用語 | 意味 |
|------|------|
| **Hook** | Claude Codeが特定のタイミングで自動実行する仕組み。「引っ掛ける」の意味 |
| **Harness** | Hookを使って作った「安全装置」。Guardrailの具体実装 |
| **Guardrail** | AIの安全を守る仕組み全体。安全柵（ガードレール）のこと |
| **PreToolUse** | ツール実行**前**に発動するHookの種類 |
| **PostToolUse** | ツール実行**後**に発動するHookの種類 |
| **daemon** | バックグラウンドで常時動き続けるプログラム。デーモンと読みます |
| **Slash command** | `/` で始まるコマンド。Claude Code内で特殊操作を triggers します |
| **compact** | 会話が長くなった時、Claude Codeが自動的に会話を要約・圧縮すること |
| **PreCompact** | compactが起きる**直前**に発動するHookの種類 |

<!--
この章では5つの到達点を目指します。3つのGuardrail分類の理解、12種類のHarnessの比較、選定判断フレームワークの活用、1週間ロードマップの作成、よくある選定ミスの回避を学びます。
-->

---

# 「便利な道具がたくさんあると、全部欲しくなる」

> 大丈夫です。この章では、あなたのプロジェクトに **必要な3つだけ** を選ぶ方法を解説します。

- 第10〜14章で解説したGuardrail + 本章のカタログ = **12種類**
- **全部導入すれば安全**……ではありません
- プロジェクトの規模・フェーズに合わせて **最小限** を選ぶのが正解

<!--
つかみのスライドです。便利なGuardrailがたくさんあると、つい全部導入したくなります。しかしすべてを導入すると保守コストが増え、かえって複雑になります。この章では12種類の中から自分のプロジェクトに必要なものだけを選ぶフレームワークを解説します。多くのプロジェクトでは、3つ導入すれば8割の問題を防げます。
-->

---

# 3 Guardrail Categories

Guardrail（安全柵）を **3つのカテゴリ** に分類します:

| カテゴリ | 役割 | タイミング | 例 |
|---------|------|-----------|-----|
| **Prevention** | 問題を未然に防ぐ | ツール実行前 | 破壊操作BLOCK、入力検証 |
| **Detection** | 問題を早期発見する | ツール実行後 | 完了検証、形式チェック |
| **Recovery** | 問題から復旧する | セッション境界 | 状態復元、データ退避 |

- **Prevention** は **PreToolUse** で実現
- **Detection** は **PostToolUse** で実現
- **Recovery** は **SessionStart / Stop** で実現

<!--
3つのGuardrailカテゴリです。Preventionは問題を未然に防ぎPreToolUseで実現します。Detectionは問題を早期発見しPostToolUseで実現します。Recoveryは問題から復旧しSessionStartやStopで実現します。この3分類で12種類のHarnessを整理するのが選定の第一歩です。
-->

---

# 12 Harness カタログ — Prevention (1/3)

| # | 名称 | ライフサイクル | 目的 | 導入コスト |
|---|------|-------------|------|----------|
| 1 | **破壊操作防止** | PreToolUse | `rm -rf` 等をBLOCK | 低 |
| 2 | **過去事例検索** | PreToolUse | 類似タスクの自動検索 | 中 |
| 3 | **Phase-Gate** | PreToolUse | 前フェーズ完了確認 | 中 |

> **Prevention の共通点**: ツール実行 **前** に条件を確認し、必要に応じて **BLOCK** する

<!--
Preventionカテゴリの3つのHarnessです。破壊操作防止は最も導入コストが低く、どのプロジェクトでも最初に導入すべきHarnessです。過去事例検索は第13章で詳しく解説したセマンティック検索パイプラインです。Phase-Gateは前フェーズの完了を確認する検証です。すべてPreToolUseで実行されます。
-->

---

# 12 Harness カタログ — Detection (2/3)

| # | 名称 | ライフサイクル | 目的 | 導入コスト |
|---|------|-------------|------|----------|
| 4 | **完了Gate** | PostToolUse | 完了報告を自動検証 | 中 |
| 5 | **YAML整合性** | PostToolUse | 書込後の形式チェック | 低 |
| 6 | **自動インデックス** | PostToolUse | ファイル変更の自動索引 | 中 |
| 7 | **Silent fail検出** | daemon常駐 | エラーなしの失敗検出 | 高 |
| 8 | **コンテキスト監視** | daemon常駐 | 残量監視と警告 | 高 |

> **Detection の共通点**: ツール実行 **後** に結果を検証し、問題があれば **通知または修正** する

<!--
Detectionカテゴリの5つのHarnessです。完了GateとYAML整合性はPostToolUseで実行されます。自動インデックスもPostToolUseで、ファイル変更を検知してセマンティックインデックスに登録します。Silent fail検出とコンテキスト監視はdaemonとして常駐するため導入コストが高めです。すべてツール実行後に結果を検証します。
-->

---

# 12 Harness カタログ — Recovery + Slash (3/3)

| # | 名称 | ライフサイクル | 目的 | 導入コスト |
|---|------|-------------|------|----------|
| 9 | **セッション復旧** | SessionStart | `/clear` 後の自動復元 | 中 |
| 10 | **圧縮前保存** | PreCompact | compact前のデータ退避 | 低 |
| 11 | **終了時チェック** | Stop | 未処理タスクの警告 | 低 |
| 12 | **Feedback自動化** | Slash command | 不満を構造化に変換 | 低 |

> **Recovery の共通点**: セッション境界で **状態を保存・復元** し、データ消失を防ぐ

<!--
RecoveryカテゴリとSlash commandの4つのHarnessです。セッション復旧は/clear後の自動復元、圧縮前保存はcompact前のデータ退避、終了時チェックは未処理タスクの警告です。これら3つはRecoveryに分類されます。Feedback自動化はSlash commandとして動作し、第14章で詳しく解説しました。
-->

---

# 選定判断フレームワーク

**3ステップ** で必要最小限を選ぶ:

### Step 1: 分類 — 12種類を3カテゴリに分ける
- Prevention (1-3) / Detection (4-8) / Recovery + Slash (9-12)

### Step 2: 優先順位付け — 失敗記録で採点
> あなたのプロジェクトで過去に起きた失敗を「頻度(高/中/低)」と「影響度(高/中/低)」で評価し、両方「高」のものから優先します。**新規プロジェクト(失敗記録なし)の場合は、表の固定優先度を出発点にしてください。**

| 失敗カテゴリ | 対応Harness | 優先度 |
|------------|-----------|--------|
| 破壊的操作の事故 | #1 破壊操作防止 | 最高 |
| 完了漏れによる再作業 | #4 完了Gate | 高 |
| コンテキスト消失 | #9 セッション復旧 | 高 |
| 重複作業 | #2 過去事例検索 | 中 |

### Step 3: 選定 — 各カテゴリから1個 (合計3つ)
- 余裕があればカテゴリごとに2個目を追加 (合計4〜6個)

<!--
選定判断フレームワークです。3ステップで必要最小限を選びます。まず12種類を3カテゴリに分類します。次に過去の失敗記録の頻度と影響度で採点し、優先順位を付けます。最後に各カテゴリから1個を選び、合計3つに絞ります。出発点は過去の失敗記録です。失敗がないプロジェクトでも、未然に防げるリスクを評価しましょう。
-->

---

# 適用条件 — プロジェクト規模別

| Harness | 小規模 (1-5人) | 中規模 (5-20人) | 大規模 (20+人) |
|---------|:---:|:---:|:---:|
| #1 破壊操作防止 | **必須** | **必須** | **必須** |
| #2 過去事例検索 | 推奨 | **推奨** | **必須** |
| #4 完了Gate | 推奨 | **必須** | **必須** |
| #7 Silent fail | — (小規模ではエラー検知で代替可) | 推奨 | **推奨** |
| #9 セッション復旧 | 推奨 | **推奨** | **必須** |
| #12 Feedback自動化 | 推奨 | **推奨** | **推奨** |

> **鉄則**: #1 破壊操作防止は **全プロジェクトで必須** — これだけは最初に導入する

<!--
プロジェクト規模別の適用条件です。破壊操作防止は全規模で必須です。これだけは最初に導入してください。小規模プロジェクトでは3〜4個で十分です。中規模では完了Gateとセッション復旧も推奨になります。大規模では過去事例検索も必須になり、Silent fail検出も検討すべきです。
-->

---

# 実装ロードマップ

**1週間で段階導入する方法**:

| Day | タスク | 成果物 | 参照章 |
|-----|--------|--------|--------|
| 1 | 失敗記録の整理 + 選定表作成 | 選定表 (Markdown) | — |
| 2 | #1 破壊操作防止の実装 + テスト | pretool_check.sh | 第10章 |
| 3 | #4 完了Gateの実装 + テスト | done_gate.sh | 第12章 |
| 4 | #9 セッション復旧の実装 + テスト | session_restore.sh | 第11章 |
| 5 | settings.json統合 + 結合テスト | settings.json |
| 6 | 運用観察 + ログ確認 | 運用レポート |
| 7 | 効果測定 + 次フェーズ計画 | 振り返りメモ |

> **鉄則**: 1日に1Harness。複数同時導入はトラブルの元。

<!--
1週間でHarnessを導入するロードマップです。1日目は失敗記録の整理と選定表の作成です。2日目から4日目までは選定したHarnessを1日1つずつ実装してテストします。5日目にsettings.jsonに統合して結合テストを行います。鉄則は1日に1Harnessです。複数を同時に導入すると問題が起きたときに原因を特定できなくなります。
-->

---

# よくある選定ミス 3選

### ミス1: 「全部入り」症候群
- **症状**: 12種類すべてを導入して保守コスト爆発
- **対策**: まず3つ選ぶ。効果を確認してから増やす

### ミス2: コスト無視
- **症状**: daemon常駐Harnessを3つ導入してリソース枯渇
- **対策**: daemon常駐は最大2つまで。軽量hookで代用できないか検討

### ミス3: 既存hookとの競合
- **症状**: 新しいhookが既存のhookを上書きして動作不良
- **対策**: 導入前にsettings.jsonのhooksセクションを必ず確認

<!--
よくある3つの選定ミスです。1つ目は全部入りの症候群で、12種類すべてを導入すると保守コストが爆発します。まず3つ選び効果を確認してから増やしましょう。2つ目はコスト無視で、daemon常駐は最大2つまでに抑えます。3つ目は既存hookとの競合で、導入前にsettings.jsonを必ず確認します。
-->

---

# この章のまとめ

- **3 Guardrail categories**: Prevention / Detection / Recovery で分類
- **12 Harness**: 3カテゴリに整理し、比較表で把握
- **選定判断フレームワーク**: 分類 → 優先順位付け → 各カテゴリから1個 (計3つ)
- **1週間ロードマップ**: 1日1Harnessの段階導入が鉄則
- **3つのミス**: 全部入り / コスト無視 / 競合 — これらを避ければ3つで多くの問題を防止

<!--
この章のまとめです。3つのGuardrailカテゴリで12種類のHarnessを整理しました。選定判断フレームワークで必要最小限を選びます。段階的な導入が重要で、1日1Harnessが鉄則です。3つのよくあるミスを避ければ、3つのHarnessで多くの問題を防ぐことができます。
-->

---

# 確認問題

**Q1**: 3 Guardrail categoriesのうち、「問題を未然に防ぐ」カテゴリはどれか？
- A: Detection
- B: Prevention
- C: Recovery

**Q2**: Harness選定で最初にやるべきことは何か？
- A: 12種類すべてを導入する
- B: 過去の失敗記録を整理する
- C: 最もコストの低いHarnessを選ぶ

**Q3**: 「全部入り」症候群の対策として正しいものは？
- A: まず3つ選び、効果確認後に増やす
- B: 12種類すべて同時に導入する
- C: コストが高いものから優先して導入する

<!--
確認問題です。Q1、問題を未然に防ぐのはPreventionカテゴリです。正解はBです。Q2、選定で最初にやるべきは過去の失敗記録の整理です。正解はBです。Q3、全部入りの対策はまず3つを選び効果確認後に増やすことです。正解はAです。
-->

---

<!-- _class: cover -->

# 第15章 完了!
## あなたに必要な3つ、見つかりましたか?

**到達点チェック**:
- ✅ 3 Guardrail categoriesを説明できる
- ✅ 12 Harnessの比較表を読み解ける
- ✅ 選定判断フレームワークを使える
- ✅ 1週間ロードマップを計画できる
- ✅ よくある選定ミスを回避できる

**次章**: 三層アーキテクチャ実装パターン

<div class="meta">
講師: なぎなた
</div>

<!--
第15章完了です。3つのGuardrail分類とHarness選定フレームワークを理解できましたか。到達点を振り返りましょう。3カテゴリの分類、12Harnessの比較、選定フレームワーク、ロードマップ、ミス回避の5つを理解できていれば完璧です。次章は三層アーキテクチャ実装パターンです。ここまで学んだすべてが結実します。
-->
