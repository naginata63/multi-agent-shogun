# 📊 戦況報告
最終更新: 2026-04-24 15:21

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

---

## 🚨 要対応（殿の御判断必要）

~~🔴 cmd_1434 polish~~: cmd_1437+cmd_1438で全件解消済み

### 🚨 cmd_1441 Phase B2 完了 → 殿判断要請（execution_plan_v2.md + decision_gates_v2.md）

軍師 subtask_1441_phaseB2 完了（commit 94383d7）。殿2重指示反映済み: (A)D4=A1-a復活確定+(B)動画系4件保留。優先度A=3件(今夜)/B=5件(今週)/C=7件(2週内)/保留=4件/MCN別軸=1件。

**🚨 殿判断要請6件（未決ゲート）:**
| # | 判断事項 | 軍師推奨 |
|---|---------|---------|
| **D10(新設・最優先)** | capability_tiers モデルmapping（L1-L6 × GLM/Sonnet/Opus[1m]） | **Option β**: L1-L3=GLM / L4-L5=Sonnet / L6=今夜限Opus[1m]・平時Sonnet |
| D3 | skills/ whitelist vs 全体tracked | 全体tracked（.gitignoreからskills/除外・根本解決） |
| D5 | instructions/ 26file archive化 OK? | archive化（git mv・履歴保持） |
| D6 | MEMORY.md Session Start 変更可否（292行→100行index化） | core/*.md分割+shogun.md同期更新 |
| D7訂正 | MCP削除対象 **10件 or 11件**（expression_index.jsonが現役2D資産・CDP漫画パネル用・足軽5号発見） | **要殿判断**: (A) expression_index.json温存で10件削除 or (B) 11件全削除 |
| D9 | dozle_kirinuki submodule履歴書換 OK? | backup+force-with-lease |
| D8(別軸継続) | MCN v2（ガイドラインURL/PDF+送信チャネル+AI3段構え承認） | 殿外部情報依存・待機 |

**進行状況:**
- 足軽5号 subtask_1441_p20 **STOP中**: D7対象entity 11件（内3D=10・現役2D=1）判明→殿判断待ち。archive/3d_pipeline_2026q1.md には11件全転記済（非破壊）
- 軍師 idle（phaseB2完了）
- Wave A着手は殿判断後

詳細: `work/cmd_1441/execution_plan_v2.md` + `decision_gates_v2.md` (commit 94383d7)

### 🚨 スキル化候補（殿承認要）
- **skill-candidate-tracker**: スキル化候補のトラッキング・棚卸しツール化（足軽7号 subtask_1441ghi で浮上・skill_candidate:true）
- ~~yt-dlp-js-runtimes-fix~~: cmd_1439 でスキル化完了 commit c179f8a+85e1e32

### ⚠️ 技術的残課題（優先度低）
- **dozle_kirinukiサブモジュール push不可**: gcloud SDK 194MB超過 → git-lfs移行 or 履歴書換が必要
- **disk使用率88%（残116GB）**: Day6 MIX前に要確認（4視点×約50GB消費見込み）
- **cmd_1425d2 part_info.json誤記**: 『oo_men不在』は誤り・実態は `t7JJlTDACyc_part_*` 10本存在（軍師qc_1425d2見落とし・Phase Bで修正）
- **Day6 4視点MIX codec混在**: charlotte=vp9 / 他=h264 → concat -c copy不可・事前トランスコード必須（Day6 MIX cmd起票時に明示必要）

### 🔧 cmd_1441で浮上した技術負債（足軽hotfix報告より）
- **家老タスクYAMLのtarget_path欠落**: cmd_1441で全足軽が pretool_check.sh BLOCKに遭遇→自力workaround（3/4/5号のhotfix_notes報告）。家老のtask_design_checklistに `target_path必須` を追加せよ
- **bloom_routing 参照破綻**: CLAUDE.md/karo.mdがsettings.yaml→bloom_routing参照するが当該キー不在（足軽4号発見）
- **.gitignore work/配下**: git add -f で強制追加運用中（足軽4号指摘）→ work/ は.gitignoreから除外 or 運用見直し

---

## 🔄 進行中

| cmd | 担当 | 状態 |
|-----|------|------|
| cmd_1436 | — | ✅ **完了** todolist.md作成済み(将軍) |
| cmd_1441 | 軍師/足軽5号 | ⏸ Phase B2 完了(execution_plan_v2.md) / 足軽5号 D7 判定待ち / 殿判断要請6件 |
| cmd_1437 | 足軽1号 | ✅ 収益化進捗セクション削除完了 commit 73fc9c0c+d2dde95 |
| cmd_1438 | 軍師 | ✅ PASS メンバー名日本語化/命名衝突/caption/by_duration/Chart destroy全完了 |

---

## 足軽・軍師 状態

| 足軽 | CLI | 状態 | 現タスク |
|------|-----|------|---------|
| 1号 | Opus[1m] | ✅ idle | subtask_1441a 殿判断でskip(重複作業回避)・cmd_1439完了済 |
| 2号 | Opus[1m] | ✅ idle | subtask_1441b 完了(ashigaru2_b.md 113行・軍師qc PASS) |
| 3号 | Opus[1m] | ✅ idle | subtask_1441c 完了(ashigaru3_c.md 10アイデア/f294637) |
| 4号 | Opus[1m] | ✅ idle | subtask_1441d 完了(ashigaru4_d.md/bloom_routing破綻発見) |
| 5号 | Opus[1m] | ⏸ STOP | subtask_1441_p20(D7) archive転記済・delete待機(expression_index.json判定待ち) |
| 6号 | Opus[1m] | ✅ idle | subtask_1441f 完了(ashigaru6_f.md 114行/8案/040ff46) |
| 7号 | Opus[1m] | ✅ idle | subtask_1441ghi 完了(ashigaru7_ghi.md 206行/22案/6c704fb) |
| 軍師 | Opus[1m] | ✅ idle | subtask_1441_phaseB2 完了(execution_plan_v2.md+decision_gates_v2.md/94383d7) |

---

## ✅ 本日の完了（2026-04-24）

| cmd | 内容 |
|-----|------|
| cmd_1439 | ✅ **完了** yt-dlp-js-runtimes-fix スキル化（SKILL.md 135行）軍師qc_1439a PASS commit c179f8a+85e1e32 |
| cmd_1440 | ✅ **完了** claude-mem Phase1 C/J/D三項目完遂（cmem_quickstart.md+cmem_search.sh+worker LAN公開）軍師qc_1440j/qc_1440cd PASS commit 1517ccc |
| cmd_1425 | ✅ **完了** Day6 3視点DL+集約（tsurugi/hendy/charlotte 各9パート・part_info.json git commit d9fce67）|
| cmd_1434 | ✅ **完了** Phase1+2+3+by_duration4区分全完了。generate_dashboard.py冪等生成対応済み・6セクション表示確認 git f5408ab |
| cmd_1437 | ✅ **完了** 収益化進捗セクション削除（YPP達成済みのため不要）commit 73fc9c0c+d2dde95 |
| cmd_1438 | ✅ **完了** ダッシュボードpolish7項目（日本語化/命名衝突/caption/by_duration/Chart destroy全対応）Phase3最終形態確立 |
| cmd_1436 | ✅ **完了** claude-mem活用分析+todolist.md作成（軍師分析→将軍統合） |
| nightly_audit_20260424_video | ✅ 動画制作系矛盾検出（CRITICAL×0 HIGH×0・MEDIUM×1 outro stderr deadlock）|
| cmd_1428 | ✅ done化（殿判断: YouTube非公開アップ完結）|
| cmd_1411/1413/1414 | ✅ done化（DoZ5日目ヒーラー漫画ショート・ゼピュロス3版投稿済みで終了・殿判断）|

> 過去の完了記録 → `dashboard_archive_2026-04.md`

---

## APIキー状況
- **Vertex AI ADC**: ✅ 正常
- **モデル**: ✅ 全エージェント Opus[1m] 統一稼働中（YAML syntax修正済）

## チャンネル実績（2026-04-24更新）
- 登録者**2,740人** / 総再生**348万回** / 動画**74本**
- 過去365日視聴時間: 横長**4,786h** / ショート**19,360h**
- YPP条件: 横長4,786h > 4,000h ✅ / 登録2,740 > 1,000 ✅ → **条件達成・YouTube判定通知待ち（1週間遅延中・あす明後日見込み）**
- ドズル社MCN加入・ライセンス契約: 未申請（申請文v1ドラフト work/dozle_application/）

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
