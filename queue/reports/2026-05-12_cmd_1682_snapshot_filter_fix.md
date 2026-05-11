# cmd_1682: snapshot.py 非公開動画除外フィルタ修正

## 修正概要
`scripts/youtube_analytics_snapshot.py` の Shorts feed 露出警告ロジックに非公開動画を除外するガードを追加。

## 背景
- 2026-05-12 snapshot で `[確認用・非公開] 断崖絶壁` (NXUY7Dd0mRY, privacy_status=private) が警告対象に含まれる誤検知が発生
- L298 で `privacy_status == "public"` フィルタ済みだが、防御的に is_warn 判定にもガードを追加

## 修正内容 (3箇所)

### 1. is_warn 判定 (L353-360)
```python
# Before
is_warn = (elapsed_days >= 2 and views > 0 ...) or (elapsed_days >= 2 and views == 0)

# After
is_warn = v.get("privacy_status") == "public" and (
    (elapsed_days >= 2 and views > 0 ...) or (elapsed_days >= 2 and views == 0)
)
```

### 2. レポート warns フィルタ (L914)
```python
# Before
warns = [c for c in shorts_feed_check if c.get("is_warning")]

# After
public_only = [c for c in shorts_feed_check if c.get("privacy_status") == "public"]
warns = [c for c in public_only if c.get("is_warning")]
```

### 3. レポート表表示 (L934)
```python
# Before
for c in shorts_feed_check[:10]:

# After
for c in public_only[:10]:
```

## テスト結果
2026-05-12_raw.json (117KB, 全動画データ) で検証:
- Public shorts: 64本 (変更なし・L298フィルタ正常動作)
- 除外された非公開動画: 13本 (private/unlisted)
- 内訳: private=12本, unlisted=1本
- `[確認用・非公開] 断崖絶壁` (NXUY7Dd0mRY): 除外確認済み

## 修正前後の警告動画数変化
- 修正前 (既存L298フィルタのみ): 警告 4本 (いずれも public)
- 修正後 (is_warn ガード追加): 警告 4本 (変更なし・防御的追加のみ)
- **レポート側**: 非公開動画が表に表示されなくなった

## acceptance_criteria
- [x] privacy_status != public の動画が is_warn 対象外
- [x] レポート生成側でも非公開動画が除外
- [x] テスト実行で誤検知なし確認
- [x] git commit 済
- [x] 報告書 queue/reports/2026-05-12_cmd_1682_snapshot_filter_fix.md 格納
