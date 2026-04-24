# cmd_1449 領域D / subtask_1449_d — part_info.json 誤記修正レポート

- **worker**: ashigaru1
- **task**: subtask_1449_d (cmd_1449 領域D)
- **parent_cmd**: cmd_1449
- **target file (needs fix)**: `work/cmd_1425/part_info.json`
- **generated_at**: 2026-04-24T23:45 JST
- **status**: **BLOCKED_FOR_APPLY** — パッチ全文準備完了・PreToolUse hook (cmd_1443 p06 scope guard) により足軽が `work/cmd_1425/` 直接書換不可。家老 apply 待ち

## 1. 結論サマリ

`work/cmd_1425/part_info.json` の誤記:

| 箇所 | 誤 | 正 |
|------|-----|----|
| `description` | "Day6 4視点DL+1時間分割集約 (**oo_men除く3視点**)" | "Day6 4視点DL+1時間分割集約 (**4視点: tsurugi/hendy/charlotte/oo_men**)" |
| `note` | "**oo_men_parts.jsonが存在しないため3視点のみ**" | (下記§4 の新 note 文面に差し替え。root cause 解説付き) |
| `oo_men` セクション | **欠落** | **10 parts を追記**（§4 全文参照） |

実態: おおはらMEN視点 Day6 動画は **10 parts 実在** (合計 **09:01:48.43**, 16.58 GB) が `projects/dozle_kirinuki/work/20260416_…おおはらMEN視点/` 配下にダウンロード済・分割済。

## 2. 根本原因 (Root Cause)

他3視点 (tsurugi / hendy / charlotte) が `day6_{speaker}_part_XX.mp4` 命名なのに対し、
oo_men のみ **video_id 命名** `t7JJlTDACyc_part_XX.mp4` で格納されている。

cmd_1425 の `part_info.json` 生成時に `day6_oo_men_part_*` パターンで探索したため「oo_men_parts.json 存在しない → 3視点のみ」と誤判定された。実ファイルは `t7JJlTDACyc_part_*.mp4` として全 10 本揃っている。

**推奨恒久対策** (別 cmd 化): cmd_1425 の分割 pipeline で保存時に命名を正規化するか、part_info 生成器を video_id fallback 探索付きに改修せよ。本 subtask ではスコープ外（家老判断）。

## 3. 実在証跡

### 3.1 ls -la（ファイルサイズ証跡）

```
$ ls -la "projects/dozle_kirinuki/work/20260416_【#DoZ】6日目…おおはらMEN視点/"/t7JJlTDACyc_part_*.mp4
-rw-rw-r-- 1 murakami murakami 1816898876 4月 19 15:39 t7JJlTDACyc_part_00.mp4
-rw-rw-r-- 1 murakami murakami 1873027722 4月 19 15:39 t7JJlTDACyc_part_01.mp4
-rw-rw-r-- 1 murakami murakami 1869511362 4月 19 15:40 t7JJlTDACyc_part_02.mp4
-rw-rw-r-- 1 murakami murakami 1740771602 4月 19 15:41 t7JJlTDACyc_part_03.mp4
-rw-rw-r-- 1 murakami murakami 2024495521 4月 19 15:41 t7JJlTDACyc_part_04.mp4
-rw-rw-r-- 1 murakami murakami 1741514055 4月 19 15:42 t7JJlTDACyc_part_05.mp4
-rw-rw-r-- 1 murakami murakami 2086631301 4月 19 15:42 t7JJlTDACyc_part_06.mp4
-rw-rw-r-- 1 murakami murakami 1631934981 4月 19 15:43 t7JJlTDACyc_part_07.mp4
-rw-rw-r-- 1 murakami murakami 1181141710 4月 19 15:43 t7JJlTDACyc_part_08.mp4
-rw-rw-r--  1 murakami murakami  13421407 4月 19 15:43 t7JJlTDACyc_part_09.mp4
```

**10 本確認**（DL 完了: 2026-04-19 15:39〜15:43）

### 3.2 ffprobe（コーデック / duration 証跡）

`ffprobe -v error -select_streams v:0 -show_entries stream=codec_name` + `-select_streams a:0` 実測:

