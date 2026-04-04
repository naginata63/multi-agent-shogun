---
name: expression-gen
description: |
  ドズル社メンバーの表情差分画像をGemini画像生成APIで生成する。
  元立ち絵確認→generate_v8.py/v9実行→白黒バリアント生成→品質確認まで一貫して担当。
  「表情差分生成」「expression-gen」「立ち絵表情」「Gemini画像生成」「/expression-gen」で起動。
  Do NOT use for: サムネイル合成（それは/thumbnailを使え）。Do NOT use for: 音声・SRT処理（それは/video-pipelineを使え）。
argument-hint: "[member_key] [version]"
allowed-tools: Bash, Read
---

# /expression-gen — 表情差分生成スキル

## North Star

ドズル社メンバー全員の表情差分白黒画像（9表情×3バリアント）をGemini APIで生成し、
`work/expression_gen/v{N}/white/` と `work/expression_gen/v{N}/black/` に格納すること。

## 前提知識

### スクリプトパス（プロジェクトルート相対）

| スクリプト | パス |
|-----------|------|
| v8（5メンバー用） | `projects/dozle_kirinuki/work/expression_gen/generate_v8.py` |
| v9（ネコおじ用） | `projects/dozle_kirinuki/work/expression_gen/generate_v9_nekooji.py` |
| 表情設計書 | `projects/dozle_kirinuki/context/expression_design_v5.md` |
| メンバープロファイル | `projects/dozle_kirinuki/context/member_profiles.yaml` |
| 元立ち絵 | `projects/dozle_kirinuki/assets/dozle_jp/character/` |

### Gemini モデル

```
gemini-3.1-flash-image-preview
```

- **注意**: 正しいモデル名は `context/gemini_api_registry.json` を参照のこと（名称変更があり得る）
- 環境変数: `GEMINI_API_KEY`（必ず `source ~/.bashrc &&` でプリフィックス）
- レート制限: 生成後に適切なsleepを入れること（スクリプト内で処理済み）

### メンバーキーと担当スクリプト

| キー | 名前 | 担当スクリプト |
|------|------|--------------|
| dozle | ドズル | generate_v8.py |
| bon | ぼんじゅうる | generate_v8.py |
| qnly | おんりー | generate_v8.py |
| orafu | おらふくん | generate_v8.py |
| oo_men | おおはらMEN | generate_v8.py |
| nekooji | ネコおじ | generate_v9_nekooji.py |

### 表情カテゴリ（9種）

`angry` / `crying` / `embarrassed` / `scheming` / `skeptical` / `smile` / `smug` / `surprise` / `troubled`

各カテゴリに r1（弱）、r2（中）、r3（強）の3バリアント。

### 出力ディレクトリ規則

```
projects/dozle_kirinuki/work/expression_gen/v{N}/
  white/   # 白背景（背景白・線画白黒）
    {member_key}_{expression}_{r1|r2|r3}.png
  black/   # 黒背景（暗色合成用）
    {member_key}_{expression}_{r1|r2|r3}.png
```

例: `dozle_smile_r2.png`、`bon_angry_r3.png`

バージョン: 現在の本番用は v8（5メンバー）＋v9（nekooji）。次世代はv{N+1}として作成。

## 実行手順

### Step 1: 元立ち絵の確認

```bash
ls projects/dozle_kirinuki/assets/dozle_jp/character/
# dozle.png, bonjour.png, qnly.png, orafu.png, oo_men.png 等が存在すること
```

表情設計書を読む（キャラクター性・表情の詳細定義）:
```bash
cat projects/dozle_kirinuki/context/expression_design_v5.md
```

### Step 2: 既存生成ファイルの確認

```bash
ls projects/dozle_kirinuki/work/expression_gen/v8/white/ 2>/dev/null | wc -l
ls projects/dozle_kirinuki/work/expression_gen/v9/white/ 2>/dev/null | wc -l
# 既存があればスキップ可。無い場合は生成へ
```

### Step 3: 5メンバー生成（generate_v8.py）

```bash
cd /home/murakami/multi-agent-shogun
source ~/.bashrc && source projects/dozle_kirinuki/venv/bin/activate

python3 projects/dozle_kirinuki/work/expression_gen/generate_v8.py
```

全5メンバー×9表情×3バリアント×白黒 = **270枚** 生成。
長時間処理のため、出力ディレクトリを監視しながら進捗確認:

```bash
ls projects/dozle_kirinuki/work/expression_gen/v8/white/ | wc -l
# 順次増加していくこと
```

### Step 4: ネコおじ生成（generate_v9_nekooji.py）

```bash
source ~/.bashrc && source projects/dozle_kirinuki/venv/bin/activate

python3 projects/dozle_kirinuki/work/expression_gen/generate_v9_nekooji.py
```

ネコおじは1メンバー×9表情×3バリアント×白黒 = **54枚** 生成。

### Step 5: 品質確認

枚数確認:
```bash
ls projects/dozle_kirinuki/work/expression_gen/v8/white/ | wc -l
# 期待値: 135枚（5メンバー×27）
ls projects/dozle_kirinuki/work/expression_gen/v9/white/ | wc -l
# 期待値: 27枚（nekooji×27）
```

サンプル目視確認（各メンバー1枚ずつ）:
```bash
ls projects/dozle_kirinuki/work/expression_gen/v8/white/dozle_smile_r2.png
ls projects/dozle_kirinuki/work/expression_gen/v8/white/bon_angry_r1.png
ls projects/dozle_kirinuki/work/expression_gen/v9/white/nekooji_surprise_r3.png
```

ファイルサイズ確認（0バイトはNG）:
```bash
find projects/dozle_kirinuki/work/expression_gen/ -name "*.png" -size 0
# 出力が空（0バイトファイルなし）であること
```

## 重要ルール

1. **GEMINI_API_KEY必須** — `source ~/.bashrc &&` を必ずプリフィックスする
2. **中間成果物は保存必須** — 生成済みPNGは消去しない。再生成は高コスト
3. **generate_v8.pyとv9は別スクリプト** — 一方が終わってから他方を実行
4. **バージョン管理** — 既存v8/v9を上書きしない。新バージョンは v{N}ディレクトリを新規作成
5. **0バイトファイルは即報告** — 生成失敗の証拠。原因調査してカロに報告

## 報告フォーマット

```
## expression-gen 完了報告
- v8（5メンバー）white: <N>枚 / black: <N>枚
- v9（nekooji）white: <N>枚 / black: <N>枚
- 合計: <N>枚
- 0バイトファイル: なし / <あれば詳細>
- 出力パス: projects/dozle_kirinuki/work/expression_gen/v{N}/
```
