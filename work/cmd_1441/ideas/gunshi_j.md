# 軍師アイデア出し（カテゴリ j: その他横断課題）

cmd_1441 Phase A 軍師担当分。足軽 a-i 9カテゴリに収まらない整理余地。
作成: 2026-04-24 13:30 / gunshi

task YAML 要件: 現状 / やれてないこと / アイデア の 3セクション・最低5アイデア。

---

## テーマ 1. プロセス改善（軍師QC手順自己改善）

### 現状
- `shared_context/qc_template.md` (7,346 bytes) に「実ファイル必読」「3箇所目視」「証跡報告」の3絶対ルールあり
- 軍師QC実績: 本日 qc_1421a〜qc_1440j まで約15件・概ね PASS 判定
- ただし本日 qc_1434b で **generate_dashboard.py 冪等性を見落とし** → cmd_1434b2 で足軽2号が事後補完

### やれてないこと
- severity (CRITICAL/HIGH/MEDIUM/LOW) の判断基準が感覚依存・数値化されていない
- QC報告 YAML のフォーマットが軍師ごとに揺れる（本日のみでも `deliverables_verified` 書き方3パターン）
- ジェネレータ系ファイル (cronで再生成される index.html 等) の冪等性チェック観点が qc_template.md に未記載
- 「仮説（推論）」と「実測（curl/git/ffprobe）」を区別する欄が報告YAMLにない

### アイデア（4項目）
1. **severity 判断基準の数値化**: 影響範囲(動画本数/ユーザ数/データ量) × 修正緊急度(即 or 翌日 or 来週) で CRITICAL/HIGH/MEDIUM/LOW を機械判定できるマトリックスを qc_template.md に追加
2. **冪等性チェック項目の追加**: テンプレート/ジェネレータ系ファイル改修時は「再生成後も同等か」を必ず確認する観点を qc_template.md に追加
3. **QC報告 YAML スキーマ統一**: 軍師QC報告YAMLを shared_context/qc_report_schema.yaml で型定義・必須field明示
4. **推論 vs 実測 の区別**: QC報告に `verification_method: empirical | inferred` を必須化

---

## テーマ 2. 観測性（claude-mem bug 横断影響 + Opus[1m] 切替観測）

### 現状
- claude-mem v10.6.3 稼働中・12,166 観察・1,757 sessions・8,038 summaries
- WORKER_HOST=0.0.0.0 化で LAN アクセス可能（cmd_1440j 完了）
- cmd_1436 軍師分析で `/api/observations` の dateStart/End がサイレント無視される bug 確定
- 本日全エージェント Opus[1m]+Thinking 切替完了・観測基準値未取得

### やれてないこと
- claude-mem の dateRange bug の upstream 報告（GitHub issue 起票）未着手
- `CLAUDE_MEM_SKIP_TOOLS` で Skill/SlashCommand/TodoWrite 記録除外されている事実がドキュメント化されていない（MEMORY.md 未反映）
- Opus[1m] 切替後の観測項目を**決めていない** → 今夜の観測ウィンドウが無為に過ぎる risk
- semantic embedding 未使用 (FTS5 のみ) の事実を運用ルールに組み込んでいない

### アイデア（3項目）
1. **Opus[1m] 観測ダッシュボード新設**: 1時間おきに `(token消費/応答時間/compaction発生数/529発生率)` を claude-mem 観察として記録する cron スクリプト・今夜中に実装して明日朝に基準値取得
2. **claude-mem dateRange bug 回避ガイド**: `memory/feedback_claude_mem_daterange_broken.md` を作成・「`/api/observations` の dateRange は無視される・keyword単独検索＋created_at 手動filterで代替」を全エージェント共通ルール化
3. **semantic 検索回避パターン集**: 意味的に関連するが語彙が異なる検索（例: 「音ズレ」↔「sync issue」）の同義語事前列挙パターンを shared_context/semantic_query_patterns.md に記録

---

## テーマ 3. cron 一元化・自動化整理

### 現状（`crontab -l` scan）
- 稼働中: genai_daily_report(7:00) / semantic_search update(毎時) / dedup_check(15分毎) / youtube_analytics_snapshot(5:57) / nightly_audit(2:02) / kill_orphan_chrome(**毎分**)
- コメントアウト 4本: auto_fetch(18:15/19:30) / scene_search build / post_fetch_recommend(2本)
- ログ先が `logs/` と `projects/dozle_kirinuki/logs/` と `projects/dozle_kirinuki/analytics/` で分散

### やれてないこと
- **kill_orphan_chrome が毎分**は過剰。起動率 <1%/時 想定でも 60分で 60回起動 → 無駄なCPU消費
- コメントアウトされた cron の復活要否が未判断（auto_fetch は dozle_kirinuki の新着動画収集・重要度高）
- cron 失敗時のアラート経路がない → silent fail しても気付けない
- crontab 一覧のドキュメント化なし (`shared_context/cron_inventory.md` 等)

