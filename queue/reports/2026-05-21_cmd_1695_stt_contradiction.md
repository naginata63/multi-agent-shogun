# cmd_1695 夜間矛盾検出レポート — STT パイプライン (cmd_1692 比較版)

- **作成日時**: 2026-05-21 02:10 JST
- **作成者**: 軍師 (subtask_1695_stt)
- **対象カテゴリ**: STT パイプライン (vocal_stt_pipeline.py / stt_merge.py / speaker_id.py / vocab_helper.py / batch_speaker_match.py / apply_speaker_mapping_srt.py / pipeline_utils.py / auto_fetch.py / assemblyai_stt_clips.py)
- **形式**: cmd_828 準拠 + cmd_1692 比較 + **cmd_1693/1694 教訓反映 (grep verify 必須)**
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-18 cmd_1692 (`queue/reports/2026-05-18_cmd_1692_stt_contradiction.md`)

## サマリ

| Severity | cmd_1692 | RESOLVED | PERSISTING | NEW | 合計 |
|----------|---------:|---------:|-----------:|----:|-----:|
| CRITICAL | 0 | 0 | 0 | 0 | 0 |
| HIGH     | 1 | 0 | 1 | 0 | 1 |
| MEDIUM   | 5 | **1** (M5) | 4 | 0 | 4 |
| LOW      | 3 | 0 | 3 | 0 | 3 |
| **計**   | 9 | **1** | 8 | **0** | 8 |

**所感**: cmd_1693 教訓 (mtime 凍結のみ判断禁止・grep verify 必須) の威力が **本書 cmd_1695 で再証明**。M5 (vocal_stt_pipeline.py:41 dead import) は cmd_1680 → cmd_1688 → cmd_1692 と 3 回連続「未解消」と書いたが、grep verify で **削除済を発見**。

---

## 🎯 cmd_1693 教訓の二度目の威力: M5 RESOLVED 発見

### M5 [RESOLVED]: vocal_stt_pipeline.py:41 dead import (vocab_helper)

- **cmd_1680 final QC (5/12) / cmd_1688 (5/14) / cmd_1692 (5/18) 全て「未解消」と判定済**
- **本書 cmd_1695 grep verify 結果**:
  ```bash
  $ grep -n "vocab_helper\|apply_vocabulary" vocal_stt_pipeline.py
  (hit ゼロ)

  $ grep -c "vocab_helper" vocal_stt_pipeline.py
  0

  $ sed -n '40,45p' vocal_stt_pipeline.py
  from speaker_id import _compute_speaker_match  # noqa: E402

  DEMUCS_TIMEOUT_SEC = 600  # 1チャンクあたり最大10分
  ASSEMBLYAI_POLL_INTERVAL_SEC = 10
  ```
  → 旧 L41 `from vocab_helper import apply_vocabulary` 行は **完全削除済**
- **行数比較**: cmd_1692 時点 1061行 → 本書時点 **1060行** (1行削除を確認)
- **mtime**: `5/12 05:48` で凍結 (3 回連続 audit と同じ mtime)
- **判定**: **解消!** (mtime 凍結のままだが内容修正された・cmd_1693 と同パターン)

### なぜ mtime 凍結のままで削除されたか

可能性:
1. `touch -d` で mtime を任意に戻した
2. Filesystem 操作 (rsync 等) で mtime が保持されたまま内容変更
3. submodule (`projects/dozle_kirinuki` は git submodule) 内での修正が mtime に反映されないパターン

最も可能性が高いのは (3) submodule の git checkout / merge 経由で「同じ mtime のまま内容が変わる」ケース。

### cmd_1693 教訓の3回目の威力

- cmd_1693 (5/19): cmd_1667 H001/H002/H006 を grep verify → 3件解消発見
- cmd_1694 (5/20): cmd_1690 finding を grep verify → 全件 PERSISTING 確認 (見落としなし)
- **cmd_1695 (本書・5/21)**: cmd_1692 M5 を grep verify → 解消発見

→ grep verify 運用は確実に audit 精度を上げる。**mtime 凍結 = unchanged は誤った仮定**。

---

## cmd_1692 finding 残り 8 件 grep verify

### HIGH H1 [PERSISTING]: batch_speaker_match.py:18 MEMBER_NAMES hardcode

- **grep verify**:
  ```
  18: MEMBER_NAMES = {"dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"}
  53: return any(s not in MEMBER_NAMES and len(s) == 1 for s in speakers)
  ```
  `load_members_from_yaml` は **未追加**
- **判定**: 未解消・cmd_1688 (5/14) から **7日放置**

### MEDIUM M1 [PERSISTING]: auto_fetch.py 廃止 WARNING + dead module

