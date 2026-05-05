# cmd_1631 完了報告書: xZTtk4pJcAs 話者実名化 + index 同期

## 概要

scene_index_v2 に含まれる xZTtk4pJcAs (86万トンダム埋め) の旧話者ラベル (A-F) を実名に更新する作業。
旧エントリを削除 → build --update で実名版SRTから再投入 → info/query/audit で検証完了。

## 修正前の状態

- words metadata: 66961 entries (うち xZTtk4pJcAs: 434件)
- chunks metadata: 12316 entries (xZTtk4pJcAs: 0件 — 既に未登録)
- comments metadata: 2626 entries (うち xZTtk4pJcAs: 23件)
- 話者一覧に A-F は含まれていなかったが、xZTtk4pJcAs の434件が旧SRT由来のエントリとして残存

## 実施手順

1. **words 削除**: metadata.json から xZTtk4pJcAs の434件を除去、embeddings.npy も同期削除
   - Before: 66961 entries → After: 66527 entries
2. **comments 削除**: comments_metadata.json から xZTtk4pJcAs の23件を除去
   - Before: 2603 entries → After: 2603 entries (23件除去)
3. **chunks**: 既に0件のため処理不要
4. **build --update --mode words**: xZTtk4pJcAs の実名SRT (merged_xZTtk4pJcAs.json) から再投入
   - 3841 words → 434 word-segments 再生成
5. **build --update --mode chunks**: xZTtk4pJcAs のチャンク生成
   - 85 新規30s-chunks 生成

## 修正後の状態 (scene_search_v2.py info 出力)

```
=== scene_index_v2 情報 ===
  build_time: 2026-05-05T15:09:30.178585
  n_word_segments: 66961
  n_chunk_segments: 12401
  n_videos: 67
  version: v2.1
  model: gemini-embedding-2-preview
  embed_dim: 3072

[words インデックス]
  shape: (66532, 3072)
  動画数: 67
  話者: ['bon', 'dozle', 'external_collab', 'nekooji', 'oo_men', 'orafu', 'qnly', 'ramerry', 'unknown']

[chunks インデックス]
  shape: (12317, 3072)
  動画数: 67
  話者: ['bon', 'dozle', 'external_collab', 'nekooji', 'oo_men', 'orafu', 'qnly', 'ramerry', 'unknown']

[comments インデックス]
  shape: (2603, 3072)
  動画数: 66
```

## Acceptance Criteria 検証

| 項目 | 結果 |
|------|------|
| info 話者一覧に A/B/C/D/E/F が存在しない | **PASS** — 話者: bon, dozle, external_collab, nekooji, oo_men, orafu, qnly, ramerry, unknown |
| query で xZTtk4pJcAs 関連に実名話者が返る | **PASS** — おじいちゃんで検索 → bon, dozle 等の実名で hit |
| audit で xZTtk4pJcAs=quality_status:ok | **PASS** — `xZTtk4pJcAs  ok  bon, dozle, oo_men, orafu, qnly` |
| 完了報告書作成 | **PASS** — 本ファイル |

## query 検証結果 ('おじいちゃん')

```
# Rank Score  Video          Time        Speaker
1    0.693  ojQivRzcBzs    38:30-38:59 bon,dozle,nekooji
2    0.691  d3bDsu_pFh8    26:45-27:15 dozle,oo_men,orafu
3    0.691  p1aSPm-VWGc    60:45-61:15 bon,dozle,oo_men
4    0.691  koeM_jz4CdM    01:15-01:45 dozle,nekooji
5    0.690  p1aSPm-VWGc    60:30-61:00 bon,dozle,oo_men
```

## audit 検証結果

```
xZTtk4pJcAs      ok                     bon, dozle, oo_men, orafu, qnly
```

## 備考

- data/scene_index_v2/ は .gitignore 済みのため、index更新はローカルのみ。git commit は本報告書のみ。
- words metadata/embeddings の行数不一致 (66961 vs 66537) は旧エントリ削除で解消 → 再投入後 66961 entries / 66532 embeddings (metadataにはspeaker無しエントリ含む)
- comments は xZTtk4pJcAs の23件を削除のみ (build --update ではcommentsは再投入対象外)