| # | filename | duration_sec | duration_hms | size_bytes | size_mb | video | audio |
|---|----------|-------------:|:-------------|-----------:|--------:|:------|:------|
| 00 | t7JJlTDACyc_part_00.mp4 | 3600.081 | 01:00:00.08 | 1,816,898,876 | 1732.7 | vp9 | opus |
| 01 | t7JJlTDACyc_part_01.mp4 | 3600.074 | 01:00:00.07 | 1,873,027,722 | 1786.3 | vp9 | opus |
| 02 | t7JJlTDACyc_part_02.mp4 | 3600.068 | 01:00:00.07 | 1,869,511,362 | 1782.9 | vp9 | opus |
| 03 | t7JJlTDACyc_part_03.mp4 | 3600.001 | 01:00:00.00 | 1,740,771,602 | 1660.1 | vp9 | opus |
| 04 | t7JJlTDACyc_part_04.mp4 | 3600.001 | 01:00:00.00 | 2,024,495,521 | 1930.7 | vp9 | opus |
| 05 | t7JJlTDACyc_part_05.mp4 | 3600.001 | 01:00:00.00 | 1,741,514,055 | 1660.8 | vp9 | opus |
| 06 | t7JJlTDACyc_part_06.mp4 | 3600.421 | 01:00:00.42 | 2,086,631,301 | 1990.0 | vp9 | opus |
| 07 | t7JJlTDACyc_part_07.mp4 | 3602.664 | 01:00:02.66 | 1,631,934,981 | 1556.3 | vp9 | opus |
| 08 | t7JJlTDACyc_part_08.mp4 | 3600.074 | 01:00:00.07 | 1,181,141,710 | 1126.4 | vp9 | opus |
| 09 | t7JJlTDACyc_part_09.mp4 |  105.048 | 00:01:45.05 |    13,421,407 |   12.8 | vp9 | opus |
| **計** | | **32,508.433** | **09:01:48.43** | **17,779,348,537** | **17,239.0** | | |

**合計 9h01m48.43s / 16.58 GiB**（part_09 は tail tsurugi_08 同様の端数 part）

他3視点 (h.264/aac, 1080p) と異なり oo_men のみ **VP9/Opus** コンテナ (YouTube オリジナル DASH stream 由来)。video_id `t7JJlTDACyc` は Day6 おおはらMEN視点動画。

## 4. 修正後 part_info.json 全文

以下を `work/cmd_1425/part_info.json` に上書き適用せよ。

