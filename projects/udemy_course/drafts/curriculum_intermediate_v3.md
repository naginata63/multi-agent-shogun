# Udemy中級編カリキュラム v3 (1人+1AI完結版)
## 「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全実践」

- 版: v3 (1人+1AI完結版)
- 作成: 2026-04-25 / 足軽7号 (subtask_1482a)
- 出典: v2 (cmd_1465) を3ファイル分割。本ファイルは教育設計のみ。
- v2 との差分: マルチエージェント要素を全面削除、1人+1AIで全章再現可能に再構成

---

## 1. カリキュラム構成

### 1.1 全体構造

```
序章 (無料)                :  30 min × 1本  — before/after体験
L1 プロンプト基礎 (章1-4)  :  45 min × 4本
L2 コンテキスト実装 (章5-9):  60 min × 5本
L3 ハーネス実装 (章10-15)  :  60 min × 6本
L3 flagship case study     :  60 min × 1本  — 三層アーキ実装パターン
総合演習 (章17-18)         :  60 min × 2本
附録                       :  30 min × 3本

合計: 22 レクチャー / 約 17.5 時間 (本編・附録抜き) / 19.0 時間 (附録込み)
```

### 1.2 受講生の最終成果物 (L6 Create)

受講完了時、受講生は以下 4 点を自分のリポジトリに保有:

1. `CLAUDE.md` + `instructions/*.md` セット (L2 実装)
2. SessionStart / PreToolUse / PostToolUse / Stop / PreCompact 各ライフサイクル hook スクリプト 5本以上 (L3 実装)
3. claude-mem または同等メモリバックエンドへの `add_observations` 自動経路 (L2+L3 統合)
4. 自分のドメインに合わせた `cmd_intake_hook.sh` (起票時 mem-search + 自動 add_observations)

---

## 2. 章別構成 (ハンズオン具体化 + ストーリー設計)

### 序章: AI開発 3階層モデルとは (L0: Remember + Understand)

**所要**: 30 min / **無料プレビュー**

#### ストーリー (Emotional Hook)
> 「あなたが今やっているAI開発は、『壁に絵を描いては消す』を繰り返している状態かもしれません。本講座は、その壁に『窓』を開け、さらに『配管』まで通す方法を教えます。」

- 受講者の「これだ！」ポイント: 序章の3分タイムラプスで「before: 無秩序なプロンプト → after: 3層システム稼働」を見せる。このギャップが購買決断のトリガー。

#### 学習目標
- 3階層の定義を自分の言葉で説明できる
- 単独層では解決しない理由を切り分けられる
- 本講座の終着点 (L6 Create) を把握する

#### アウトライン
1. 3階層モデル図 (1枚スライド・全講座通貫)
2. 各層の failure mode 実例 3本ずつ
3. 既存ベストセラー講座マップと本講座の位置づけ
4. 最終成果物ツアー (受講後のリポジトリを3分で見せる)

---

### 第1章 プロンプトを「関数」として設計する

**所要**: 45 min / Bloom: L3 Apply / **無料プレビュー**

#### ストーリー (Emotional Hook)
> 「『AIに伝わればいい』と思っていませんか？ 伝わるプロンプトと、**再利用できる**プロンプトは別物です。この章では、1回書いて終わる指示を、何度でも使える『関数』に変えます。」

- 受講者の「これだ！」ポイント: 自分の日常業務タスクが「口頭指示 → 関数プロンプト」に変わる瞬間。before/after をその場で体験。

#### ハンズオン具体化
- **何を作る**: `prompts/task_XX_v1.md` (業務タスク1件の関数プロンプト)
- **どう作る**: (1) 日常の口頭指示を1つ選ぶ → (2) 入力/処理/出力の3パートに分解 → (3) XMLテンプレートに当てはめる → (4) Claude Codeで実行して結果を確認
- **完成品見た目**: 30-50行の構造化マークダウン。`<input>`/`<task>`/`<output_format>`タグ付き。
- **所要時間**: 演習15min + 解説30min

#### 成果物
- `prompts/task_XX_v1.md`

---

### 第2章 構造化プロンプトと失敗パターン

**所要**: 45 min / Bloom: L4 Analyze

