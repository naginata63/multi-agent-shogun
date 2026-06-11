# cmd_1631 完了報告書 — xZTtk4pJcAs 話者実名化 + index同期

- **報告日時**: 2026-06-11T17:21:36
- **作業者**: ashigaru5
- **タスクID**: subtask_1631_index_v2

## 実行概要

scene_index_v2 から xZTtk4pJcAs の旧embedding（A-F話者ラベル）を削除 → build --update で実名版再投入を試行。

## Acceptance Criteria 検証

| 項目 | 結果 | 備考 |
|------|------|------|
| info 話者一覧に A/B/C/D/E/F が存在しない | **PASS** | 話者: bon, dozle, external_collab, nekooji, oo_men, orafu, qnly, ramerry, unknown |
| query で xZTtk4pJcAs 関連に実名話者が返る | **FAIL** | xZTtk4pJcAs が index に不在（Gemini rate limitで再embedding未完了） |
| audit で xZTtk4pJcAs=quality_status:ok | **FAIL** | index_missing（同上） |
| 完了報告書作成 | **PASS** | 本ファイル |

## 実行詳細

### Step 1: 旧データ削除（完了）

- **words**: metadata.json から xZTtk4pJcAs 434件除去 + 444 orphan entries除去 → 66527 → 66521 entries
- **chunks**: chunks_metadata.json から xZTtk4pJcAs 2件除去 + 86 orphan entries除去 → 12318 → 12316 entries
- **comments**: xZTtk4pJcAs 0件（既に不在）
- merged JSON (merged_xZTtk4pJcAs.json) は既に実名話者で修正済み: `dozle, bon, orafu, qnly, oo_men`

### Step 2: build --update（部分的失敗）

2回実行したが、どちらも Gemini 429 rate limit で大量の embedding 生成失敗:

| 回 | words新規 | words成功 | chunks新規 | chunks成功 | zero vectors |
|----|-----------|-----------|------------|------------|-------------|
| 1回目 | 21678 | ~207 (残りorphan) | 4218 | ~3033 | 1000 |
| 2回目 | 20451 | ~205 (残りorphan) | 2888 | ~1722 | 700 |

**結果**: xZTtk4pJcAs の 434 words + 85 chunks は全て metadata に保存されたが、embedding は全て未生成（orphan zone）。trim 処理で除去されたため、現在 index に xZTtk4pJcAs は不在。

### Step 3: orphan 除去・整列修正（完了）

metadata/embeddings の行数不一致を解消:
- Words: 87195 → 66949 (20246 orphans trimmed)
- Chunks: 16237 → 14071 (2166 orphans trimmed)

## info 出力全文（最終状態）

```
=== scene_index_v2 情報 ===
  build_time: 2026-06-11T17:18:55.228025
  n_word_segments: 87195  (build_info上の表示値・实际は66949)
  n_chunk_segments: 16237  (build_info上の表示値・实际は14071)
  n_videos: 93

[words インデックス]
  shape: (66949, 3072)
  動画数: 70
  話者: ['bon', 'dozle', 'external_collab', 'nekooji', 'oo_men', 'orafu', 'qnly', 'ramerry', 'unknown']

[chunks インデックス]
  shape: (14071, 3072)
  動画数: 82
  話者: ['bon', 'dozle', 'external_collab', 'nekooji', 'oo_men', 'orafu', 'qnly', 'ramerry', 'unknown']
  掛け合いスコア: max=3.704, avg=0.394

[comments インデックス]
  shape: (2603, 3072)
  動画数: 66
  comment_density: max=32, avg=2.2
```

## query 結果

```
query 'おじいちゃん' --top 5:
→ 実名話者(bon, dozle, nekooji, orafu, oo_men)でhit。A-F話者0件 ✅
※ xZTtk4pJcAs は現在indexに不在
```

## audit 結果

```
ok: 74
violation_alphabet: 0  ← A-F話者撲滅確認 ✅
index_missing: 10355
xZTtk4pJcAs: index_missing (再embedding未完了)
```

## バックアップ

`data/scene_index_v2/backup_before_1631/` に元の4ファイルを保存済み。

## 次に必要なアクション

1. **Gemini rate limit回復後（~1時間後）に以下を実行**:
   ```bash
   python3 scripts/scene_search_v2.py build --update --mode both
   # その後 orphan trim:
   python3 -c "import json,numpy as np,pathlib; p=pathlib.Path('data/scene_index_v2'); m=json.loads((p/'metadata.json').read_text()); e=np.load(str(p/'embeddings.npy')); (p/'metadata.json').write_text(json.dumps(m[:e.shape[0]],ensure_ascii=False)); print(f'trimmed {len(m)}->{e.shape[0]}')"
   # 同様に chunks_metadata.json も
   ```
2. **build後の確認**:
   ```bash
   python3 scripts/scene_search_v2.py info  # xZTtk4pJcAs 93動画確認
   python3 scripts/scene_search_v2.py query 'ダムを埋める' --top 5
   python3 scripts/audit_video_index_consistency.py --index-dir data/scene_index_v2 --csv projects/dozle_kirinuki/data/dozle_video_list.csv
   ```
3. **build script修正検討**: embedding生成失敗時にmetadataも除外する仕様にすべき（現在はmetadataだけ残りorphan化する）

## 備考

- data/scene_index_v2/ は .gitignore 済みのため、index更新はローカルのみ。git commit は本報告書のみ。
- build_info.json の n_word_segments / n_chunk_segments は旧値のまま（build scriptが上書きしない場合あり）。
