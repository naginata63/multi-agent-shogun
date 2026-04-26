# 漫画パネルPNG生成手順（Vertex AI API）

## パラメータ（タスクYAMLから受け取る）
- `${PANELS_JSON}` — panels JSONファイルパス
- `${PANEL_IDS}` — 生成するパネルID（全部 or 指定IDリスト）
- `${OUTPUT_DIR}` — PNG出力先ディレクトリ
- `${GALLERY_HTML}` — ギャラリーHTMLパス（オプション）

## 前提
- Vertex AI ADC認証済み
- google.genai ライブラリ使用可能
- cdp_manga_rules.yaml が参照可能

## 手順

### Step1: panels JSONとルール確認
```bash
cd /home/murakami/multi-agent-shogun
cat ${PANELS_JSON} | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'panels: {len(d[\"panels\"])}')
for p in d['panels']:
    print(f'  {p[\"id\"]}: {p[\"title\"][:40]}')
"
```

### Step2: generate_manga_short.py で生成（必須）

**⚠️ 必ずこのスクリプトを使え。手動でAPIを叩くな。**
このスクリプトはcdp_manga_rules.yaml、ref_images、director_notes、char_prohibitionsを正しくプロンプトに組み込む。

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels ${PANELS_JSON} \
  --output ${OUTPUT_DIR}
```

再生成（既存PNGを上書き）:
```bash
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels ${PANELS_JSON} \
  --output ${OUTPUT_DIR} \
  --no-cache
```

動画生成スキップ（PNGのみ生成）:
```bash
python3 projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py \
  --panels ${PANELS_JSON} \
  --output ${OUTPUT_DIR} \
  --skip-gen  # 既存PNGがある場合スキップ
```

### Step3: 出力確認
```bash
ls -la ${OUTPUT_DIR}/*.png
python3 -c "from PIL import Image; img=Image.open('${OUTPUT_DIR}/$(最初のpanel_id).png'); print(img.size)"
# → (768, 1376) であること
```

### Step4: ギャラリーHTML更新（指定がある場合）
```bash
sed -i "s/\.png\"/\.png?t=$(date +%Y%m%d%H%M%S)\"/" ${GALLERY_HTML}
```

### Step5: 報告
```bash
bash scripts/inbox_write.sh karo \
  "足軽N号、subtask_XXX完了。漫画パネルPNG生成完了（${PANEL_IDS}）。" \
  report_completed ashigaruN
```

## 注意事項
- **generate_manga_short.py を必ず使え。自前でAPI叩くな。**
- 生成は1枚ずつ順番に（並列禁止・APIレート制限回避）
- ref_imagesクォータ制限エラー時はスクリプトが自動でフォールバックする
- ガチャ上限: 殿の指示がない限り各パネル1回
- git commitは不要（work/はgit-ignored）
- ntfyは不要（karoが通知する）
