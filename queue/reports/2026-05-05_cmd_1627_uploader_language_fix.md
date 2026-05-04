# cmd_1627 完了報告: youtube_uploader.py --language ja 修正

## 概要

`youtube_uploader.py` の `upload_video()` で `--language ja` 指定時に YouTube Studio に「動画の言語: 日本語」が反映されない bug を修正。

## 根本原因

`defaultAudioLanguage` が `status` オブジェクト内に誤って配置されていた。YouTube Data API v3 の videos resource では `defaultAudioLanguage` は `snippet` プロパティであり、`status` には存在しない。API は `status` 内の未知フィールドをサイレントに無視するため、アップロード自体は成功するが言語設定は反映されなかった。

### 修正前 (status に誤配置)
```python
status_body = {
    "privacyStatus": privacy,
    "selfDeclaredMadeForKids": False,
    "defaultAudioLanguage": language,  # ← 誤: statusには存在しない
}
body = {
    "snippet": {
        ...
        "defaultLanguage": language,
    },
    "status": status_body,
}
```

### 修正後 (snippet に正しく配置)
```python
body = {
    "snippet": {
        ...
        "defaultLanguage": language,
        "defaultAudioLanguage": language,  # ← 正: snippet内
    },
    "status": status_body,
}
```

## 修正内容

| ファイル | 変更 |
|---------|------|
| `scripts/youtube_uploader.py` | `defaultAudioLanguage` を `status_body` から `snippet` に移動 |

## テスト結果

1. **アップロードテスト**: 10秒テスト動画 (private) を `--language ja` でアップロード → video_id `Fu9VuEAvE_A` 取得
2. **API確認**: `videos.list(part='snippet')` → `defaultLanguage: "ja"`, `defaultAudioLanguage: "ja"` 両方確認
3. **削除**: テスト動画を `delete --confirm` で削除済み

| テスト項目 | 結果 |
|-----------|------|
| `--language ja` でアップロード成功 | PASS |
| `snippet.defaultLanguage` = "ja" | PASS |
| `snippet.defaultAudioLanguage` = "ja" | PASS |
| 既存機能 (title/description/privacy) への影響なし | PASS |
| テスト動画削除 | PASS |

## commit

- submodle: `fix(uploader): --language ja が Studio に反映されない bug 修正 (cmd_1627)`
- main repo: 報告書 + metadata更新
