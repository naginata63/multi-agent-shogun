# DoZセマンティック検索基盤構築 手順 (cmd_1421)

## 前提
- 既存スクリプト: `projects/dozle_kirinuki/scripts/subtitle_semantic_index.py`
- 新規.py作成禁止。既存スクリプトを拡張のみ
- Vertex AI API: `source config/vertex_api_key.env` 必須（~/.bashrcのGEMINI_API_KEYは期限切れ）
- Embedding モデル: `gemini-embedding-2-preview`（location=global）
- BQ dataset location: asia-northeast1
- BQ project: gen-lang-client-0119911773

## SRTファイル一覧（8本）

| 日数 | video_id | SRTパス |
|------|----------|---------|
| 1 | 0EMTgf-ivWw | `projects/dozle_kirinuki/work/20260411_【#DoZ】Doom or Zenithの世界にキターーーーーー！！！！！！！ 【ドズル社／おおはらMEN視点】/0EMTgf-ivWw.ja.srt` |
| 2 | Sl7fdkCxqyg | `projects/dozle_kirinuki/work/20260412_【#DoZ】2日目  誰も死なせないよ　だって私はヒーラーだもの【ドズル社／おおはらMEN視点】/Sl7fdkCxqyg.ja.srt` |
| 3 | Bd8M2VAsm6k | `projects/dozle_kirinuki/work/20260413_【#DoZ】3日目 万物の破壊者おおはらMEN　いまだにゴブリンは倒せず【ドズル社／おおはらMEN視点】/Bd8M2VAsm6k.ja.srt` |
| 4 | vFfVavC_y5M | `projects/dozle_kirinuki/work/20260414_【#DoZ】4日目 おれは100万DOZをかき集めるよ【ドズル社／おおはらMEN視点】/vFfVavC_y5M.ja.srt` |
| 5 | gszoq-2br2o | `projects/dozle_kirinuki/work/20260415_【#DoZ】5日目 知ってるか？ヒーラーはな…絶対に仲間を見捨てちゃいけねぇのさ【ドズル社／おおはらMEN視点】/gszoq-2br2o.ja.srt` |
| 6 | t7JJlTDACyc | `projects/dozle_kirinuki/work/20260416_【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】/t7JJlTDACyc.ja.srt` |
| 7 | YJ3TVMe8qAY | `projects/dozle_kirinuki/work/20260417_【#DoZ】7日目 ヒーラーは固きゃ固いほどええねん【ドズル社／おおはらMEN視点】/YJ3TVMe8qAY.ja.srt` |
| 8 | RXMQraU2f54 | `projects/dozle_kirinuki/work/20260418_【#DoZ】8日目 ヒーラーは大声で叫べば叫ぶほど回復量は上がるんだ【ドズル社／おおはらMEN視点】/RXMQraU2f54.ja.srt` |

## Step1: subtitle_semantic_index.py 拡張

既存スクリプト（503行）を読んで以下を追加:

### 追加機能
a) `--input-srt` オプション: SRTファイルを直接指定（既存は merged_*.json 前提）
b) `--dataset` オプション: BQデータセット名を引数化（デフォルト=既存の dozle_subtitle_semantic）
c) SRTパーサ: 各字幕エントリを時刻付きで読み、30秒チャンクにグルーピング
d) 追加メタ列: `video_day`（INT64, 1-8）、`video_title`（STRING）、`source`（STRING, 固定='youtube_auto_caption'）
e) `--video-day`、`--video-title` 引数を追加

### BQテーブルスキーマ（既存と互換性に注意）
```
chunk_id INT64（必須）
video_id STRING（必須）
video_day INT64（1-8）
video_title STRING
start_ms INT64
end_ms INT64
text STRING
embedding FLOAT64 REPEATED
source STRING
```

## Step2: DoZ専用BQリソース作成

```bash
source config/vertex_api_key.env

# データセット作成
bq mk --dataset --location=asia-northeast1 gen-lang-client-0119911773:doz_subtitle_semantic

# テーブル作成（スキーマJSONを先に作成してから）
bq mk --table gen-lang-client-0119911773:doz_subtitle_semantic.chunks \
  chunk_id:INT64,video_id:STRING,video_day:INT64,video_title:STRING,start_ms:INT64,end_ms:INT64,text:STRING,embedding:FLOAT64,source:STRING
```

※ embeddingは REPEATED 型。bq mk のスキーマ定義で `embedding:FLOAT64` は array対応しない場合、
JSON スキーマファイル経由で作成すること。

