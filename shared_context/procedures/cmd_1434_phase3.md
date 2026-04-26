# cmd_1434 Phase3 手順: dashboard/index.html 拡張

## 対象ファイル
- `projects/dozle_kirinuki/analytics/dashboard/index.html` — 新セクション追加（既存セクション維持必須）

## 前提条件
- subtask_1434a (Phase1+2) が完了し、data.json に新keys が存在すること
- data.json 実体パス: `projects/dozle_kirinuki/analytics/dashboard/data.json`
- 既存セクション: KPI / 日次推移 / トラフィックソース / 動画一覧 / ランキング / AI分析

## 事前確認
1. 現状 dashboard/index.html を読み込み、既存セクション構造を把握
2. data.json の新keys を確認（demographics/content_type/monetization/predictions/content_analysis/retention_top5）
3. advisor() 呼び出し（実装前）

## 追加セクション一覧

### 3-A. 収益化進捗パネル（最上部に追加）
```html
<!-- 収益化進捗 -->
ショートパス: X万/1000万 (XX%) [進捗バー]
長尺パス: X,XXXh/4,000h (XX%) [進捗バー]
見込み達成日: YYYY-MM-DD
```
data参照: `data.monetization`

### 3-B. 視聴者層グラフ（新セクション）
- 年齢層 円グラフ (Chart.js doughnut) ← data.demographics.age
- 性別 円グラフ ← data.demographics.gender
- 国別 横棒グラフ Top10 ← data.demographics.country
- デバイス別 円グラフ ← data.demographics.device

### 3-C. Audience Retention 折れ線グラフ
- Top5動画のretention折れ線（動画IDタブ切替）
- X軸: 0%〜100%、Y軸: 視聴維持率 ← data.retention_top5

### 3-D. CTRトレンド（二重軸）
- CTR折れ線 + インプレッション折れ線
- ← data.daily_extended.ctr / data.daily_extended.impressions

### 3-E. 尺別・キャラ別パフォーマンス表
- 尺別: <30s / 30-60s / 60-120s / 120s+ 各平均再生/Like率 ← data.content_analysis.by_duration
- キャラ別: dozle/bon/MEN/qnly/orafu/nekooji 各平均再生 ← data.content_analysis.by_character

### 3-F. 予測セクション
- 3ヶ月後・6ヶ月後登録者予測 ← data.predictions.subs_3mo / subs_6mo
- 3ヶ月後累計再生予測 ← data.predictions.views_3mo
- **収益化達成予測日は除外**（monetization_est_date は data.json に存在しない）

## 注意事項
- Chart.js は既存CDNを流用（新規CDN追加不可の場合は簡易バーチャートで代替）
- data.json の新keys が存在しない場合は graceful degradation（セクション非表示）
- モバイル対応（800px以下でレイアウト崩れないこと）
- **既存KPI/日次推移/ランキング等を一切壊すな（regression-free必須）**

## テスト
```bash
# ブラウザで http://localhost:8080/ にアクセスして全セクション目視確認
# 新セクション: 収益化進捗/視聴者層/retention/CTR/キャラ別/予測
# 既存セクション: KPI/日次推移/トラフィック/動画一覧/ランキング が壊れていない
```

## advisor() 呼び出し
実装前（Step 3.8）と完了前（Step 4.8）の2回必須。

## 完了報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽X号、subtask_1434b完了。Phase3 dashboard新セクション6種実装済み。" \
  report_completed ashigaruX
```
