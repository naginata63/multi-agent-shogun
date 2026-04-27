# 📊 戦況報告
最終更新: 2026-04-27 22:46

## 🔄 進行中

### cmd_1501 (high) — faiss index 再構築 + semantic_index_hook flock追加
- subtask_1501a → 足軽2号: rm*.faiss → update → flock追加 → 5分監視 (実行中)

## ✅ 本日の完了（2026-04-27）

| cmd | 内容 |
|-----|------|
| cmd_1502 | ✅ **完遂(22:45・将軍再起動)** silent_fail_watcher noise分類追加+再起動。genai_daily.log除外+noise 6パターン(commit f012247)。PID 1429051で稼働中 |
| cmd_1507 | ✅ **完遂(22:36・足軽4号・軍師QC PASS)** YmExrTL3Ojc 説明欄を標準テンプレで更新済み |
| cmd_1506 | ✅ **完遂(22:34・足軽1号)** day2_3sou_men_only_with_countdown_v2.mp4 YouTube非公開アップ。URL: https://www.youtube.com/watch?v=GCnCUAuL0p8 |
| cmd_1505 | ✅ **完遂(22:20・足軽3号・軍師QC PASS)** tono_edit縦長クロップ正規版(ffmpeg crop+pad)。URL: https://www.youtube.com/watch?v=YmExrTL3Ojc |
| cmd_1500 | ✅ **完遂(22:11・軍師QC PASS)** drawtext式バグ修正。正式式採用・v2=正本。countdown_overlay.md修正commit。git push済 |
| cmd_1504 | ✅ **完遂(21:57・軍師)** dashboard API 設計不整合8点解析完了。推奨cmd 5件。🚨要対応追記済 |
| cmd_1503 | ✅ **完遂(22:06・軍師QC PASS)** Embedding API 404修正。location=us-central1・text-embedding-005・768次元実証。git push済 |
| cmd_1499 | ✅ **完遂(21:53・殿命done)** tono_short_vertical.mp4 YouTube非公開アップ。WB-xCyX-9J0 |
| cmd_1467 | ✅ **殿命done(21:46)** Day6 ECHIDNAサムネ v3案1確定 |
| cmd_1488 | ✅ **殿命done(21:46)** SQLite dual-path writes完遂 |
| cmd_1425 | ✅ **殿命done(21:46)** Day6 3視点DL+集約完了 |
| cmd_1498 | ✅ **完遂(21:28・軍師)** ntfy silent_fail 313件解析。修正cmd3件推奨 |
| cmd_1496 | ✅ **完遂(21:22・軍師QC PASS)** day2_3sou_men_only_with_countdown.mp4 5段drawtext/NVENC。git push済 |
| cmd_1497 | ✅ **殿命done(21:10)** HnDcGHXKJFQ 1080p h264 DL (1.35GB)。後続パイプライン不要 |
| cmd_1487 | ✅ **殿命done(20:51)** Day6エキドナ再修正不要。YouTube非公開版(M7UKrqiI3Eo)で殿了承済 |
| nightly_audit_20260427_stt | ✅ **完遂(02:12・軍師)** CRITICAL1/HIGH6/MEDIUM5/INFO4 |

## 🚨 要対応（殿の御判断必要）

### 🔴 dashboard API 設計不整合修正 — 将軍直接実装 or 家老起票？ (cmd_1504 軍師解析完了)
軍師が計8点不整合確認。推奨cmd 5件。詳細: queue/reports/gunshi_dashboard_api_review_1504.yaml
- **[HIGH]** get_active_cmds/get_recent_done → SQLite移行 (dashboard vs cmd_list 矛盾根絶)
- **[HIGH]** R7 dedup強化 + cmd_id:null 疑似ID付与 (同一警告3-5件複製の根絶)
- **[MED]** R3 age_hours 閾値段階化 / **[MED]** agent.status 二重定義整理 / **[LOW]** first_seen_at記録
→ server.py 改修のため将軍直接実装 or 家老起票どちらか指示されたし

### 🔴 CRITICAL: stt_pipeline.md 手順書が実装と完全乖離（nightly_audit_20260427_stt）
足軽が手順通り叩くと即 argparse error で停止。修正cmd起票要否を判断されたし。
推奨: python3 vocal_stt_pipeline.py INPUT.mp4 --output OUT.json --work-dir DIR 形式に書換

### 🔴 HIGH: MEMORY違反 WhisperX禁止スクリプト残存
transcribe_with_speakers.py (import whisperx) + stt_merge.py L766-797 (whisperx-fallback経路)
削除/廃止cmd起票要否判断されたし。

### ⚠️ 技術的残課題（将来対処）
- pretool_check: /tmp/work/cmd_* でメッセージ誤表示 (動作は正常): 別cmd起票推奨
