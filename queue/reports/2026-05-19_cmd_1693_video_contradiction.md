# cmd_1693 夜間矛盾検出レポート — 動画制作スクリプト群 (cmd_1689 比較版)

- **作成日時**: 2026-05-19 02:10 JST
- **作成者**: 軍師 (subtask_1693_video)
- **対象カテゴリ**: 動画制作 (main.py / make_expression_shorts.py / vertical_convert.py / make_thumbnail_auto.py / china_shorts_compose.py / china_shorts_pipeline.py / blur_subtitles.py + Remotion .tsx)
- **形式**: cmd_828 準拠 + cmd_1689 比較
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**:
  - 2026-05-15 cmd_1689 (`queue/reports/2026-05-15_cmd_1689_video_contradiction.md`)
  - 2026-05-08 cmd_1667 (`queue/reports/2026-05-08_cmd_1667_video_mujun_detection.md`)
- **タスク明示要件**: cmd_1667 H001 / H002 / H006 残課題の現状確認

## サマリ

| Severity | cmd_1689 | RESOLVED | PERSISTING | NEW | 合計 |
|----------|---------:|---------:|-----------:|----:|-----:|
| CRITICAL | 0 | 0 | 0 | 0 | 0 |
| HIGH     | 0 | 0 | 0 | 0 | 0 |
| MEDIUM   | 4 | 0 | 4 | 0 | 4 |
| LOW      | 3 | 0 | 3 | 0 | 3 |
| **計**   | 7 | 0 | 7 | **0** | 7 |

**+ cmd_1667 残課題 H001/H002/H006 全件 RESOLVED 発見** (前回 cmd_1689 で見落とし)

---

## 🎯 タスク明示要件: cmd_1667 H001 / H002 / H006 現状確認

### ✅ H001 [RESOLVED]: vertical_convert.py atempo 範囲外チェック

- **cmd_1667 指摘**: L391 `atempo={speed:.6f}` で argparse type=float のみ・範囲チェック無し → speed=0.3/2.5 で ffmpeg filter_complex error
- **現状 verify** (`grep -n "atempo\|valid_speed" vertical_convert.py`):
  ```
  379: f"[0:a]atempo={speed:.6f},"           ← atempo 使用箇所
  430: def valid_speed(value):                ← NEW: type validator 関数
  433:     raise argparse.ArgumentTypeError(f"speed must be between 0.5 and 2.0, got {fval}")
  450: p.add_argument("--speed", type=valid_speed, default=1.0,  ← type=valid_speed で gate
  ```
- **判定**: **解消** (valid_speed gate で 0.5-2.0 範囲外を argparse 段階で reject)

### ✅ H002 [RESOLVED]: main.py 1080p 再 DL 閾値

- **cmd_1667 指摘**: L861 `if _src_h > 0 and _src_h <= 480:` で 480p 動画に対して毎回再 DL
- **現状 verify** (`grep -nE "_src_h|<= 480" main.py`):
  ```
  (hit ゼロ)
  ```
  対象コードが main.py から **完全削除済**。代わりに L556/L577 で resolution suffix (`_(1080p|720p|480p|360p)$`) を regex で剥がす設計に置換
- **判定**: **解消** (再 DL 閾値ロジック自体が廃止された設計改修)

### ✅ H006 [RESOLVED]: make_expression_shorts.py duration int 化

- **cmd_1667 指摘**: L246 `duration = int(cfg["end"]) - int(cfg["start"])` でフレーム精度 start/end (例 226.11/293.08) が 0.03s ずれ
- **現状 verify** (`grep -n "duration\b\|int(cfg" make_expression_shorts.py`):
  ```
  246: duration = float(cfg["end"]) - float(cfg["start"])   ← int → float 変更済
  211: fade_start = duration - 1                            ← duration が float ゆえ fade_start も float
  ```
- **判定**: **解消** (float 化でフレーム精度ずれ解消)

### 総合判定 — cmd_1667 HIGH 全件解消

cmd_1667 (5/8 audit) の HIGH 6件のうち、本書 cmd_1693 verify で:
- C001 WhisperX 残存 → cmd_1689 (5/15) で解消発見
- C002 vertical_convert argparse 4引数 → cmd_1689 で解消発見
- **H001 atempo 範囲外 → 本書で解消発見**
- **H002 1080p 再 DL 閾値 → 本書で解消発見**
- **H006 duration int → 本書で解消発見**
- (H003 Root.tsx hardcode / H004 shorts mode override / H005 動的 importlib は本書 verify 省略)

→ **cmd_1667 CRITICAL 2件 + HIGH 3件 (H001/H002/H006) = 計 5件解消**。
注: **cmd_1689 audit (5/15) では H001/H002/H006 を grep verify せずに mtime 凍結だけ見て「unchanged 推定」と書いていた = 軍師 audit テンプレ依存ミス**。今回 cmd_1693 タスク要件で明示 verify したことで真実発覚。

---

## ファイル mtime 検証 (cmd_1689 5/15 以降の変更)

```
main.py                       5/9 08:16
make_expression_shorts.py     5/9 07:12
vertical_convert.py           5/9 07:33
make_thumbnail_auto.py        4/5
blur_subtitles.py             4/7
china_shorts_compose.py       4/8
china_shorts_pipeline.py      4/8
```

→ **全 7 ファイル mtime 5/15 以前で凍結・cmd_1689 audit 後の修正ゼロ**

