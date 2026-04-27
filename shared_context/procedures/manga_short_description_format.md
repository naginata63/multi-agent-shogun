# 漫画ショート タイトル + 説明欄フォーマット (殿確定 2026-04-27)

ドズル社切り抜きチャンネルの**漫画ショート動画**で YouTube タイトル & 説明欄に書く標準テンプレ。
通常切り抜き (shorts_knowledge.md) とは別物・AI画像生成注記付き。

## タイトルフォーマット

```
{状況本文・体言止め or 動詞+!? 体}【ドズル社切り抜き】@dozle  #漫画動画
```

### 実例 (殿提示・2026-04-27)

```
平安ぼんじゅうるが原始人ドズルを怒らせる!? 【ドズル社切り抜き】@dozle  #漫画動画
```

### 鉄則

1. **本文は 1 文・短く・キャラ名 + 動作 で完結**
2. 末尾に **!?** を付けると引き寄せ強化 (殿提示パターン)
3. **【ドズル社切り抜き】** 必須 (チャンネル明示)
4. **@dozle** (本家チャンネルメンション・スペース1個 + @ )
5. `@dozle` と `#漫画動画` の間は **半角スペース2個** (殿提示通り)
6. **#漫画動画** タグで shorts/通常切り抜きと区別 (タイトル末尾)
7. 全角スペースは使うな・半角スペースのみ

## テンプレ

```
{1-2行 状況説明 / 漫画タイトル相当}

📌 元動画：
{元動画タイトル}
{元動画URL}

■ドズル社公式チャンネル
https://www.youtube.com/@dozle

※公式ガイドラインに基づいて運営しています
https://www.dozle.jp/rule/

※漫画パネルはAI画像生成を使用しています

#ドズル社 #切り抜き #shorts #マイクラ #漫画
```

## 実例 (殿提示・2026-04-27)

```
ぼんじゅうるが原始人ドズルを怒らせて・・・

📌 元動画：
いろんな時代の人になってエンドラ討伐！【マイクラ】
https://www.youtube.com/watch?v=xlDFsyNm_eE

■ドズル社公式チャンネル
https://www.youtube.com/@dozle

※公式ガイドラインに基づいて運営しています
https://www.dozle.jp/rule/

※漫画パネルはAI画像生成を使用しています

#ドズル社 #切り抜き #shorts #マイクラ #漫画
```

## 鉄則

1. **1行目は状況説明** (漫画タイトルでない単純な状況描写・「○○が△△を××して・・・」体)
2. **📌 元動画：** 行は絵文字付き (📌)
3. **■ドズル社公式チャンネル** 行は ■ で始める (📌 ではない)
4. **AI画像生成注記必須**: 「※漫画パネルはAI画像生成を使用しています」(memory feedback_manga_short_description.md 由来・通常切り抜きには無い)
5. **公式ガイドライン参照必須**: https://www.dozle.jp/rule/
6. **タグ末尾固定**: `#ドズル社 #切り抜き #shorts #マイクラ #漫画` (順序厳守)

## YouTube アップロード時

```bash
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py update-description \
  --video-id "${VIDEO_ID}" \
  --description "$(cat <<'EOF'
{1行状況説明}

📌 元動画：
{元動画タイトル}
https://www.youtube.com/watch?v={元動画ID}

■ドズル社公式チャンネル
https://www.youtube.com/@dozle

※公式ガイドラインに基づいて運営しています
https://www.dozle.jp/rule/

※漫画パネルはAI画像生成を使用しています

#ドズル社 #切り抜き #shorts #マイクラ #漫画
EOF
)"
```

## 関連

- 通常切り抜き description: `shared_context/shorts_knowledge.md` 等 (本テンプレとは別)
- 漫画ショート全体workflow: `skills/manga-short-workflow/`
- 動画→panels JSON 中核script: `projects/dozle_kirinuki/scripts/generate_panel_candidates.py`
- 縦長変換+アップ: `shared_context/procedures/video_vertical_crop_upload.md`
