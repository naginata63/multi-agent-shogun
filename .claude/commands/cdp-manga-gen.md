# CDP漫画パネル生成スキル

## トリガーワード
「パネル生成」「漫画パネル」「CDP生成」「漫画生成」「パネルCDP」

## 概要
パネルJSONとパネルIDを指定し、CDP方式（Gemini UI操作）で漫画パネル画像を生成する。
キャラリファレンス画像の自動選択、プロンプト組み立て、比較ページ生成まで一気通貫。

## 3つの入力ファイル
1. **パネルJSON** — シーン・キャラ・セリフ・リファレンス画像を定義
2. **共通ルールconfig** — `context/cdp_manga_rules.yaml`（スクリプトが自動読み込み）
3. **スクリプト** — `projects/dozle_kirinuki/scripts/cdp_manga_panel.py`

この3つだけで完結する。ルール変更はconfigを編集するだけ。

## 前提条件
- Chrome起動済み: `google-chrome --remote-debugging-port=9222`
- Gemini Pro/Plusにログイン済み
- DISPLAY=:0 (X11)
- `pip install pyyaml`

## 使い方

### 基本（1枚生成）
```bash
python3 projects/dozle_kirinuki/scripts/cdp_manga_panel.py \
  --panels-json <パネルJSONパス> \
  --panel-id <パネルID> \
  --out work/<cmd_id>/
```

### リファレンス画像を手動指定
```bash
python3 projects/dozle_kirinuki/scripts/cdp_manga_panel.py \
  --panels-json <パネルJSONパス> \
  --panel-id <パネルID> \
  --ref-image path/to/ref1.png path/to/ref2.png \
  --out work/<cmd_id>/
```

### 一貫性テスト（3回生成＋比較ページ）
```bash
python3 projects/dozle_kirinuki/scripts/cdp_manga_panel.py \
  --panels-json <パネルJSONパス> \
  --panel-id <パネルID> \
  --count 3 --html \
  --out work/<cmd_id>/
```

## パネルJSON作成ルール（重要）

パネルJSONにCDP生成に必要な情報を**全部含める**こと。スクリプトのハードコードに依存するな。

### 必須フィールド
```json
{
  "id": "panel_06",
  "title": "全力拒否",
  "speaker": "qnly",
  "line": "ハァ？来んなよ",
  "characters": ["qnly", "orafu"],
  "scene_desc": "大きなコマ。おんりーが腕を突き出し威圧的に睨みつける。おらふくんが身を縮めて怯えている",
  "situation": "おんりーの全力拒否 vs おらふの怯え",
  "director_notes": "おんりーアップ（qnly_angry_r2）腕を突き出し威圧。おらふ（orafu_crying_r1）身を縮めて泣きそうな怯え。2人の対比を1コマに。表情で勝負。",
  "ref_image": "シーンスクショのパス",
  "ref_images": [
    "シーンスクショのパス",
    "assets/dozle_jp/character/selected/qnly_angry_r2_rgba.png",
    "assets/dozle_jp/character/selected/orafu_crying_r1_rgba.png"
  ]
}
```

### ref_imagesの構成
1. **シーンスクショ**（場面の雰囲気）
2. **登場キャラ×表情1枚ずつ**（`selected/`から選ぶ）

**全キャラのリファレンスを入れよ。** 入れないとGeminiがキャラの見た目を勝手に想像する。

### director_notes記載ルール
- 表情IDはexpression_design_v5.md参照（r1/r2/r3まで指定）
- おおはらMENはゴーグル（サングラスではない）
- 盾・武器・バケツは描くな（殿指示がない限り）

## 共通ルールconfig（cdp_manga_rules.yaml）

スクリプトにハードコードせず、configに定義する。変更はここだけ。

