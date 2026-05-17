# cmd_1692 夜間矛盾検出レポート — STT パイプライン (cmd_1688 比較版)

- **作成日時**: 2026-05-18 02:10 JST
- **作成者**: 軍師 (subtask_1692_stt)
- **対象カテゴリ**: STT パイプライン (vocal_stt_pipeline.py / stt_merge.py / speaker_id.py / vocab_helper.py / batch_speaker_match.py / apply_speaker_mapping_srt.py / pipeline_utils.py / auto_fetch.py / assemblyai_stt_clips.py)
- **形式**: cmd_828 準拠 + cmd_1688 比較
- **制約遵守**: コード修正なし / テスト作成なし / 読んで報告のみ
- **baseline**: 2026-05-14 cmd_1688 (`queue/reports/2026-05-14_cmd_1688_stt_contradiction.md`) — HIGH 1 / MEDIUM 5 / LOW 3 = 9 件

## サマリ

| Severity | cmd_1688 | RESOLVED | PERSISTING | NEW | 合計 |
|----------|---------:|---------:|-----------:|----:|-----:|
| CRITICAL | 0 | 0 | 0 | 0 | 0 |
| HIGH     | 1 | 0 | **1** | 0 | 1 |
| MEDIUM   | 5 | 0 | **5** | 0 | 5 |
| LOW      | 3 | 0 | **3** | 0 | 3 |
| **計**   | 9 | 0 | **9** | **0** | 9 |

**所感**: cmd_1688 から 4 日経過しても **9 件全て未解消**・STT scope ファイル全て **mtime 5/14 以前で凍結**。infra 系 (cmd_1686→1690 で CRITICAL+HIGH 2件解消) と対照的に **STT 系の対処が完全停滞**。

---

## ファイル mtime 検証 (5/14 以降の変更)

```
apply_speaker_mapping_srt.py     5/4
assemblyai_stt_clips.py          3/25
auto_fetch.py                    5/12
batch_speaker_match.py           5/4
pipeline_utils.py                4/5
run_speaker_match_only.py        5/4
speaker_id.py                    5/12
stt_merge.py                     5/12
vocab_helper.py                  5/11
vocal_stt_pipeline.py            5/12
```

→ **STT scope の全 10 ファイルが 5/14 cmd_1688 audit より前の mtime で凍結**。

`find -newer queue/reports/2026-05-14_cmd_1688_stt_contradiction.md` 結果:
- `panels_to_cdp_simple.py` (NEW・CDP/漫画系)
- `run_with_auto_retry.sh` (NEW・retry runner)
- `cdp_chatgpt_image_poc.py` (NEW・CDP/漫画系)

→ 5/14 以降の新規 3 ファイルは **全て CDP/漫画系**・STT scope 外。STT パイプラインへの修正はゼロ。

---

## cmd_1688 finding 現状検証 (1件ずつ verify)

### HIGH H1 [PERSISTING]: batch_speaker_match.py:18 MEMBER_NAMES hardcode

- **file:line**: `projects/dozle_kirinuki/scripts/batch_speaker_match.py:18`
- **verify**: `grep -n "MEMBER_NAMES\|load_members" batch_speaker_match.py` 結果:
  ```
  18:MEMBER_NAMES = {"dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"}  ← hardcode 残存
  53:        return any(s not in MEMBER_NAMES and len(s) == 1 for s in speakers)
  ```
  `from members import load_members_from_yaml` は **未追加** (grep hit ゼロ)
- **status**: **未解消** (cmd_1688 後 4日放置・mtime 5/4 で変更なし)
- **タスク要件** (`cmd_1688 HIGH 現状確認必須`) 完遂

### MEDIUM M1 [PERSISTING]: auto_fetch.py 「廃止済み」WARNING + 全ロジック残存

- **file:line**: `auto_fetch.py:20-21,22以降`
- **status**: 未解消・cron も crontab.snapshot.txt L12-14 で **依然コメントアウト** で hit (実 call site 0・dead module 状態継続)

### MEDIUM M2 [PERSISTING]: assemblyai_stt_clips.py dead module (SDK vs REST 乖離)

- **status**: 未解消・mtime 3/25 で変更なし

### MEDIUM M3 [PERSISTING]: apply_speaker_mapping_srt.py COPY_FROM hardcode

- **file:line**: `apply_speaker_mapping_srt.py:33-35`
- **verify**: `grep -n "COPY_FROM" apply_speaker_mapping_srt.py` 結果:
  ```
  33:COPY_FROM = {
  86:    for srt_name, src_path in COPY_FROM.items():
  ```
- **status**: 未解消・mtime 5/4・特定動画 `merged__sVuKf5Zu4A.srt` (2026-02-14「寝ないと死ぬ」回) 固有名残存

### MEDIUM M4 [PERSISTING]: batch_speaker_match.py preflight check 不在

- **file:line**: `batch_speaker_match.py:19-20`
- **verify**: `grep -n "exists\|assert" batch_speaker_match.py` 結果:
  ```
  27:    if candidate.exists():    ← find_vocals_for_video 内・対象動画 vocals に対する確認
  33:        if vocals.exists():
  41:        if vocals.exists():
  ```
  - run_speaker_match_only.py / venv/bin/python3 の preflight assert は **依然不在**
- **status**: 未解消

