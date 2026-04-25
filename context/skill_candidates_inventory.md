# Skill Candidates Inventory (自動棚卸し)

**最終更新**: 2026-04-25T02:52:05 / skill-candidate-tracker (cmd_1447)

`queue/reports/*.yaml` の `skill_candidate.found=true` を横断抽出した一覧。
同名候補は初出/最終言及日で集約。Python/PyYAML でパース (旧形式 bare + 新形式 nested 両対応)。

## サマリー

- 総候補数: **10**
- 🚨 PENDING (未スキル化): **2**
- ✅ IMPLEMENTED (スキル化済): **3**
- 🟡 NAMELESS (旧形式・name欠落): **5**
- 🔁 2回以上言及 (ashigaru.md skill化基準クリア): **2**
- 🆕 直近7日以内初出 (cutoff=2026-04-18): **2**

## 候補一覧 (PENDING 先頭・last_seen 降順)

| # | skill_name | status | mentions | first_seen | last_seen | purpose | evidence |
|---|-----------|--------|----------|-----------|----------|---------|----------|
| 1 | `pretool-target-path-fix` | 🚨 PENDING | 1 | 2026-04-17 | 2026-04-17 | pretool_check.shのtarget_path取得をstatus: in_progressにも対応させる修正パターン | subtask_1408e(ashigaru3) |
| 2 | `bigquery-embedding-batch` | 🚨 PENDING | 1 | 2026-04-02 | 2026-04-02 | 大量字幕データのembedding生成・BigQuery投入バッチシステム (batch_continue.py) | subtask_1071c(ashigaru2) |
| 3 | `(nameless)` | 🟡 NAMELESS | 1 | 2026-03-26 | 2026-03-26 | 「ナレーション動画制作パイプライン」— VOICEVOX音声合成 + 画像スライドショー + ffmpeg合成を 自動化するスクリプト。受託案件が継続する場合、テンプレート化して再利用可能。 入力: 原稿テキスト + 画像プロンプトリスト  | subtask_952a(gunshi) |
| 4 | `(nameless)` | 🟡 NAMELESS | 1 | 2026-03-26 | 2026-03-26 | 「AIショートドラマ制作パイプライン」— Claude脚本→Gemini画像→Kling動画化→ElevenLabs音声→ffmpeg合成の自動化。 受託案件が継続する場合、入力（原稿テキスト）→出力（縦型ショートドラマMP4）の パイプラ | subtask_952b(gunshi) |
| 5 | `(nameless)` | 🟡 NAMELESS | 2 | 2026-03-23 | 2026-03-23 | minecraft_skin_to_rig: マイクラスキンPNG→Blenderリグ付きキャラ変換スクリプト (Method B, 6パーツ, vertex group + armature modifier) | cmd876(ashigaru1), cmd876(gunshi) |
| 6 | `(nameless)` | 🟡 NAMELESS | 1 | 2026-03-21 | 2026-03-21 | render_with_remotion()のPopen+setsidラッパーは、他のsubprocess.run()呼び出し（Demucs, WhisperX等）にも適用可能なユーティリティ関数化の候補 | cmd864(gunshi) |
| 7 | `(nameless)` | 🟡 NAMELESS | 1 | 2026-03-14 | 2026-03-14 | Gemini Flash Liteマルチラン品質分析 — リサイクル検出・クロスバリデーション・統合 | subtask_643a(gunshi) |
| 8 | `yt-dlp-js-runtimes-fix` | ✅ IMPLEMENTED | 2 | 2026-04-24 | 2026-04-24 | yt-dlp使用時にn-challenge solving failedが発生したら --js-runtimes node を追加で解決 | subtask_1425c2(ashigaru4), qc_1425c2(gunshi) |
| 9 | `skill-candidate-tracker` | ✅ IMPLEMENTED | 1 | 2026-04-24 | 2026-04-24 | queue/reports/ を週次 grep で skill_candidate:found=true を集計→dashboard🚨セクションに自動反映するトラッキング skill（本タスクの H-2 相当） | subtask_1441ghi(ashigaru7) |
| 10 | `master-telop-two-stage` | ✅ IMPLEMENTED | 1 | 2026-04-25 | 2026-04-25 | 動画MIX (4視点等) でテロップを後加工する標準ワークフロー。master.mp4 + with_telop.mp4 二段保存方式 | subtask_1489a(ashigaru3) |

## 🔁 2回以上言及された候補 (skill化基準クリア)

- **`(nameless)`** (NAMELESS, 2回) — minecraft_skin_to_rig: マイクラスキンPNG→Blenderリグ付きキャラ変換スクリプト (Method B, 6パーツ, vertex group + armature modifier)
- **`yt-dlp-js-runtimes-fix`** (IMPLEMENTED, 2回) — yt-dlp使用時にn-challenge solving failedが発生したら --js-runtimes node を追加で解決

## 🆕 直近7日以内 初出候補 (軍師 quarterly review 観察対象)

- **`yt-dlp-js-runtimes-fix`** (IMPLEMENTED) — first_seen=2026-04-24
- **`skill-candidate-tracker`** (IMPLEMENTED) — first_seen=2026-04-24

---

## 運用

- **weekly cron**: `shared_context/cron_inventory.md` C14 参照 (毎週日曜深夜)
- **即時再生成**: `/skill-inventory` slash command または `bash skills/skill-candidate-tracker/collect.sh --write`
- **判定ロジック**: `skills/<name>/` 実在で IMPLEMENTED。なければ PENDING。name 欠落の旧形式 → NAMELESS (軍師レビューで name 付与 or 見送り判断)