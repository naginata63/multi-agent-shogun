# ドズル社切り抜き動画 サムネ生成手順

ドズル社 + DoZ 系動画のサムネを `generate_thumbnail.py` (Gemini API ベース) で生成する手順。
Day2/Day3/Day5/Day6 で実証済みパターン。

## 関連ファイル

| 種別 | パス |
|------|------|
| **生成スクリプト** | 各 work ディレクトリ内 `thumbnail_xxx/generate_thumbnail.py` (357行・テンプレ流用) |
| **DoZ 6人構成表** | `projects/dozle_kirinuki/context/buzzerbeater_members.yaml` |
| **ドズル社 6人プロファイル** | `projects/dozle_kirinuki/context/member_profiles.yaml` |
| **コラボ立ち絵** | `projects/dozle_kirinuki/assets/collab/{charlotte.jpg,hendy.jpg,tsurugi.png,itoi.png,haseshin.jpeg}` |
| **DoZ 用 oo_men 立ち絵** | `projects/dozle_kirinuki/work/20260411_…/oo_men_goggle_on.png` (Day1 ディレクトリに格納・全 Day で流用) |
| **GCS upload キャッシュ** | 各 thumbnail ディレクトリ内 `gcs_upload_cache_thumbnail.json` |
| **汎用スキル (別ルート)** | `skills/thumbnail/` (make_thumbnail_auto.py・PIL合成版・Gemini不使用版) |

## DoZ ブザービーター 6人 (buzzerbeater_members.yaml)

| キー | 名前 | ハンドル | 種別 |
|------|------|---------|------|
| oo_men | おおはらMEN | @ooharaMEN | ドズル社 |
| charlotte | 島村シャルロット | @Charlotte_Shimamura | コラボ・実写 |
| tsurugi | 柊ツルギ | @HiiragiTsurugi | コラボ・実写 |
| itoi | 絲依とい | @itoitoi_Q | コラボ・実写 |
| hendy | 山下ヘンディー | @TONAHENDY | コラボ・実写 |
| haseshin | HASESHIN | @XxHASESHINxX | コラボ・実写 |

ドズル社 (bon/dozle/qnly/orafu/nekooji) は DoZ 不参加・サムネに含めない。

## generate_thumbnail.py 引数

| 引数 | 用途 |
|------|------|
| `--title` (required) | 上部テロップ |
| `--subtitle` | 下部テロップ |
| `--characters` | キャラキー or **絶対画像パス**カンマ区切り (mix 可) |
| `--hero` | 中央大きく配置キャラ |
| `--bg-image` | 背景画像 |
| `--photo-keys` | 実写扱いキー (コラボメンバー用・カンマ区切り) |
| `--ref-dir` | 参考サムネディレクトリ |
| `--ref-limit` | 参考サムネ最大数 (デフォルト 5) |
| `--output` | 出力ディレクトリ |
| `--count` | 生成枚数 (デフォルト 3) |
| `--style` | energetic / dark / collage |

## サムネ構成 (シリーズ統一)

```
┌──────────────────────────────────┐
│ 【ブザービーター】成長の軌跡!  │  ← --title (上部赤帯)
├──────────────────────────────────┤
│  立ち絵   ECHIDNA      立ち絵   │  ← bg-image に焼き込み済
│  立ち絵   VI層 副題    立ち絵   │
│  立ち絵                立ち絵   │
├──────────────────────────────────┤
│   新たな戦略でボスを倒せ!!     │  ← --subtitle (下部黄色テロップ)
└──────────────────────────────────┘
```

中央のボス名ロゴ + 副題は **背景画像 (bg-image) に既に焼き込み済**。生成スクリプトは中央配置をしない (--title=上部・--subtitle=下部のみ)。

## 実行例 (Day6 エキドナ・cmd_1467)

```bash
python3 generate_thumbnail.py \
  --title '【ブザービーター】成長の軌跡!' \
  --subtitle '新たな戦略でボスを倒せ!!' \
  --characters '/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/20260411_【#DoZ】Doom or Zenithの世界にキターーーーーー！！！！！！！ 【ドズル社／おおはらMEN視点】/oo_men_goggle_on.png,/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/assets/collab/charlotte.jpg,/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/assets/collab/tsurugi.png,/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/assets/collab/itoi.png,/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/assets/collab/hendy.jpg,/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/assets/collab/haseshin.jpeg' \
  --photo-keys 'charlotte,tsurugi,itoi,hendy,haseshin' \
  --bg-image '/home/murakami/ピクチャ/Screenshots/Screenshot from 2026-04-25 11-32-31.png' \
  --output 'projects/dozle_kirinuki/work/20260416_…/thumbnail_echidna/' \
  --count 3 \
  --style energetic \
  --ref-limit 0
```

`--ref-limit 0` は cmd_1467 初回で competitor_thumbs (デフォルト ref) からぼんじゅうる中央配置を学習踏襲した事故を受けて必須化 (鉄則7)。

## 鉄則