#### ストーリー (Emotional Hook)
> 「プロンプトは『上手く書く』だけでは足りません。**どこが壊れているかを診断する力** が必要です。医者が病気を見分けるように、あなたはプロンプトの病気を見分けられるようになります。」

- 受講者の「これだ！」ポイント: 自分が書いたプロンプトを診断チェックリストに当てはめ、「あ、ここが原因だった」と発見する瞬間。

#### ハンズオン具体化
- **何を作る**: `prompts/diagnoses/case_1-3.md` (3件の失敗プロンプト診断レポート)
- **どう作る**: (1) 用意されたfailureプロンプト3本を読む → (2) 診断checklist(10項目)を適用 → (3) 修正案を作成 → (4) 再実行して改善を確認
- **完成品見た目**: 各ケース「症状 → 原因 → 修正 → 結果」の4セクション構成
- **所要時間**: 演習15min + 解説30min

#### 成果物
- `prompts/diagnoses/case_1-3.md`

---

### 第3章 「階層的プロンプト」: CLAUDE.md / instructions / task YAML の役割分担

**所要**: 45 min / Bloom: L4 Analyze + L5 Evaluate

#### ストーリー (Emotional Hook)
> 「CLAUDE.md に全部書いていませんか？ それは『引っ越し荷物を全部リビングに放り込む』状態です。この章では、引っ越し先の『部屋』を3つ設計します。」

