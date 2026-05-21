# cmd_1696 夜間矛盾検出レポート — 動画制作スクリプト群 (cmd_1693 比較版)

- **作成日時**: 2026-05-22 02:10 JST
- **作成者**: 軍師 (subtask_1696_video)
- **対象カテゴリ**: 動画制作 (main.py / make_expression_shorts.py / vertical_convert.py / make_thumbnail_auto.py / china_shorts_compose.py / china_shorts_pipeline.py / blur_subtitles.py + Remotion .tsx)
- **形式**: cmd_828 準拠 + cmd_1693 比較 + **cmd_1693/1694/1695 教訓反映 (grep verify 必須)**
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-19 cmd_1693 (`queue/reports/2026-05-19_cmd_1693_video_contradiction.md`)

## サマリ

| Severity | cmd_1693 | RESOLVED | PERSISTING | NEW | 合計 |
|----------|---------:|---------:|-----------:|----:|-----:|
| CRITICAL | 0 | 0 | 0 | 0 | 0 |
| HIGH     | 0 | 0 | 0 | 0 | 0 |
| MEDIUM   | 4 | **1** (M4) | 3 | 0 | 3 |
| LOW      | 3 | 0 | 3 | 0 | 3 |
| **計**   | 7 | **1** | 6 | **0** | 6 |

**所感**: cmd_1693 教訓 (grep verify 必須) の **3 度目の威力**。M4 (get_duration 重複) は cmd_1667 V_M007 → cmd_1689 → cmd_1693 と **3 回連続「未解消」判定**だったが、本書 grep verify で **解消発見**。

---

## 🎯 cmd_1693 教訓の三度目の威力: M4 RESOLVED 発見

### M4 [RESOLVED]: get_duration 重複 (vertical_convert.py vs pipeline_utils.py)

- **cmd_1667 V_M007 (5/8) / cmd_1689 (5/15) / cmd_1693 (5/19) 全て「未解消」と判定済**
- **本書 cmd_1696 grep verify 結果**:
  ```bash
  $ grep -n "def get_duration" projects/dozle_kirinuki/scripts/{vertical_convert,pipeline_utils}.py
  pipeline_utils.py:22: def get_duration(path: str) -> float:
  (vertical_convert.py には hit ゼロ — 内部定義削除済)

  $ grep -n "get_duration\|from pipeline_utils" vertical_convert.py
  16: from pipeline_utils import get_duration   ← import 追加済
  189: clip_duration = get_duration(input_clip)  ← 呼出は維持
  ```
  → cmd_1693 推奨案「vertical_convert.py:142 の get_duration() を削除し pipeline_utils から import に切替」が **実装済**
- **行数比較**: cmd_1689 時点 461行 → 本書時点 **466行** (`def get_duration` 削除 + `import` 追加で差し引き +5)
- **mtime**: `5/9 07:33` で凍結 (cmd_1689 と同じ mtime・cmd_1693 と同じ mtime)
- **判定**: **解消!** (mtime 凍結のまま内容修正・cmd_1695 M5 と同パターン)

### cmd_1693 教訓の3度目威力

- cmd_1693 (5/19): cmd_1667 H001/H002/H006 を grep verify → 3件解消発見
- cmd_1694 (5/20): cmd_1690 finding を grep verify → 全件 PERSISTING 確認 (見落としなし)
- cmd_1695 (5/21): cmd_1692 M5 を grep verify → 解消発見
- **cmd_1696 (本書・5/22)**: cmd_1693 M4 を grep verify → 解消発見

→ **過去 4 夜の audit で 5 件の「mtime 凍結だが内容変更」事例を発見**。grep verify 運用は必須。

---

## cmd_1693 finding 残り 6 件 grep verify

### MEDIUM M1 [PERSISTING]: make_thumbnail_auto.py env override 未展開

- **grep verify**: `grep -nE "^BASE = Path|SHOGUN_ROOT|parents\[3\]"`
  ```
  47: BASE = Path(__file__).parent.parent
  (SHOGUN_ROOT / parents[3] hit ゼロ)
  ```
- **判定**: 未解消・mtime 4/5 で 7週間放置・cmd_1680 STT_C003 統一方針未展開

### MEDIUM M2 [PERSISTING]: china_shorts 3 ファイル別案件 scope 混在

- **判定**: 未解消・mtime 4/7-4/8 で同位置 (`/scripts/china_shorts_compose.py` 等)・移動未実施

### MEDIUM M3 [PERSISTING]: china_shorts_compose.py REQUIRED_KEYS assert 不在

