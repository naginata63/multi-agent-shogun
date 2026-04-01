# cmd_1037 最終サマリー

## 概要
ドズル社YouTubeチャンネルの2025-04-01以降公開動画に対する
字幕取得・セマンティックインデックス構築パイプライン

## 実行期間
2026-04-01

## 最終結果

| 項目 | 数値 |
|------|------|
| 対象動画数（CSV総数） | 844本 |
| インデックス済み動画数 | **822本** |
| 字幕なし（スキップ）動画数 | **22本** |
| 総チャンク数 | **46,292チャンク** |
| embeddings.jsonサイズ | 約2.7GB |
| 使用APIキー | config/vertex_api_key.env (VERTEX_API_KEY) |

## バッチ処理内訳

| バッチ | 処理本数 | 成功 | 失敗 |
|--------|----------|------|------|
| batch01〜batch11 | 各30本 | - | - |
| batch12 | 30本 | 29 | 1（XA-7u0UumYE） |
| batch13 | 30本 | 29 | 1（Jg7SPi8OPWw） |
| batch14〜batch21 | 各30本 | - | - |
| batch22 | 30本 | 29 | 1（3_mFDz1EzpM） |
| batch_final | 96本 | 95 | 1（Ms6iyVnRXTk） |
| **合計** | **844本** | **822本** | **22本** |

## 字幕なし動画リスト（fail_list.txt・22件）
```
-RZeHghiHTU, 14zhZ3eEpjA, 3_mFDz1EzpM, 9ZcwlyIwGCI, FP0eWQDwb9o
HxNnXRaBF7k, Jg7SPi8OPWw, Ms6iyVnRXTk, RIWieneMVQc, XA-7u0UumYE
Zh0YxDjlw24, aLKBtBSsRH0, b5ny1htDZlM, fHz3f_VcMyQ, j_KVuabNrFg
mVLyXpsvmbI, n-wtokssJJs, nW8YR_7XUQQ, pla8j_sLe7Y, s29lAXxt1-Q
sCaLSchxRSk, x15ZACYaRxg
```

## 成果物ファイル

| ファイル | 場所 |
|----------|------|
| インデックスレジストリ | `projects/dozle_kirinuki/reports/semantic_index_registry.yaml` |
| 埋め込みデータ | `projects/dozle_kirinuki/work/subtitle_index/embeddings.json` |
| 字幕ファイル | `projects/dozle_kirinuki/work/yt_subs/` |
| 失敗リスト | `work/cmd_1037/fail_list.txt` |
| バッチログ | `work/cmd_1037/batch*_log.yaml` |

## 技術仕様
- 字幕取得: `yt-dlp --write-auto-sub --sub-lang ja --sub-format srt`
- 変換: `subtitle_semantic_index.py import_srt`
- インデックス構築: `subtitle_semantic_index.py build` (Vertex AI Embeddings API)
- チャンクサイズ: 約56チャンク/動画（平均）

## 備考
- バッチ処理中、embeddings.jsonは複数回チェックポイントリセット（正常動作）
- 字幕なし動画はYouTube側で自動字幕生成が無効化されているもの
- git commit済み（サブモジュール + 親リポジトリ）