- 受講者の「これだ！」ポイント: 自分のCLAUDE.mdが100行→30行にスリム化され、instructions/*.mdに整理されるリファクタリング体験。

#### ハンズオン具体化
- **何を作る**: スリム化後 `CLAUDE.md` + `instructions/*.md` 複数ファイル
- **どう作る**: (1) 既存CLAUDE.mdを読む → (2) 「変更頻度×適用範囲」マトリクスで分類 → (3) 3層に分解してcommit → (4) Claude Code新セッションで正しく動作確認
- **完成品見た目**: CLAUDE.md 30行以内 + instructions/role.md + instructions/project.md の構成
- **所要時間**: 演習20min + 解説25min

#### 成果物
- `CLAUDE.md` (スリム化後) + `instructions/*.md`

---

### 第4章 プロンプト品質 Gate: advisor() と QC template

**所要**: 45 min / Bloom: L5 Evaluate

#### ストーリー (Emotional Hook)
> 「『上手くいったと思う』は品質保証ではありません。この章では、あなたのプロンプトを**別のAI** に審査させる仕組みを作ります。裁判官がいる裁判所のように。」

- 受講者の「これだ！」ポイント: advisorが自分のプロンプトの盲点を指摘する瞬間。「自分では気づかなかった」という体験が、品質Gateの価値を実感させる。

#### ハンズオン具体化
- **何を作る**: `scripts/advisor_wrap.sh` + `shared_context/qc_template.md`
- **どう作る**: (1) advisor呼出3方式を比較 → (2) 最適方式をshellで実装 → (3) QC templateを自プロジェクト用に作成 → (4) 第1章成果物をadvisor+QCで評価
- **完成品見た目**: 30行程度のbashスクリプト + PASS/FAIL判定基準15項目のQC template
- **所要時間**: 演習15min + 解説30min

#### 成果物
- `scripts/advisor_wrap.sh` + `shared_context/qc_template.md`

---

### 第5章 コンテキストウィンドウ経済学

**所要**: 60 min / Bloom: L4 Analyze

#### ストーリー (Emotional Hook)
> 「コンテキストウィンドウは『財布』です。無限にあると思うと、いつの間にか空っぽになります。この章では、あなたのAIの『家計簿』をつけます。」

- 受講者の「これだ！」ポイント: 自分の直近セッションのtokens消費を見える化し、「ファイル読込が7割を占めていた」という発見。

#### ハンズオン具体化
- **何を作る**: `reports/context_budget_analysis.md` (コンテキスト消費源マトリクス)
- **どう作る**: (1) 直近1週間のセッションログからtokens計測 → (2) 消費源3カテゴリ(ツール結果/ファイル読込/会話履歴)別に集計 → (3) 予算配分案を作成 → (4) auto-compact閾値を設定
- **完成品見た目**: 表形式の消費源マトリクス + 予算配分のYAML設定
- **所要時間**: 演習20min + 解説40min

#### 成果物
- `reports/context_budget_analysis.md`

---

### 第6章 永続コンテキスト層 (claude-mem / MCP memory / Agent Skills)

**所要**: 60 min / Bloom: L4 Analyze + L5 Evaluate

#### ストーリー (Emotional Hook)
> 「AIに『前回のことを覚えている？』と聞いて、覚えていないことにイラッとしたことはありませんか？ この章では、AIに**忘れない記憶**を与えます。」

- 受講者の「これだ！」ポイント: 自分の過去1ヶ月の教訓10件をmemory/*.mdに落とし込み、新セッションで自動読込されることを確認する体験。

#### ハンズオン具体化
- **何を作る**: `memory/*.md` + `memory/MEMORY.md` (永続コンテキスト基盤)
- **どう作る**: (1) 3バックエンド比較表から自プロジェクトに適したものを選定 → (2) 過去教訓10件を4カテゴリ(user/feedback/project/reference)に分類 → (3) 各カテゴリmdファイルを作成 → (4) MEMORY.md索引を作成 → (5) 新セッションでmemoryが読まれることを確認
- **完成品見た目**: memory/ ディレクトリに4-6個のmdファイル + MEMORY.md索引(50-100行)
- **所要時間**: 演習25min + 解説35min

#### 成果物
- `memory/*.md` + `memory/MEMORY.md`

---

### 第7章 セッション再起動耐性 (SessionStart / PreCompact / rehydrate)

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### ストーリー (Emotional Hook)
> 「昨日の作業を今日再開したら、AIが『初めまして』と言ってきた――この絶望感、ありませんか？ この章では、AIに『おかえりなさい』と言わせる仕組みを作ります。」

- 受講者の「これだ！」ポイント: 意図的に /clear → SessionStart hookが発動 → 完全復旧する「魔法のような」体験。ここがL2の山場。

#### ハンズオン具体化
- **何を作る**: `scripts/sessionstart_hook.sh` + `scripts/precompact_hook.sh` + `.claude/commands/rehydrate.md`
- **どう作る**: (1) SessionStart hookテンプレを自分のプロジェクトに適用 → (2) 「自己識別 → memory読込 → instructions読込 → YAML復元」の4段階を実装 → (3) PreCompact hookで圧縮前情報保存 → (4) 意図的 /clear → 完全復旧テスト
- **完成品見た目**: 3ファイル + settings.json hook登録。/clear後3秒で完全復旧。
- **所要時間**: 演習25min + 解説35min

#### 成果物
- `scripts/sessionstart_hook.sh` + `scripts/precompact_hook.sh` + `.claude/commands/rehydrate.md`

---

### 第8章 コンテキスト運用ベストプラクティス

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### ストーリー (Emotional Hook)
> 「コンテキストは『設定して終わり』ではありません。日々の運用でどう読み、どう書き、どう使い回すかが、AI開発の生産性を決めます。この章では、コンテキストの『日常業務マニュアル』を作ります。」

- 受講者の「これだ！」ポイント: 自分の直近1週間のセッション履歴を分析し、「どのコンテキストが役立った/無駄だった」を定量化する体験。

#### ハンズオン具体化
- **何を作る**: `reports/context_operations_playbook.md` (運用プレイブック)
- **どう作る**: (1) 過去1週間のセッションを振返 → (2) CLAUDE.md/instructions/memoryの読込頻度と効果を計測 → (3) 不要コンテキストの削減プラン作成 → (4) rehydrateによる効率的な再開パターンを設計 → (5) 運用プレイブックとして文書化
- **完成品見た目**: 5-7セクションの運用マニュアル。チェックリスト付き。
- **所要時間**: 演習25min + 解説35min

#### 成果物
- `reports/context_operations_playbook.md`

---

### 第9章 コンテキスト劣化検出と自動更新

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### ストーリー (Emotional Hook)
> 「メモリは書いた時点の真実であって、今の真実とは限りません。この章では、メモリに『賞味期限』を設定します。」

- 受講者の「これだ！」ポイント: 自分のmemoryファイルから「ファイルパスが既に存在しない」「3ヶ月前の前提が古い」を自動検出するスクリプトが動く体験。

#### ハンズオン具体化
- **何を作る**: `scripts/memory_review.sh` (cron実行可能)
- **どう作る**: (1) staleness判定3ルールを実装(ファイル存在確認/日付チェック/手動検証フラグ) → (2) memory/*.mdをスキャンするbashスクリプト作成 → (3) 週次cronに登録 → (4) テスト用に古いmemoryを1件仕込んで検出確認
- **完成品見た目**: 週次レポートが出力される。「3件のstaleness検出: feedback_xxx.md のパスが存在しません」等。
- **所要時間**: 演習20min + 解説40min

#### 成果物
- `scripts/memory_review.sh` (cron実行可能)

---

### 第10章 ハーネスとは: Claude Code lifecycle 7イベント

**所要**: 60 min / Bloom: L2 Understand + L3 Apply

#### ストーリー (Emotional Hook)
> 「今までの章は『AIに何を覚えさせるか』でした。この章からは『AIが何をしたかを**監視する**』に変わります。あなたのAIに、監視カメラを付けます。」

- 受講者の「これだ！」ポイント: 最初のhookが実際に発火して「hello from hook!」が表示される瞬間。L3の入口。

#### ハンズオン具体化
- **何を作る**: `.claude/settings.json` hook登録 + `scripts/hook_hello.sh`
- **どう作る**: (1) 7イベントのflow図を理解 → (2) 最小のPreToolUse hook(echoするだけ)を作成 → (3) settings.jsonに登録 → (4) Claude Codeでコマンド実行→hook発火確認
- **完成品見た目**: settings.jsonにhookエントリが追加され、コマンド実行時にメッセージが表示される
- **所要時間**: 演習15min + 解説45min

#### 成果物
- `.claude/settings.json` (hook登録) + `scripts/hook_hello.sh`

---

### 第11章 完了 Gate ハーネス (H1 + H10 統合型)

**所要**: 60 min / Bloom: L6 Create

#### ストーリー (Emotional Hook)
> 「AIが『完了しました』と報告して、実際には完了していなかった――これ、毎日起きています。この章では、**機械的に完了を検証する門番**を立てます。」

- 受講者の「これだ！」ポイント: 「完了」報告に対してdone_gateがERRORを返す場面を見て、「やっぱり完了していなかった」を肌で感じる体験。

#### ハンズオン具体化
- **何を作る**: `scripts/done_gate.sh` (PostToolUse hook)
- **どう作る**: (1) 完了条件5項目をリスト化 → (2) done_gate.shに条件判定ロジックを実装 → (3) PostToolUse hookとして登録 → (4) 意図的に「未完了の完了報告」を再現 → done_gateがBLOCKすることを確認
- **完成品見た目**: 40-60行のbashスクリプト。YAML status → done の時に5条件を自動チェック。
- **所要時間**: 演習20min + 解説40min

#### 成果物
- `scripts/done_gate.sh`

---

### 第12章 silent fail 検出ハーネス (H4)

**所要**: 60 min / Bloom: L6 Create

#### ストーリー (Emotional Hook)
> 「エラーログに何も出ていないのに、結果がおかしい。これが**静かな失敗(silent fail)**です。一番危険なタイプの失敗です。この章では、沈黙を破る監視員を配置します。」

- 受講者の「これだ！」ポイント: 成功ログの中に紛れた「実は失敗」パターンをwatcherが検出し、WARNを出す瞬間。

#### ハンズオン具体化
- **何を作る**: `scripts/silent_fail_watcher.sh` + systemd user service unit file
- **どう作る**: (1) logからsilent fail候補パターン3個を抽出 → (2) inotifywait監視daemonを実装 → (3) exclusion filter(self-feedback防止)を追加 → (4) systemd user service化 → (5) テスト用logで検出確認
- **完成品見た目**: 常駐daemonがlogを監視し、silent fail検出時にWARNを通知。systemd status で active 確認。
- **所要時間**: 演習25min + 解説35min

#### 成果物
- `scripts/silent_fail_watcher.sh` + systemd user service unit file

---

### 第13章 Phase 間ゲートと cmd intake ハーネス (H3 + H8 + H9)

**所要**: 60 min / Bloom: L6 Create

#### ストーリー (Emotional Hook)
> 「過去に解決した問題を、また最初からやり直していませんか？ この章では、新しいタスクを始める前に**自動で過去を検索する**仕組みを作ります。」

- 受講者の「これだ！」ポイント: タスク起票時に自動で過去類似事例が表示され、「1ヶ月前に同じ問題を解決していた」を発見する体験。

#### ハンズオン具体化
- **何を作る**: `scripts/cmd_intake_hook.sh` + cmd YAML schema拡張
- **どう作る**: (1) mem-search pre-hookを実装(キーワード抽出→検索→結果注入) → (2) hit=0の場合の警告注入 → (3) PreToolUse hookとして登録 → (4) サンプルcmdで動作確認
- **完成品見た目**: cmd起票時にターミナルに「過去3件の類似事例を発見」と表示される
- **所要時間**: 演習20min + 解説40min

#### 成果物
- `scripts/cmd_intake_hook.sh` + cmd YAML schema拡張

---

### 第14章 殿激怒を feedback 自動化する lord-angry slash (H11)

**所要**: 60 min / Bloom: L5 Evaluate + L6 Create

#### ストーリー (Emotional Hook)
> 「ステークホルダーの怒りは、**最高の品質改善データ**です。でも、多くの場合、その場で終わってしまいます。この章では、怒りを**永続的な学習データ**に変換します。」

- 受講者の「これだ！」ポイント: 過去の上司/顧客の不満発言3件を入力 → slash commandが半自動でfeedback文書に変換 → レビュー→承認→commit までの流れを体験。

#### ハンズオン具体化
- **何を作る**: `.claude/commands/{ステークホルダー}-angry.md`
- **どう作る**: (1) 過去の強い不満発言3件をリストアップ → (2) lord-angry slashのテンプレートを作成 → (3) レビュー方式(y承認/e修正/n破棄)を実装 → (4) 実際に3件のfeedbackを生成
- **完成品見た目**: `.claude/commands/` にカスタムslash command。実行 → feedback草案が表示 → y/n で承認。
- **所要時間**: 演習20min + 解説40min

#### 成果物
- `.claude/commands/{ステークホルダー}-angry.md`

---

### 第15章 残り 7 ハーネスカタログと選定判断

**所要**: 60 min / Bloom: L4 Analyze + L5 Evaluate

#### ストーリー (Emotional Hook)
> 「12種類の道具を知って、全部欲しくなりましたか？ 大丈夫です。この章では、あなたのプロジェクトに**必要な3つだけ**を選びます。」

- 受講者の「これだ！」ポイント: 自分の直近1ヶ月の失敗記録と12ハーネスを照らし合わせ、「これ3つを採用すれば8割の問題が防げる」と判断できる体験。

#### ハンズオン具体化
- **何を作る**: `reports/harness_selection.md` (選定表 + 採用計画)
- **どう作る**: (1) 直近1ヶ月の失敗記録を整理 → (2) 12ハーネスの適用条件・コスト・効果を比較 → (3) 自プロジェクトに必要な3件を選定 → (4) 選定理由と期待効果を記述 → (5) 実装ロードマップを作成
- **完成品見た目**: 表形式の選定表 + 1週間の実装ロードマップ
- **所要時間**: 演習20min + 解説40min

#### 成果物
- `reports/harness_selection.md`

---

### 第16章 flagship: 三層アーキ実装パターン (L1+L2+L3 統合)

**所要**: 60 min / Bloom: L6 Create / **本講座最重要章**

#### ストーリー (Emotional Hook)
> 「ここまで学んだすべてが、1つのhookスクリプトに結実します。この章は本講座の**クライマックス**です。3階層統合の実例を、60分かけて一行ずつ解剖します。」

- 受講者の「これだ！」ポイント: L1のプロンプト設計 → L2のコンテキスト注入 → L3のhook実装が1つの `cmd_intake_hook.sh` に統合されているコードを読解し、「3層が繋がった！」を体験。さらに primary が死んでも fallback 3点が動く二重安全設計に感動。

#### ハンズオン具体化
- **何を作る**: `scripts/cmd_intake_hook.sh` (受講生版・3層統合) + `scripts/cmem_search.sh` + `logs/cmd_intake_obs.jsonl` + `queue/pending_mcp_obs.yaml` + SessionStart hook ingest ブロック
- **どう作る**:
  1. (10min) 問題設定: タスク起票時に過去事例検索忘れ
  2. (10min) L1層: mem-searchクエリ生成ルール(awk+名詞抽出)
  3. (15min) L2層: 4系統自動add_observations設計
  4. (15min) L3層: PreToolUse hook登録と発火
  5. (10min) fallback 3点: 監査ログ + pending queue + SessionStart ingest
- **完成品見た目**: 5ファイル構成の3層統合hook。primary APIが落ちた状態でテスト → fallback 3点が動くことを確認。
- **所要時間**: 演習30min + 解説30min

#### 成果物
- `scripts/cmd_intake_hook.sh` + `scripts/cmem_search.sh` + 監査ログ + fallback queue + SessionStart ingest

#### 附録: 応用例 (30min・オプション)
- 複数プロジェクトでの横断検索パターン
- 大規模コードベースでのスケーリング戦略
- チーム内でのhook共有とカスタマイズ

---

### 第17章 総合演習 Part 1: 自プロジェクトに3階層統合を組み込む

**所要**: 60 min / Bloom: L6 Create

#### ストーリー (Emotional Hook)
> 「ここまでバラバラに作ってきたパーツを、**自分のプロジェクト**に統合します。あなたのリポジトリが、『AI開発の3階層』対応になります。」

- 受講者の「これだ！」ポイント: 1-16章の個別成果物が統合され、`git log` に「3layer integration complete」が残る達成感。

#### ハンズオン具体化
- **何を作る**: `plans/3layer_roadmap.md` + Day 1実装commit
- **どう作る**: (1) 現状診断(3階層別の成熟度評価) → (2) Gap分析 → (3) 1週間の実装ロードマップ作成 → (4) Day 1分を実装してcommit
- **完成品見た目**: markdownのロードマップ(7日分のチェックリスト) + Day 1のcommit差分
- **所要時間**: 演習40min + 解説20min

#### 成果物
- `plans/3layer_roadmap.md` + Day 1 commit

---

### 第18章 総合演習 Part 2: ハーネス統合テスト

**所要**: 60 min / Bloom: L6 Create

#### ストーリー (Emotional Hook)
> 「最終演習です。あなたのAIに複数のタスクを実行させ、完了を自動検証し、静かな失敗を検知する。**本講座で学んだすべてがここで動きます。**」

- 受講者の「これだ！」ポイント: failure注入 → done_gateがBLOCK → silent_fail_watcherがWARN → すべて自動検出。「これがあれば安心してAIに任せられる」という確信。

#### ハンズオン具体化
- **何を作る**: 3ハーネス統合済みのリポジトリ
- **どう作る**: (1) 第11/12/13章のハーネス3件を1つのプロジェクトに組み込む → (2) 意図的なfailure注入テスト3パターン → (3) 全ハーネスが正常検出することを確認 → (4) 動作レポート作成
- **完成品見た目**: hookがブロック/検出する様子をキャプチャしたレポート
- **所要時間**: 演習40min + 解説20min

#### 成果物
- 3ハーネス統合済みのリポジトリ + 動作レポート

---

## 3. 附録

### 附録A. 差別化戦略 (30 min)

- 「3階層統合は市場ゼロ」調査根拠 (60件分析データ)
- 18 hook実装カタログ
- 受講生が自分のニッチを見つける3ステップフレームワーク

### 附録B. ビジネス導線設計 (30 min・オプション)

Marketing Trip メソッド準拠:
- **フロント**: 本講座 1,980円 (セール時980円) / 17.5h本編
- **導線**: ボーナスレクチャー → メルマガ登録 → オプトイン率32%目標
- **バックエンド**: 300リスト → 5%成約 → AI開発コンサル月30万 / 受託100-300万 / オンラインスクール30-50万
- **受講生ワークシート**: 自分のバックエンド商品設計テンプレート

### 附録C. トラブルシュート集 (30 min)

- Claude Code設定ファイル競合
- hookが発火しない5大原因
- claude-mem書き込み失敗時の復旧
- cost爆発の防衛策

---

## 4. 章別サマリ表

| # | 章 | 所要 | Bloom | 成果物 | Emotional Hook |
|---|----|------|-------|--------|---------------|
| 0 | 序章 | 30min | L0 | なし(無料) | before/afterのギャップ体験 |
| 1 | プロンプトを関数として | 45min | L3 | 関数プロンプト | 口頭指示→再利用可能プロンプト変換 |
| 2 | 構造化とfailure診断 | 45min | L4 | 診断レポート3件 | 自分のプロンプトの病気を発見 |
| 3 | 階層的プロンプト | 45min | L4-L5 | CLAUDE.md+instructions | 荷物を部屋に整理する快感 |
| 4 | advisor+QC template | 45min | L5 | advisor_wrap.sh | AIに自分の盲点を指摘される体験 |
| 5 | コンテキスト経済学 | 60min | L4 | 予算分析レポート | AIの家計簿を見る発見 |
| 6 | 永続コンテキスト3層 | 60min | L4-L5 | memory/*.md | AIに忘れない記憶を与える |
| 7 | セッション再起動耐性 | 60min | L5-L6 | 3hook+slash | /clear→完全復旧の魔法体験 |
| 8 | コンテキスト運用BP | 60min | L5-L6 | 運用プレイブック | 自分のコンテキストを定量化 |
| 9 | コンテキスト劣化検出 | 60min | L5-L6 | memory_review.sh | メモリに賞味期限を設定 |
| 10 | ハーネスとは | 60min | L2-L3 | 最小hook | AIに監視カメラを付ける |
| 11 | 完了Gate(H1+H10) | 60min | L6 | done_gate.sh | 未完了報告を門番がBLOCK |
| 12 | silent fail検出(H4) | 60min | L6 | watcher+unit file | 沈黙の失敗を検出する快感 |
| 13 | cmd intake(H3+H8+H9) | 60min | L6 | cmd_intake_hook.sh | 過去事例が自動表示される体験 |
| 14 | lord-angry slash(H11) | 60min | L5-L6 | カスタムslash | 怒りを学習データに変換 |
| 15 | ハーネスカタログ+選定 | 60min | L4-L5 | harness_selection.md | 自分に必要な3つを見つける |
| **16** | **flagship:三層アーキ** | **60min** | **L6** | **5ファイル統合hook** | **3層が繋がるクライマックス** |
| 17 | 総合演習1:3層統合 | 60min | L6 | ロードマップ+Day1 commit | 自分のプロジェクトが3層対応に |
| 18 | 総合演習2:ハーネス統合 | 60min | L6 | 3ハーネス統合レポート | 全学習が結実する達成感 |
| A | 附録:差別化戦略 | 30min | — | — | — |
| B | 附録:ビジネス導線 | 30min | — | ワークシート | — |
| C | 附録:トラブルシュート | 30min | — | — | — |

**合計**: 22 レクチャー / 約 17.5 時間 (本編・附録抜き) / 19.0 時間 (附録込み)

---

## 5. 差別化ポイント (4点)

1. **3階層統合は市場ゼロ** (60件調査で確認): 単独層の講座はレッドオーシャンだが、3層通貫の実装講座は存在しない
2. **18本hook実コードカタログ**: 既存ベストセラー2件は概論止まり。本講座は実コード18本の読解を含む
3. **失敗事例15件以上**: 実運用での事故(context爆発/silent fail等)を教材化
4. **flagship case study (第16章)**: 三層アーキテクチャを60+30minで解剖。既存講座では見られない深度

---

## 6. 変更履歴

- 2026-04-25 v3: 足軽7号 (subtask_1482a) マルチエージェント要素全面削除・1人+1AI完結化。第8章・第18章を全面書換。flagship を60+30minに分割。成果物4点に削減。
- 2026-04-25 v2: 足軽7号 (subtask_1465a) マーケ強化版
- 2026-04-24 v1: 足軽7号 (subtask_cmd_1445) 初版