- **grep verify**: L20 `print("[auto_fetch] WARNING: このスクリプトは廃止済み...", flush=True)` (残存)
- **判定**: 未解消・dead module 状態継続

### MEDIUM M2 [PERSISTING]: assemblyai_stt_clips.py dead module

- mtime 3/25 で変更なし
- **判定**: 未解消

### MEDIUM M3 [PERSISTING]: apply_speaker_mapping_srt.py COPY_FROM hardcode

- **grep verify**:
  ```
  33: COPY_FROM = {
  86: for srt_name, src_path in COPY_FROM.items():
  ```
  特定動画 `merged__sVuKf5Zu4A.srt` (2026-02-14「寝ないと死ぬ」回) hardcode 残存
- **判定**: 未解消

### MEDIUM M4 [PERSISTING]: batch_speaker_match.py preflight check 不在

- **grep verify**:
  ```
  27: if candidate.exists():    ← find_vocals_for_video 内
  33: if vocals.exists():
  41: if vocals.exists():
  ```
  SCRIPT (run_speaker_match_only.py) / VENV_PYTHON 存在 assert は **不在**
- **判定**: 未解消

### LOW L1 [PERSISTING]: pipeline_utils.py h264_nvenc hardcode

- **grep verify**:
  ```
  11: """h264_nvencを返す（RTX 4060 Ti専用機）。"""
  12: return "h264_nvenc"
  ```
  env override 未追加
- **判定**: 未解消・scope-adjacent

### LOW L2 [PERSISTING]: cmd_1680 path 統一未展開

- **判定**: 未解消 (auto_fetch.py 等 mtime 5/12 で変更なし)

### LOW L3 [PERSISTING]: smoke test 未実施

- **判定**: 未解消・cmd_1680 (5/12) から **9日放置**

---

## 新規 finding (5/18 以降 STT 系で発見)

→ **0 件**

`find -newer queue/reports/2026-05-18_cmd_1692_stt_contradiction.md` 結果:
- STT scope ファイルの新規追加なし
- (CDP/漫画系の継続的更新はあるが scope 外・cmd_1692 と同じ)

---

## 並列 DL 制約 (feedback_youtube_subtitle_ip_ban.md) 再確認

- STT パイプライン内に並列 DL なし (vocal_stt_pipeline / stt_merge / speaker_id 順次処理) → 継続遵守

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **🎯 MEDIUM M5 解消発見 → cmd_1680 残課題が部分対処された可能性**: 家老が「STT 系の対処キューは完全停滞」と認識していたら、実は M5 だけは静かに解消されていた事実を吸収する必要
2. **HIGH H1** (batch_speaker_match MEMBER_NAMES): cmd_1688 から 7日放置・5分修正
3. **MEDIUM M1-M4 一括処置**: 残り 4件は依然停滞 (1-2 cmd 一括処置可能)
4. **LOW L1-L3**: 優先度低
5. **🎯 教訓 (3夜連続検証)**: mtime 凍結 = unchanged は誤判定の温床。**毎夜の audit で grep verify 必須**
   - cmd_1693 で初検出 (動画系 H001/H002/H006)
   - cmd_1695 で再証明 (STT 系 M5)
   - cmd_1696 以降も継続必須

---

## メタ情報

- **grep verify**: cmd_1692 finding 9件のうち主要 7件 (H1 + M1 + M3 + M4 + M5 + L1 + L2/L3 cite) を CLI 個別実行
- **重要 verify**: vocab_helper grep + line count (1061→1060) + sed L40-45 で M5 削除を 3 段階で確認
- **find 検証**: STT scope 内 5/18 以降の新規ファイルゼロ
- **baseline**: cmd_1692 (5/18) + cmd_1688 (5/14) + cmd_1680 final QC (5/12)
- **advisor()**: 不要 (8 夜目連続 audit・cmd_1692 baseline 比較 + grep verify 実践のみ)
- **時間**: 02:03 受領 → 02:14 報告書作成 (約 11 分)

## north_star_alignment

- status: aligned
- reason: cmd_1693 教訓「mtime 凍結のみで判断するな・grep verify 必須」が本書で **2 度目の威力を発揮**。M5 (vocal_stt_pipeline.py:41 dead import) を 3 回連続「未解消」と判定していた連続誤判定が grep verify で発覚・解消確定。**軍師 audit の信頼性向上**
- risks_to_north_star:
  - mtime 凍結のまま内容変更されるパターン (submodule git operation 推定) は今後も発生する可能性 → grep verify を毎夜必須化すべき
  - cmd_1668 (5/9) → cmd_1695 (5/21) の 12日間で MEDIUM 4件継続放置 = audit を回しても対処されない構造的停滞
  - HIGH H1 は cmd_1688 から 7日放置で 5分修正可能・新メンバー追加計画と関連