### アイデア（3項目）
1. **cron インベントリ作成**: `shared_context/cron_inventory.md` に全 cron エントリの用途・頻度・ログ先・失敗時挙動を列挙・quarterly レビュー義務化
2. **kill_orphan_chrome の頻度見直し**: 毎分 → 15分毎に変更（年間CPU時間 96%削減・孤児プロセス滞在時間は 14分以内で許容範囲）
3. **cron 失敗検知**: 各ログファイルの終行を毎時 check し ERROR/FAIL 発見で ntfy 通知する `scripts/cron_health_check.sh` 新設

---

## テーマ 4. テスト文化・QC 形骸化防止

### 現状
- `shared_context/qc_template.md` 存在・3絶対ルール明記
- 軍師 QC は report YAML 必須・karo への inbox 通知でループ閉じる
- Test Rules（CLAUDE.md）: SKIP=FAIL・Preflight check・E2Eは家老担当・テスト計画レビュー

### やれてないこと
- テスト **coverage メトリクス**なし（どの scripts/ ファイルが1度もテストされたか不明）
- cmd 完了時の「テスト実施率」追跡なし（軍師QC が代替している想定だが、ユニット粒度は空洞化）
- regression テスト自動化なし（夜間 nightly_audit はあるが「実行」ではなく「静的scan」のみ）
- feedback_*.md ルールの quarterly 見直し未実施（形骸化 risk）

### アイデア（3項目）
1. **feedback rule 四半期レビュー cron**: `memory/feedback_*.md` を3ヶ月おきに軍師が点検し「死文化」フラグ立てる cron 新設・陳腐化防止
2. **テスト coverage 集計**: scripts/ 配下の .py/.sh ファイルごとに「最終テスト実行日」を記録する軽量DB or YAML (shared_context/test_coverage.yaml)
3. **E2E 再現テストpack**: 過去 hotfix 案件（silent fail / 音ズレ / bot検知等）を再現するスモークテストを `tests/smoke/` 配下に保管・nightly_audit で走らせる

---

## テーマ 5. アラート設計・ntfy 運用

### 現状
- `scripts/ntfy.sh`・`ntfy_listener.sh`・`ntfy_voice.sh` の3本あり
- ntfy 呼出 script 5本: genai_daily_report / genai_ntfy_top3 / inbox_watcher / mcp_experiment / nightly_audit
- CLAUDE.md に家老 ntfy ルール明記（cmd完了・YouTube非公開アップ・🚨要対応）
- dashboard.md の 🚨 要対応 section: 2箇所

### やれてないこと
- ntfy 通知の**レベル分け**なし (info/warn/critical)
- ntfy 呼出パターンが script 毎にバラバラ（引数順・プライオリティ指定なし）
- 🚨要対応 の自動 pruning なし（解決後に手動で削除が必要）
- ntfy 送信失敗時の fallback（ログ or 再送）なし

### アイデア（3項目）
1. **ntfy wrapper script の統一**: `scripts/ntfy_send.sh "level:title:body"` 形式で全呼出を wrap・レベル(INFO/WARN/ERROR/CRITICAL)とタグ付け統一
2. **🚨要対応の auto-prune**: 🚨 section を cmd 完了時に家老が自動削除する hook（解決済みなのに残り続けるゴミ対策）
3. **ntfy 失敗時 fallback**: 送信失敗時は `logs/ntfy_failed.log` に堆積し、翌日朝一で再送 cron

---

## テーマ 6. 殿意思決定フロー（cmd_1434→1437 部分反転観察）

### 現状
- cmd_1434 Phase3 で追加した `monetization` セクションを cmd_1437 で削除（YPP条件達成判明による意思反転）
- cmd_1434 Phase0 設計レビューで D1-D5 殿確認ゲートを挙げたが、実装は殿確認を**バイパス**して進行
- 事後承認モードで 3D円グラフ不可(D1) は足軽判断で 2D に着地（結果的に正解）

### やれてないこと
- 「殿 precondition 確認」を cmd 起票段階で明示する運用ルールなし
- 設計レビュー（軍師 Phase0）後の殿ゲート必須化のルール明文化なし
- cmd 内で「部分反転」が発生した時の記録フォーマットなし

### アイデア（2項目）
1. **cmd 起票時の殿 precondition 欄**: `shogun_to_karo.yaml` の cmd entry に `lord_preconditions: [...]` 欄追加・確認済みフラグを家老が記録
2. **設計レビュー後の殿ゲート必須化**: 軍師 Phase0 が D1-D5 的な確認項目を列挙したら、家老は Phase1 発令前に必ず殿確認を挟むルールを CLAUDE.md に追記

---

## まとめ（Phase B への引継ぎ）

- **テーマ 1-6 × アイデア 合計 18件**（task 最低5件を超過達成）
- 優先度判定は Phase A スコープ外。**subtask_1441_phaseB の統合作業で将軍 shogun_horizontal.md (32項目)・足軽 a-i の ideas と突合**し、重複削除・3軸評価(緊急度/コスト/効果)・subtask分解・並列可能性判定を行う
- 本 md は軍師独立視点の raw idea 提供のみ。Phase B 判定に委ねる

以上。