### 主要ルール（2026-04-03確定）
| ルール | 内容 |
|--------|------|
| リファレンス再現 | 添付画像のキャラの外見・色・髪型・服装を正確に再現 |
| テキスト禁止 | 指定セリフ以外の吹き出し・テキストを追加するな |
| カメラ距離 | 遠景禁止。顔〜上半身アップまたはミドルショット |
| 吹き出し位置 | 中央〜上部に配置 |
| 余白禁止 | 絵で画面全体を隙間なく埋める。白い余白を作るな |
| コマ分割 | scene_descで指示がない限り1枚絵。勝手にコマ分割するな |
| 禁止アイテム | 盾・武器・バケツは持たせるな |
| サイズ | 9:16 portrait, 768x1376px |
| MENゴーグル | MEN登場パネルのみ適用（非登場パネルには入れるな） |

## リファレンス画像の自動選択

### 正式アセットパス
`projects/dozle_kirinuki/assets/dozle_jp/character/selected/`
（v3/v6/v8等のバージョンディレクトリではなく、selectedが正式）

### 選択ロジック
1. パネルJSONの`ref_images`を優先（重複排除あり）
2. `characters`でref_imagesに含まれないキャラのみ → 表情キーワード自動推定 → `selected/`から取得

### 表情推定（キャラ名周辺テキストから判定）
スクリプトはsituation/director_notes/scene_descからキャラ名の周辺テキストを抽出し、キーワードマッチで表情を推定する。全文ではなくキャラごとに分離して判定するため、他キャラの描写に引きずられない。

| 表情 | キーワード例 |
|------|------------|
| angry | 怒り、威圧、睨む、拒否 |
| crying | 泣き、悲しい、涙 |
| troubled | 困り顔、怯え、身を縮め |
| surprise | 驚き、びっくり、衝撃 |
| smug | ドヤ顔、得意げ、自信満々 |
| skeptical | 疑い、困惑、キョトン |
| smile | 笑顔、嬉しい、楽しい |

### フォールバック（configで定義）
1. selected/に指定表情がなければ → 近い表情（troubled→crying→panic_scream等）
2. 近い表情もなければ → CDPで表情画像をその場で生成
3. 全部失敗 → smile_r1に最終フォールバック

### 手動指定 (--ref-image)
`--ref-image` オプションで自動選択を完全に上書き。

## プロンプト組み立て（自動）

スクリプトが以下を自動で組み立てる：

```
【添付画像の説明】添付画像1枚目: シーンスクリーンショット。
添付画像2枚目: おんりーのキャラクター（angry_r2表情）。
添付画像3枚目: おらふくんのキャラクター（crying_r1表情）。

{scene_desc}
{situation}
{director_notes}
{speaker日本語名}のセリフの吹き出し：「{line}」
{共通ルール（configから読み込み）}
{キャラ固有ルール（登場キャラのみ）}
```

**ポイント：**
- キャラ名はプロンプト内で**日本語名に統一**（qnly→おんりー、orafu→おらふくん）。英字キーと日本語名が混在するとGeminiが区別できない
- 添付画像の説明で「N枚目は〇〇のキャラクター」と明記（Geminiにどの画像が誰か伝える）
- 話者名をセリフに付ける（「おんりーのセリフの吹き出し：」）
- 非登場キャラのルール（MENゴーグル等）は入れない

## 成功例（cmd_1085 v5）

P6「ハァ？来んなよ」おんりー＋おらふ。

```bash
python3 projects/dozle_kirinuki/scripts/cdp_manga_panel.py \
  --panels-json work/cmd_1086/panels_test.json \
  --panel-id panel_06 \
  --count 1 \
  --out work/cmd_1086_v5/
```

panels_test.json: ref_imagesにシーンスクショ＋qnly_angry_r2＋orafu_crying_r1の3枚。
結果: キャラ外見一致、1枚絵、セリフ上部、白余白なし。

## 注意事項
- 画像生成はGemini無料枠を消費。ガチャ上限3回
- 毎回新規Geminiセッションで生成（前回の文脈を引き継がない）
- 連続生成時は--interval（デフォルト10秒）で間隔を空ける
- 生成タイムアウトは600秒
- ref_imagesがJSON内とcharacters自動選択で重複する場合は自動排除される
- ウォーターマーク（Gemini ✦マーク）はデフォルトで自動除去される（3パスNS inpaint）
- `--no-watermark-removal` で除去をスキップ可能
- API版（generate_manga_short.py）では✦が付かないため除去不要