## Step3: 8本SRTをDoZ専用BQに登録

```bash
source config/vertex_api_key.env

# 1日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260411_【#DoZ】Doom or Zenithの世界にキターーーーーー！！！！！！！ 【ドズル社／おおはらMEN視点】/0EMTgf-ivWw.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id 0EMTgf-ivWw --video-day 1 \
  --video-title "【#DoZ】Doom or Zenithの世界にキターーーーーー！！！！！！！"

# 2日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260412_【#DoZ】2日目  誰も死なせないよ　だって私はヒーラーだもの【ドズル社／おおはらMEN視点】/Sl7fdkCxqyg.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id Sl7fdkCxqyg --video-day 2 \
  --video-title "【#DoZ】2日目 誰も死なせないよ だって私はヒーラーだもの"

# 3日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260413_【#DoZ】3日目 万物の破壊者おおはらMEN　いまだにゴブリンは倒せず【ドズル社／おおはらMEN視点】/Bd8M2VAsm6k.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id Bd8M2VAsm6k --video-day 3 \
  --video-title "【#DoZ】3日目 万物の破壊者おおはらMEN いまだにゴブリンは倒せず"

# 4日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260414_【#DoZ】4日目 おれは100万DOZをかき集めるよ【ドズル社／おおはらMEN視点】/vFfVavC_y5M.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id vFfVavC_y5M --video-day 4 \
  --video-title "【#DoZ】4日目 おれは100万DOZをかき集めるよ"

# 5日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260415_【#DoZ】5日目 知ってるか？ヒーラーはな…絶対に仲間を見捨てちゃいけねぇのさ【ドズル社／おおはらMEN視点】/gszoq-2br2o.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id gszoq-2br2o --video-day 5 \
  --video-title "【#DoZ】5日目 知ってるか？ヒーラーはな…絶対に仲間を見捨てちゃいけねぇのさ"

# 6日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260416_【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】/t7JJlTDACyc.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id t7JJlTDACyc --video-day 6 \
  --video-title "【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？"

# 7日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260417_【#DoZ】7日目 ヒーラーは固きゃ固いほどええねん【ドズル社／おおはらMEN視点】/YJ3TVMe8qAY.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id YJ3TVMe8qAY --video-day 7 \
  --video-title "【#DoZ】7日目 ヒーラーは固きゃ固いほどええねん"

# 8日目
python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py build \
  --input-srt "projects/dozle_kirinuki/work/20260418_【#DoZ】8日目 ヒーラーは大声で叫べば叫ぶほど回復量は上がるんだ【ドズル社／おおはらMEN視点】/RXMQraU2f54.ja.srt" \
  --dataset doz_subtitle_semantic \
  --video-id RXMQraU2f54 --video-day 8 \
  --video-title "【#DoZ】8日目 ヒーラーは大声で叫べば叫ぶほど回復量は上がるんだ"
```

レート制限: RATE_LIMIT_SLEEP=3.0秒（既存設定尊重）。8本合計で約20〜25分かかる。

## Step4: 検索テスト（3クエリ以上）

```bash
source config/vertex_api_key.env

python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py search \
  "ヒーラーが回復する場面" --dataset doz_subtitle_semantic

python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py search \
  "おおはらMENが絶叫する" --dataset doz_subtitle_semantic

python3 projects/dozle_kirinuki/scripts/subtitle_semantic_index.py search \
  "DOZ 100万" --dataset doz_subtitle_semantic
```

各クエリで `video_id + timestamp + text` が返ることを確認。

## Step5: git commit

```bash
git add projects/dozle_kirinuki/scripts/subtitle_semantic_index.py
git add shared_context/procedures/doz_semantic_search.md
git commit -m "feat(cmd_1421): DoZセマンティック検索基盤構築 subtitle_semantic_index.py SRT対応拡張"
```

## Step6: 軍師QC + 完了報告

```bash
bash scripts/inbox_write.sh gunshi \
  "足軽5号、subtask_1421a完了。DoZセマンティック検索BQ登録完了（{N}チャンク）。QCせよ: 3クエリ検索結果の妥当性・ノイズ率確認。dataset=doz_subtitle_semantic" \
  qc_request ashigaru5

bash scripts/inbox_write.sh karo \
  "足軽5号、subtask_1421a完了。subtitle_semantic_index.py拡張+DoZ8本BQ登録({N}チャンク)+検索テスト済。軍師QC依頼済。" \
  report_completed ashigaru5
```
