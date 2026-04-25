# 4視点シーン切替 MIX 手順

複数視点動画を「シーンごとに視点を切り替える」方式で MIX する手法。
4視点同時表示 (2x2 grid・multi_view_sync.md) と対比的なアプローチ。

## 適用ケース
- DoZ シリーズ等のチーム配信動画で、視点を時系列で切り替えて見せる
- 1動画内に複数戦闘を含む場合 (ボス1戦目+8戦目 等)

## 関連手順
- 音声同期: `multi_view_sync.md` (sync_multi_videos.py + 二重チェック)
- シーン連結: cmd_1424 zephyrus_v3.sh (segA→segB 映像連続+テロップ瞬時切替)

## 実装鉄則

### 1. 各 seg 独立 MIX → concat 結合 (一気エンコ回避)
長時間 (30分+) を一気に MIX エンコすると時間かかる。短い単位で MIX → 無劣化 concat 結合。

```
seg1戦目.mp4 (4視点MIX 独立完成)
  + seg8戦目.mp4 (4視点MIX 独立完成)
  → ffmpeg concat -c copy → final.mp4 (瞬時)
```

### 2. メイン視点音声方式
画面に出ている視点の音声を採用 (時間ごと audio stream 切替)。
ffmpeg filter_complex で時間条件指定。
**4画面 grid 表示中は MEN 音声** (基準視点の音声を採用)。

cmd_1424 amix=normalize=0 とは別アプローチ (こちらは複数視点 mix)。

### 3. 視点切替パターン
- 最初/最後: 基準視点固定 (例: MEN)
- 中間: 他視点バリエーション (charlotte/hendy/tsurugi)
- たまに 4画面 grid (盛り上がりシーン)
- 30〜60秒の機械的切替+盛り上がり判断 (足軽判断)

### 4. 右上テロップ (seg ごと)
各 seg にボス名+戦闘番号テロップ表示 (ffmpeg drawtext で時間条件)。
例: 「エキドナ(初戦)」「エキドナ(8戦目)」

### 5. 境界 SE+トランジション
seg境界 (試合間) の数秒のみ再エンコで全体高速維持。
- wipeleft + sceneswitch1 (テンポ良い)
- crossfade + sceneswitch2 (滑らか)
- cut_black + sfx_don_impact (劇的)
- 定義: `projects/dozle_kirinuki/context/selected_json_v2_spec.md`

### 6. 視点テロップは不要
「MEN視点」「シャルロット視点」等の視点名表示は煩い・非表示推奨。
切替自体で視点が変わったことは伝わる。

## 既知ケース

| cmd | 動画 | 構成 | 音声 | 境界処理 |
|-----|------|------|------|---------|
| cmd_1424 | Day5 ゼピュロス v3 | segMeeting+segBossA+segBossB+outro | amix=normalize=0 (複数視点 mix) | A→B 映像連続+テロップ瞬時切替 |
| cmd_1464 | Day6 エキドナ 1+8戦目 | seg1戦目+seg8戦目 (独立MIX→concat) | メイン視点音声 (時間ごと切替・4画面時 MEN) | wipeleft + sceneswitch1 |

## acceptance_criteria 標準テンプレ（動画系cmd発令時必須）

家老が動画系cmd（視点切替MIX・4画面MIX等）のタスクYAMLを起票する際、以下の検証条件を acceptance_criteria に必ず含めよ。
これらが欠落していると軍師QCが形骸化する（cmd_1464教訓：ffprobe/API確認のみでPASS→殿が規格逸脱発見）。

```yaml
acceptance_criteria:
  - 視点切替パターン: 鉄則3（最初/最後 基準視点固定 + 中間バリエーション）準拠の視覚確認
  - 右上テロップ: 鉄則4「<ボス名>(<戦闘番号>)」形式の視覚確認
  - seg境界: wipeleft+sceneswitch1 等 selected_json_v2_spec.md 準拠
  - 軍師QC: mpv --speed=2.0 で実視聴必須 (ffprobe単独不可)
  - sync_record.yaml: multi_view_sync.md Step 7 準拠で提出
```

### 1戦目シンプルパターン（短いseg特例）

1戦目が短いseg（≤200秒目安）の場合、完全な視点バリエーションを適用すると逆に不自然になる。
この場合、**MEN→4画面→MEN** のシンプルパターンでよい（殿指示 cmd_1478 の恒久化）。

```
1戦目 (短seg):
  MEN固定 → [盛り上がり] 4画面grid → MEN固定
  ※ 視点バリエーション（charlotte/hendy等）への切替は不要
  ※ 音声もMEN固定で問題なし
```

判定基準: seg尺 ≤ 200秒 かつ 戦闘が1セット → シンプルパターン適用

## 既知ケース（更新）

| cmd | 動画 | 構成 | 音声 | 境界処理 | 備考 |
|-----|------|------|------|---------|------|
| cmd_1424 | Day5 ゼピュロス v3 | segMeeting+segBossA+segBossB+outro | amix=normalize=0 (複数視点 mix) | A→B 映像連続+テロップ瞬時切替 | |
| cmd_1464 | Day6 エキドナ 1+8戦目 | seg1戦目+seg8戦目 (独立MIX→concat) | メイン視点音声 (時間ごと切替・4画面時 MEN) | wipeleft + sceneswitch1 | cmd_1464 QC形骸化の教訓 |
| cmd_1478 | Day6 エキドナ 修正版 | seg1戦目(シンプル)+seg8戦目(通常) | メイン視点音声 | wipeleft + sceneswitch1 | 1戦目シンプルパターン適用1号 |

## 鉄則
1. **長時間一気エンコ回避** — seg ごと独立 MIX → concat 結合
2. **境界処理は短時間再エンコ** — 数秒のみ・全体に影響しない
3. **視点切替は機械的+判断併用** — 完全自動でも完全手動でもなく、足軽が両方使う
4. **音声は 1 方式に絞る** — メイン視点切替 or amix のどちらかに統一 (混在禁止)
5. **境界 SE/transition 定義は selected_json_v2_spec.md 参照** — 新規定義は同ファイル拡張
6. **master/telop 二段生成必須** — テロップ修正コスト数時間→数十分に短縮 (cmd_1486)
   - master.mp4 = テロップなしの完成形MIX動画 (sync・concat・transition全て適用済)
   - with_telop.mp4 = master.mp4 に ffmpeg drawtext で右上テロップ等を後付け1pass
   - アップロード対象は with_telop.mp4 だが、master.mp4 は永続保管 (削除禁止)
   - テロップ修正発生時: master.mp4 から再 drawtext で with_telop_v2.mp4 を生成 (4視点合成は再実行禁止)
   - 元素材 (oo_men_*.mp4 等) に既存テロップが入っている場合は素材選定からやり直し (既存テロップ上に重ね描き禁止)
   - 詳細手順: `shared_context/procedures/master_telop_two_stage.md`
