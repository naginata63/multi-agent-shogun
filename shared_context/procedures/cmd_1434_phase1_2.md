# cmd_1434 Phase1+2 手順: youtube_analytics_snapshot.py 拡張

## 対象ファイル
- `scripts/youtube_analytics_snapshot.py` — API取得拡張 + data.json 拡張

## 事前確認
1. `python3 scripts/youtube_analytics_snapshot.py --help` で現状把握
2. 既存 data.json の構造確認 (keys: generated_at/channel/daily_series/traffic_sources/videos/analysis_history等)
3. advisor() 呼び出し（実装前）

## Phase 1: API取得拡張

### 1-A. 日次シリーズ拡張
既存 `metrics=views,estimatedMinutesWatched,averageViewDuration,likes,subscribersGained` に追加:
- `subscribersLost`, `comments`, `shares`, `averageViewPercentage`
- `cardImpressions`, `cardClicks` (取れれば)

### 1-B. contentType 分離
`filters=contentType==short` / `contentType==longForm` で2回クエリ
→ 短尺/長尺別: views, estimatedMinutesWatched, subscribersGained

### 1-C. 視聴者層
- `dimensions=ageGroup` → views/estimatedMinutesWatched
- `dimensions=gender` → views
- `dimensions=country` Top10

### 1-D. デバイス別
- `dimensions=deviceType` → views/estimatedMinutesWatched
- `dimensions=operatingSystem` Top5

### 1-E. Audience Retention（再生数TOP5動画）
- `dimensions=elapsedVideoTimeRatio` + `filters=video==VIDEO_ID`
- TOP5動画について各10%地点の視聴維持率

### 1-F. impressions/CTR
- `metrics=impressions,impressionsClickThroughRate` 日次 + 動画別

## Phase 2: data.json 拡張

既存キーはそのまま維持。以下を追加:
```json
{
  "daily_extended": {"dates": [], "comments": [], "shares": [], "subs_lost": [], "avg_view_pct": [], "impressions": [], "ctr": []},
  "content_type": {"short": {"views": 0, "watch_minutes": 0, "subs_gained": 0}, "longForm": {"views": 0, "watch_minutes": 0, "subs_gained": 0}},
  "demographics": {"age": [...], "gender": {"male": 0, "female": 0, "unknown": 0}, "country": [...Top10...], "device": {...}},
  "retention_top5": {"VIDEO_ID": [{"ratio": 0.0, "audienceWatchRatio": 0.0}, ...]},
  "monetization": {"shorts_path_views_90d": 0, "shorts_path_pct": 0.0, "longform_watch_hours_365d": 0, "longform_path_pct": 0.0},
  "predictions": {"subs_3mo": 0, "views_3mo": 0, "subs_6mo": 0},
  "content_analysis": {"by_duration": [...], "by_character": [...]}
}
```

`content_analysis.by_character`: タイトルから `dozle/bon/MEN/qnly/orafu/nekooji` キーワード検出→各平均再生数

## テスト（Phase 1+2）
```bash
python3 scripts/youtube_analytics_snapshot.py
# エラーなく完走し data.json に新keys含まれることを確認
# data.json 実体パス: projects/dozle_kirinuki/analytics/dashboard/data.json
# ※ スクリプト内のOUTPUT_PATH変数を事前確認し、正しいパスで検証せよ
python3 -c "import json; d=json.load(open('projects/dozle_kirinuki/analytics/dashboard/data.json')); print(list(d.keys()))"
```

## 注意事項（パス確認必須）
- `scripts/youtube_analytics_snapshot.py` は親リポ直下に存在（`scripts/dashboard/` 配下ではない）
- data.json 出力先: スクリプト内 OUTPUT_PATH を確認。実体は `projects/dozle_kirinuki/analytics/dashboard/data.json`
- generate_dashboard.py が存在する場合、snapshot.py → generate_dashboard.py → index.html の2段構えを確認せよ

## advisor() 呼び出し
実装前（Step 3.8）と完了前（Step 4.8）の2回必須。

## 完了報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽X号、subtask_1434a完了。Phase1+2実装済み。data.json新keys確認済み。" \
  report_completed ashigaruX
```