```json
{
  "description": "Day6 4視点DL+1時間分割集約 (4視点: tsurugi/hendy/charlotte/oo_men)",
  "generated_at": "2026-04-24T08:26:14+0900",
  "updated_at": "2026-04-24T23:45:00+0900",
  "note": "cmd_1449_d で oo_men セクション追記(誤記修正)。oo_men 分割 part は `day6_oo_men_part_*.mp4` ではなく `t7JJlTDACyc_part_*.mp4` (video_id 命名) で projects/dozle_kirinuki/work/20260416_…おおはらMEN視点/ 配下に 10 本実在。当初 `day6_oo_men_*` パターンで探索したため『存在しない』と誤判定された。",
  "tsurugi": {
    "source": "day6_tsurugi_full.mp4",
    "total_parts": 9,
    "parts": [
      {"file": "day6_tsurugi_part_00.mp4", "duration_hms": "01:00:02", "size_mb": 2653.1, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3602.02},
      {"file": "day6_tsurugi_part_01.mp4", "duration_hms": "01:00:00", "size_mb": 2652.7, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_02.mp4", "duration_hms": "01:00:00", "size_mb": 2652.2, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_03.mp4", "duration_hms": "01:00:00", "size_mb": 2652.4, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_04.mp4", "duration_hms": "01:00:00", "size_mb": 2653.0, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_05.mp4", "duration_hms": "01:00:00", "size_mb": 2653.1, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_06.mp4", "duration_hms": "01:00:00", "size_mb": 2653.4, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_07.mp4", "duration_hms": "01:00:00", "size_mb": 2652.6, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 3600.0},
      {"file": "day6_tsurugi_part_08.mp4", "duration_hms": "00:21:55", "size_mb": 969.1, "video_codec": "h264", "audio_codec": "aac", "duration_sec": 1315.4}
    ]
  },
  "hendy": {
    "task": "subtask_1425b",
    "source": "twitch_2749323185",
    "parts": [
      {"file": "day6_hendy_part_00.mp4", "duration_sec": 3600.0, "size_mb": 2648.7, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_01.mp4", "duration_sec": 3600.0, "size_mb": 2652.3, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_02.mp4", "duration_sec": 3600.0, "size_mb": 2652.2, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_03.mp4", "duration_sec": 3600.0, "size_mb": 2652.3, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_04.mp4", "duration_sec": 3600.0, "size_mb": 2652.5, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_05.mp4", "duration_sec": 3600.0, "size_mb": 2653.0, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_06.mp4", "duration_sec": 3600.0, "size_mb": 2652.8, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_07.mp4", "duration_sec": 3600.0, "size_mb": 2652.5, "video_codec": "h264", "audio_codec": "aac"},
      {"file": "day6_hendy_part_08.mp4", "duration_sec": 4041.5, "size_mb": 2973.8, "video_codec": "h264", "audio_codec": "aac"}
    ],
    "total_parts": 9
  },
  "charlotte": {
    "source": "day6_charlotte_full.mp4",
    "video_id": "v19JAnVjZ_c",
    "total_parts": 9,
    "parts": [
      {"file": "day6_charlotte_part_00.mp4", "size_bytes": 1364601133, "size_mb": 1301.4, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_01.mp4", "size_bytes": 1372635937, "size_mb": 1309.0, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_02.mp4", "size_bytes": 1366989729, "size_mb": 1303.7, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_03.mp4", "size_bytes": 1376136050, "size_mb": 1312.4, "video_codec": "vp9", "duration_sec": 3605.7},
      {"file": "day6_charlotte_part_04.mp4", "size_bytes": 1459110164, "size_mb": 1391.5, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_05.mp4", "size_bytes": 1330583048, "size_mb": 1268.9, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_06.mp4", "size_bytes": 1416099675, "size_mb": 1350.5, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_07.mp4", "size_bytes": 1292691580, "size_mb": 1232.8, "video_codec": "vp9", "duration_sec": 3600.0},
      {"file": "day6_charlotte_part_08.mp4", "size_bytes": 1138337689, "size_mb": 1085.6, "video_codec": "vp9", "duration_sec": 3346.0}
    ],
    "generated_at": "2026-04-24T08:14:58+09:00"
  },
  "oo_men": {
    "source": "youtube_t7JJlTDACyc",
    "video_id": "t7JJlTDACyc",
    "video_title": "【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】",
    "source_dir": "projects/dozle_kirinuki/work/20260416_【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】/",
    "filename_pattern": "t7JJlTDACyc_part_*.mp4",
    "total_parts": 10,
    "total_duration_sec": 32508.433,
    "total_duration_hms": "09:01:48.43",
    "parts": [
      {"file": "t7JJlTDACyc_part_00.mp4", "duration_sec": 3600.081, "size_bytes": 1816898876, "size_mb": 1732.7, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_01.mp4", "duration_sec": 3600.074, "size_bytes": 1873027722, "size_mb": 1786.3, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_02.mp4", "duration_sec": 3600.068, "size_bytes": 1869511362, "size_mb": 1782.9, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_03.mp4", "duration_sec": 3600.001, "size_bytes": 1740771602, "size_mb": 1660.1, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_04.mp4", "duration_sec": 3600.001, "size_bytes": 2024495521, "size_mb": 1930.7, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_05.mp4", "duration_sec": 3600.001, "size_bytes": 1741514055, "size_mb": 1660.8, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_06.mp4", "duration_sec": 3600.421, "size_bytes": 2086631301, "size_mb": 1990.0, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_07.mp4", "duration_sec": 3602.664, "size_bytes": 1631934981, "size_mb": 1556.3, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_08.mp4", "duration_sec": 3600.074, "size_bytes": 1181141710, "size_mb": 1126.4, "video_codec": "vp9", "audio_codec": "opus"},
      {"file": "t7JJlTDACyc_part_09.mp4", "duration_sec": 105.048,  "size_bytes": 13421407,   "size_mb": 12.8,   "video_codec": "vp9", "audio_codec": "opus"}
    ],
    "generated_at": "2026-04-24T23:45:00+09:00"
  }
}
```