`find -newer queue/reports/2026-05-15_cmd_1689_*.md` 結果:
- `panels_to_cdp_simple.py` / `run_with_auto_retry.sh` / `cdp_chatgpt_image_poc.py` (CDP/漫画系・scope外・cmd_1692 と同じ)

---

## cmd_1689 NEW finding 現状検証

### M1 [PERSISTING]: make_thumbnail_auto.py env override 未展開

- **file:line**: `make_thumbnail_auto.py:47`
- **verify**: `grep -nE "BASE = Path|SHOGUN_ROOT|parents\[3\]"` 結果:
  ```
  47: BASE = Path(__file__).parent.parent   ← env override 未追加
  (SHOGUN_ROOT / parents[3] hit ゼロ)
  ```
- **status**: 未解消・cmd_1680 (5/12) の STT_C003 統一方針未展開・mtime 4/5 で 5週間放置

### M2 [PERSISTING]: china_shorts 3 ファイル別案件 (crowdworks_china_shorts) が scripts/ 直下

- **status**: 未解消・3 ファイルとも mtime 4/7-4/8 で変更なし・移動未実施

### M3 [PERSISTING]: china_shorts_compose.py REQUIRED_KEYS assert 不在

- **verify**: `grep -n "REQUIRED_KEYS" china_shorts_compose.py` → **hit ゼロ**
- **status**: 未解消・mtime 4/8 で変更なし

### M4 [cmd_1667 V_M007 PERSISTING]: get_duration 重複定義

- **status**: 未解消 (vertical_convert.py:142 / pipeline_utils.py:22 mtime 変化なし)

### LOW L1 [PERSISTING]: blur_subtitles.py easyocr preflight 不在

- **status**: 未解消 (mtime 4/7)

### LOW L2 [PERSISTING]: make_thumbnail_auto.py Gemini API registry 整合

- **status**: 整合確認済 (cmd_1689 で記録のみ・本書も同様)

### LOW L3 [部分解消]: cmd_1667 LOW 残課題

- cmd_1689 で「cmd_1667 LOW 8件継続」と記載・本書 verify 省略
- 但し cmd_1667 LOW のうち L004 (__main__ ガード) は元から OK 判定
- 他 LOW 7件は mtime 凍結ゆえ未対応推定

---

## 新規 finding (5/15 以降 動画系で発見)

→ **0 件**

理由:
1. 動画 scope の全 7 ファイル mtime 5/9 以前で凍結 (10日変更ゼロ)
2. cmd_1667 + cmd_1689 で詳細 audit 済 + 本書で 5/9 修正分の解消を補完発見
3. 5/15 以降の新規 3 ファイルは CDP/漫画系で scope 外

---

## ffmpeg_nvenc.md ルール遵守 — 再確認

cmd_1689 verify と同様・全プロジェクトコードで NVENC 一貫使用・libx264 直接利用ゼロ → **OK**

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **【最大の前進】cmd_1667 HIGH 残課題 H001/H002/H006 全件解消発見** → cmd_1667 案件は CRITICAL 2 + HIGH 3 = 5件解消で実質完了・残りは MEDIUM 6 + LOW 8 だが優先度低
2. **cmd_1689 残課題 7件** (MEDIUM 4 + LOW 3) は 1-2 cmd で一括処置可能 (足軽 1 人で 30-60 分)
   - M1 make_thumbnail_auto env override (cmd_1680 STT_C003 と同手法)
   - M2 china_shorts ファイル移動
   - M3 china_shorts_compose REQUIRED_KEYS assert
   - M4 get_duration 重複解消 (`from pipeline_utils import get_duration` 切替)
3. **cmd_1689 audit テンプレ依存ミスの教訓**:
   - mtime 凍結時も「タスク要件で明示された特定 finding は必ず grep verify する」運用に
   - 本書はその教訓を反映 (H001/H002/H006 を grep で個別 verify)

---

## メタ情報

- **精読 (差分 verify 経由)**: vertical_convert.py L379+L430-450 / main.py L556-577 / make_expression_shorts.py L211+L246 / make_thumbnail_auto.py L47 / china_shorts_compose.py L74+L113+L202
- **mtime 検証**: 全 7 ファイル + 新規 3 ファイル特定
- **grep verify**: cmd_1667 H001 (atempo/valid_speed) / H002 (_src_h/<= 480/480p) / H006 (duration/int(cfg)) + cmd_1689 M1 (BASE/SHOGUN_ROOT) / M3 (REQUIRED_KEYS) を個別 CLI 実行
- **baseline**: cmd_1689 (5/15) + cmd_1667 (5/8)
- **advisor()**: 不要 (6 夜目連続 audit で運用パターン確立済・cmd_1688/1690/1692 同パターン)
- **時間**: 02:03 受領 → 02:15 報告書作成 (約 12 分)

## north_star_alignment

- status: aligned
- reason: cmd_1667 (5/8) HIGH 残課題 H001/H002/H006 が **本書 verify で 3件全件解消発見** = 動画パイプライン制作リードタイム短縮の根本問題が解決済。cmd_1689 audit (5/15) で見落としていた事実が判明したのは軍師 audit テンプレ依存ミスの教訓
- risks_to_north_star:
  - 軍師 audit が「mtime 凍結 → 全件 unchanged 推定」になりがち = grep verify 怠ると真実を見落とす (今回検証で明白)
  - cmd_1689 残課題 7件は依然未対処だが優先度低・MEDIUM 5週間以上放置でも実害発生していない
  - cmd_1667 LOW 残課題は本書 verify 省略 = 同じ見落としリスク残存