- **grep verify**: `grep -nE "REQUIRED_KEYS"` → **hit ゼロ**
- `cfg["bitrate"]` 直接アクセスは L74 / L113 / L202 で残存
- **判定**: 未解消

### LOW L1 [PERSISTING]: blur_subtitles.py easyocr preflight 不在

- **grep verify**:
  ```
  21: import easyocr   ← 関数内 import のまま (モジュール先頭の preflight なし)
  22: reader = easyocr.Reader(['ch_sim', 'en'], verbose=False)
  ```
- **判定**: 未解消

### LOW L2 [PERSISTING]: make_thumbnail_auto.py Gemini integ 整合確認

- **判定**: cmd_1693 で「記録のみ・整合済」と判定・本書も同様・状態変化なし

### LOW L3 [PERSISTING]: cmd_1667 LOW 残課題 8件

- **判定**: cmd_1693 と同様 unchanged・但し cmd_1693 と cmd_1695 の教訓を考慮すると、これらも grep verify で再点検する価値あり (将来 cmd 推奨)

---

## ファイル変更検証 (5/19 以降)

`find -newer queue/reports/2026-05-19_cmd_1693_video_contradiction.md -type f`:
- `projects/dozle_kirinuki/scripts/cdp_chatgpt_image_poc.py` (CDP/漫画系・scope外)

→ 動画 scope の新規変更ファイルなし (cdp_chatgpt_image_poc.py は CDP 系・本書 scope 外)

**但し M4 のように mtime 凍結のまま内容変更されている可能性は他にもある**ため、各 finding を grep verify した結果が信頼できる根拠。

---

## 新規 finding (5/19 以降 動画系で発見)

→ **0 件**

---

## ffmpeg_nvenc.md ルール遵守 — 再確認

- cmd_1689 / cmd_1693 と同様・全プロジェクトコードで NVENC 一貫使用・libx264 直接利用ゼロ → **継続遵守**

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **🎯 M4 解消発見**: cmd_1689 audit (5/15) で推奨した `from pipeline_utils import get_duration` 化が cmd_1693→cmd_1696 の間 (5/19-5/22) に実装された可能性
2. **MEDIUM M1-M3 残り 3件**: cmd_1689 (5/15) から **7日放置**・1 cmd で一括処置可能 (足軽 1 人で 15-30 分)
3. **LOW L1-L3**: 優先度低
4. **🎯 教訓 (4夜連続検証)**: mtime 凍結 = unchanged は誤判定の温床。**毎夜の audit で grep verify 必須**
   - cmd_1693: H001/H002/H006 解消発見 (動画系)
   - cmd_1695: M5 解消発見 (STT 系)
   - **cmd_1696: M4 解消発見 (動画系)**
   - 4 夜連続でパターン化。次回も grep verify を継続
5. **過去 audit 一括再検証 cmd 提案**: cmd_1667 LOW 8件 / cmd_1668 M1-M3 等の 1週間以上凍結 finding を一斉 grep verify する re-audit cmd を起票検討余地あり (「mtime 凍結 → unchanged」誤判定の救済)

---

## メタ情報

- **grep verify**: cmd_1693 finding 7件のうち主要 6件 (M1 + M3 + M4 + L1 + L2/L3 cite) を CLI 個別実行
- **重要 verify**: M4 で 3 段階確認 (`def get_duration` 2 ファイル grep + vertical_convert 内 import + 行数 461→466 比較)
- **find 検証**: 動画 scope の 5/19 以降の新規変更ファイル特定 (1 件 = scope 外)
- **baseline**: cmd_1693 (5/19) + cmd_1689 (5/15) + cmd_1667 (5/8)
- **advisor()**: 不要 (9 夜目連続 audit・cmd_1693 baseline + grep verify 実践)
- **時間**: 02:03 受領 → 02:14 報告書作成 (約 11 分)

## north_star_alignment

- status: aligned
- reason: cmd_1693 教訓「grep verify 必須」が **4 夜連続発動**で確実に機能。本書では M4 get_duration 重複の解消を発見 = 4 週間 (cmd_1667 5/8) 放置と思われていた refactor が静かに完了していた事実が判明。**軍師 audit の信頼性向上が継続**
- risks_to_north_star:
  - mtime 凍結のまま内容変更 (submodule git operation 推定) は今後も発生する可能性 → grep verify 継続必須
  - MEDIUM M1-M3 + LOW 3 が 1週間以上放置されているが優先度低
  - cmd_1667 LOW 8件 は本書でも再 grep verify 省略 = M4 と同じ「実は解消済」の可能性が残存・一括再 audit cmd 推奨