## 5. 差分 (unified diff・参考)

```diff
@@ -1,5 +1,6 @@
 {
-  "description": "Day6 4視点DL+1時間分割集約 (oo_men除く3視点)",
+  "description": "Day6 4視点DL+1時間分割集約 (4視点: tsurugi/hendy/charlotte/oo_men)",
   "generated_at": "2026-04-24T08:26:14+0900",
-  "note": "oo_men_parts.jsonが存在しないため3視点のみ",
+  "updated_at": "2026-04-24T23:45:00+0900",
+  "note": "cmd_1449_d で oo_men セクション追記(誤記修正)。oo_men 分割 part は `day6_oo_men_part_*.mp4` ではなく `t7JJlTDACyc_part_*.mp4` (video_id 命名) で projects/dozle_kirinuki/work/20260416_…おおはらMEN視点/ 配下に 10 本実在。当初 `day6_oo_men_*` パターンで探索したため『存在しない』と誤判定された。",
   "tsurugi": { ... },  // 無変更
@@ (末尾 charlotte 閉じ括弧の直後に oo_men セクション追加) @@
+  ,
+  "oo_men": { ... 10 parts ...}
 }
```

## 6. 家老への apply 手順

1. 本レポートの §4 JSON ブロック全文を `work/cmd_1425/part_info.json` に書き込み（足軽は hook で阻止されるため家老が直接 Write / Edit）
2. 検証: `jq . work/cmd_1425/part_info.json > /dev/null && echo OK`
3. コミット（明示パス）:
   ```
   git add work/cmd_1425/part_info.json work/cmd_1449/part_info_fix_report.md
   git commit -m "fix(cmd_1449_d): part_info.json oo_men セクション追記(誤記修正・10 parts 実在反映)"
   ```

## 7. AC 進捗サマリ

| # | Acceptance Criterion | 状態 |
|---|----------------------|:----:|
| 1 | 対象 part_info.json 特定(Day6/cmd_1425 関連) | ✅ (`work/cmd_1425/part_info.json`) |
| 2 | 『oo_men 不在』誤記を『t7JJlTDACyc_part_* 10 本存在』に修正 | ⏸ **BLOCKED** (hook 制約・§4 パッチ準備完了) |
| 3 | part_info.json JSON 構文妥当(jq . パス) | ⏸ **apply 後 verify** (§6 step 2) |
| 4 | work/cmd_1449/part_info_fix_report.md 作成 | ✅ (本ファイル) |
| 5 | 実在確認 ls 証跡あり | ✅ (§3.1) |
| 6 | git commit 済み(明示パス) | ⏸ **apply 時に一括 commit** (§6 step 3) |

## 8. 後続提案（別 cmd 化）

- oo_men 視点 Day6 10 parts は **分割済・未 processing** 状態。speaker ID / STT / merge pipeline 通すか否かは本 subtask スコープ外（task notes 明記）。家老判断で別 cmd 化を推奨。
- cmd_1425 の part_info 生成器を video_id fallback 探索対応に改修する恒久対策を別 cmd 化推奨（再発防止）。

## 9. hotfix_notes（本レポート向け）

- **what_was_wrong**: タスク YAML `target_path: work/cmd_1449/part_info_fix_report.md` のみで、AC が要求する `work/cmd_1425/part_info.json` 書換が PreToolUse hook (cmd_1443 p06 scope guard) で阻止された。
- **workaround**: レポートに修正後 JSON 全文と unified diff を埋込・家老 apply 形式に転換。status=BLOCKED_FOR_APPLY で gunshi に通知。
- **proper_fix**: 家老がタスク YAML 発行時、複数 cmd_dir を跨ぐ修正タスクは (a) target_path にリスト指定を許容するか、(b) 書換対象ごとにサブタスク分割するか、(c) hook 設定に一時例外を追加する手順を整備せよ。