### MEDIUM M5 [PERSISTING]: vocal_stt_pipeline.py:41 dead import

- **file:line**: `vocal_stt_pipeline.py:41`
- **verify**: `grep -n "from vocab_helper" vocal_stt_pipeline.py` 結果:
  ```
  41:from vocab_helper import apply_vocabulary  # noqa: E402
  ```
  本ファイル内 `apply_vocabulary` 利用箇所は依然 0 (cmd_1680 final QC + cmd_1688 で指摘済)
- **status**: 未解消・cmd_1680 (5/12) から **6 日放置**

### LOW L1 [PERSISTING]: pipeline_utils.py `_get_h264_encoder()` h264_nvenc hardcode

- **status**: 未解消・mtime 4/5 で変更なし・scope-adjacent

### LOW L2 [PERSISTING]: auto_fetch.py の path env override 未展開

- **status**: 未解消・dead module ゆえ実害なし

### LOW L3 [PERSISTING]: smoke test 未実施 (py_compile のみ)

- **status**: cmd_1680 final QC (5/12) から **6 日放置**・実 STT 実行 evidence なし

---

## 新規 finding (5/14 以降 STT 系で発見)

→ **0 件**

理由:
1. STT scope の全 10 ファイル mtime が 5/14 cmd_1688 audit 以前で凍結 (4日間変更ゼロ)
2. cmd_1680 (5/12) + cmd_1688 (5/14) で詳細 audit 済・新規発見余地が枯渇
3. 5/14 以降の新規ファイル (panels_to_cdp_simple.py / cdp_chatgpt_image_poc.py / run_with_auto_retry.sh) は CDP/漫画系で STT scope 外

---

## 並列 DL 制約 (feedback_youtube_subtitle_ip_ban.md) 再確認

cmd_1691 (5/17) で確認した通り STT パイプライン内に並列 DL は存在しない:
- vocal_stt_pipeline.py: Demucs + AssemblyAI + Deepgram (順次)
- stt_merge.py: JSON 結合 (DL なし)
- speaker_id.py: ECAPA-TDNN 声紋識別 (DL なし)

→ 並列 DL 制約違反ゼロ・継続遵守。

---

## 推奨 follow-up cmd

> 本タスクは読んで報告のみのため実装は別 cmd。

1. **HIGH H1**: `batch_speaker_match.py:18` MEMBER_NAMES → `load_members_from_yaml()` 化 (5分・足軽1人)
   - **cmd_1688 から 4日放置のため、本書で再度ハイライト**
2. **MEDIUM M1-M5 一括処置**: cmd_1688 で提案済・依然有効
   - M1+M2 dead module 2件を legacy/ 移動
   - M3 COPY_FROM yaml 化
   - M4 preflight check 追加
   - M5 vocal_stt_pipeline.py:41 dead import 削除
3. **LOW L1-L3**: 優先度低
4. **観察**: cmd_1680 (5/12)・cmd_1688 (5/14)・cmd_1692 (5/18) と 6 日間で **同じ findings が 3 回 audit で同様に出続けている**。家老が「無限 audit ループ」に陥る前に follow-up cmd で対処すべき
5. **audit cadence 見直し提案再掲** (cmd_1690 と同様): STT 系は新規変更がない期間 (4日以上凍結) は audit 間隔を週 1回に下げる検討余地あり

---

## メタ情報

- **精読 (差分 verify 経由)**: batch_speaker_match.py L18 + L19-20 + L27-41 / apply_speaker_mapping_srt.py L33-35 / vocal_stt_pipeline.py L41 / 他 cmd_1688 既読で cite のみ
- **mtime 検証**: `ls -la projects/dozle_kirinuki/scripts/*.py` で全 10 ファイル mtime 確認 (全て 5/14 以前)
- **find 検証**: `find -newer queue/reports/2026-05-14_cmd_1688_stt_contradiction.md` で 3 ファイル特定 (全て CDP/漫画系・STT scope 外)
- **baseline**: `queue/reports/2026-05-14_cmd_1688_stt_contradiction.md` (HIGH 1 / MEDIUM 5 / LOW 3)
- **advisor()**: 不要 (5 夜目連続 audit で運用パターン確立済・cmd_1688 baseline 差分のみ集中)
- **時間**: 02:03 受領 → 02:12 報告書作成 (約 9 分・全件未解消で新規 0 件のためシンプル)

## north_star_alignment

- status: aligned
- reason: cmd_1688 (5/14) → cmd_1692 (5/18) で 4 日経過・STT 系修正ゼロを構造的に検出。本書最大の価値は「新規 finding 0」を示すことではなく、「**家老の対処キューが詰まっている**」を flag すること。infra 系 (cmd_1686→1690) は CRITICAL+HIGH 2件解消で対比明白
- risks_to_north_star:
  - cmd_1680 (5/12) 残課題が 6 日放置・cmd_1688 残課題が 4 日放置 → **audit→修正→検証** の運用ループが STT 系で詰まっている
  - HIGH H1 (batch_speaker_match MEMBER_NAMES hardcode) は 5分修正だが、新メンバー追加計画と関連し中期的事故源
  - 家老が「cmd_1688 残課題は無視して新規 audit を回す」運用になっている可能性 — 家老向けに「未対処キュー監視」を促す