1. **DoZ 6人 = oo_men + コラボ5人**: ドズル社 bon/dozle/qnly/orafu/nekooji は DoZ 不参加ゆえ含めない
2. **oo_men 立ち絵は DoZ 専用 ゴーグル ON 版を絶対パスで指定**: CHAR_MAP デフォルト (ゴーグルなし版) では Day シリーズ統一感が崩れる
3. **コラボ5人は --photo-keys で実写指定**: Gemini に photorealism preserve 指示が必要
4. **背景画像 (bg-image) に中央ロゴ焼き込み済前提**: スクリプトは中央配置しない・上部 (--title) と下部 (--subtitle) のみ
5. **3案生成 + viability スコア**: --count 3 で 3 レイアウト出力・最優秀案を thumbnail_final.png として確定
6. **テンプレ流用**: 過去 Day の generate_thumbnail.py をコピーして使う (新規開発不要)
7. **`--ref-limit 0` 必須**: デフォルトの `competitor_thumbs/` (一般ドズル社サムネ) を ref に渡すと Gemini が「ドズル社サムネ = ピンク豚 (ぼん) 中央」パターンを学習・踏襲する。DoZ サムネには **ぼん不参加**ゆえ `--ref-limit 0` で competitor_thumbs を完全 cut。代替: `--ref-dir <doz_thumbs パス>` で DoZ ref 限定使用も可 (4/19 以降の知見)
8. **家老起票時はコマンド全文を steps に strict 明示**: 抽象的「コマンド実行」記述だと足軽が title 引数を動画タイトルに勝手置換する事故が起きる (cmd_1467 初回で「【ブザービーター】成長の軌跡!」が「腹から声が出ない！」に化けた)。inbox 詳細メッセージID参照 or 引数全文転記必須
9. **build_prompt 副作用注意**: `--bg-image` 指定時、スクリプトは Gemini に「1枚目: 背景画像 (...・日本語のサブタイトル文字を含む)」と教える。殿スクショの中央焼き込みロゴと `--subtitle` 引数が競合する可能性あり・テロップ反映が不安定なら build_prompt の `bg_intro` ロジック確認
10. **`--hero <絶対画像パス>` で主役を中央下部に配置（2026-04-25 cmd_1467 v3 確定）**: cmd_1467 v2 では未使用→殿が「おおはらMENが中央下部にいない」と指摘。`--hero <oo_men_goggle_on.png 絶対パス>` 追加で build_prompt が Gemini に「主役は画面前景・中央下部に他より30%大きく」と指示する。`--characters` と `--hero` に同じパス重複指定で OK
11. **「3かい」=「3案 1セット」（殿用語）**: 殿が「3かい再作成」と指示した場合、`--count 3` で **1回コマンド実行**する意味（=1セット）。3セット連続生成（9案）の意味ではない。**1セット生成ごとに殿確認のフロー**を厳守。連続生成は殿確認の機会を奪う事故になる（2026-04-25 17:30 SET B 暴走事案）

## 確定コマンド全文 (Day6 ECHIDNA cmd_1467 v3 / 2026-04-25 17:36 案1採用)

```bash
source ~/.bashrc && cd "projects/dozle_kirinuki/work/20260416_【#DoZ】6日目 …MEN視点】/thumbnail_echidna/" && \
python3 generate_thumbnail.py \
  --title '【ブザービーター】成長の軌跡!' \
  --subtitle '新たな戦略でボスを倒せ!!' \
  --characters 'projects/dozle_kirinuki/work/20260411_…/oo_men_goggle_on.png,projects/dozle_kirinuki/assets/collab/charlotte.jpg,projects/dozle_kirinuki/assets/collab/tsurugi.png,projects/dozle_kirinuki/assets/collab/itoi.png,projects/dozle_kirinuki/assets/collab/hendy.jpg,projects/dozle_kirinuki/assets/collab/haseshin.jpeg' \
  --hero 'projects/dozle_kirinuki/work/20260411_…/oo_men_goggle_on.png' \
  --photo-keys 'charlotte,tsurugi,itoi,hendy,haseshin' \
  --bg-image '/home/murakami/ピクチャ/Screenshots/Screenshot from 2026-04-25 11-32-31.png' \
  --output . --count 3 --style energetic --ref-limit 0
```

引数の役割（要点）:
- `--hero <oo_men絶対パス>`: 中央下部30%大きく配置 ← v3 で必須化
- `--photo-keys`: コラボ5人 photorealism 保持
- `--bg-image`: 中央ロゴ焼き込み済スクショ（v3 では中央配置しない）
- `--ref-limit 0`: competitor_thumbs を ref から完全 cut（鉄則7）
- `--count 3`: **1回コマンド実行で3案 = 1セット**（鉄則11）

## 既知ケース

| Day | ボス | thumbnail dir | 副題 (中央) | 確定 |
|-----|------|--------------|-----------|------|
| Day2 | OSIRIS | `20260412_…/thumbnail/` | 第二層 迷宮を統べる者 | - |
| Day3 | MOLOCH | `20260413_…/thumbnail_moloch/` | (要確認) | - |
| Day5 | ZEPHYRUS | `20260415_…/thumbnail_zephyrus/` | V層 死期を運びし翼 | - |
| Day6 | ECHIDNA | `20260416_…/thumbnail_echidna/` | VI層 破滅の始祖 | **2026-04-25 v3案1 (--hero oo_men) thumbnail_final.png** |
