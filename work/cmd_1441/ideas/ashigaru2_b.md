# 足軽2号アイデア出し（カテゴリ b: cmd done化漏れ棚卸し）

cmd_1441 Phase A 足軽2号担当分。`queue/shogun_to_karo.yaml` の `status: in_progress / pending / on_hold` 全件を棚卸しし、実質完了だが未done化のcmdを特定する。

作成: 2026-04-24 13:30 / ashigaru2

task YAML 要件: 現状 / やれてないこと / アイデア の 3セクション・最低5アイデア。

---

## 現状

### 1. 非done cmd の総数（cmd_1441自身を除く）

`shogun_to_karo.yaml` (5,413行) の `awk '/^- id: cmd_/{id=$3} /^  status:/{print id, $2}'` 集計結果:

| status | 件数 | cmd 一覧 |
|--------|------|---------|
| in_progress | 4 | cmd_1348 / cmd_1393 / cmd_1424 / cmd_1441（現行・除外）|
| pending | 2 | cmd_1417 / cmd_1420 |
| on_hold | 1 | cmd_1412 |
| superseded | 1 | cmd_1292 |
| cancelled | 1 | cmd_1334 |

**actionable な非done対象: 6件（cmd_1348 / 1393 / 1412 / 1417 / 1420 / 1424）**。

### 2. 各cmdの実態 vs YAML status の差分

| cmd | YAML status | 実態（dashboard archive / 成果物確認） | 判定 |
|-----|-------------|---------------------------------------|------|
| cmd_1348 | in_progress（+ status:cancelled重複） | `scripts/dingtalk_qc_loop.py` から「エラーあり」grep=0・「無効→承認」フロー反映済 | **done化漏れ**（git untracked が阻害要因） |
| cmd_1393 | in_progress（+ command内に status:done混入） | `scripts/pretool_check.sh` + `scripts/posttool_cmd_check.sh` 両方実在・dashboard_archive L41 に「✅ 軍師PASS commit 6b33bcb」 | **done化漏れ確定** |
| cmd_1412 | on_hold | dashboard_archive L28「✅ YouTube非公開アップ: https://www.youtube.com/watch?v=nG6dMBspc4M」 | **done化漏れ確定** |
| cmd_1417 | pending | 救出対象 cmd_1415 は既に完了済（dashboard_archive L20: commits 8c26ce6/0d7a947/d4f2e0b）。purpose moot | **stale**（cancelled相当） |
| cmd_1420 | pending | `tono_edit_vertical.mp4` 実在 + dashboard_archive L27「✅ YouTube非公開アップ jgmXApCnPxY」 | **done化漏れ確定** |
| cmd_1424 | in_progress | dashboard_archive L17「✅ v2 アップ 2_QYghuH198」+ L15「cmd_1427でゼピュロスv3 D7JYECifQ1M」+ `work/cmd_1424/` に成果物アーティファクト多数 | **done化漏れ確定** |

### 3. 副次発見（YAMLデータ整合性問題）

棚卸し中に**重複status:フィールド**を2件発見:

- **cmd_1348**: 357行目 `status: cancelled` と 398行目 `status: in_progress` の両方を持つ → YAMLパーサ的には後者勝ち、だが意味的に矛盾
- **cmd_1393**: 2113行目 `status: in_progress` だが、command ヒアドキュメント内 2079行目に `  status: done` という擬似フィールド混入（実態は command 文字列の一部・grepすると拾われる）

これは grep ベース集計を歪める bug source。

---

## やれてないこと

1. **dashboard と shogun_to_karo.yaml の status 同期がない**: dashboard archive で「✅完了」と書かれた cmd の YAML status が更新されないケース 5/6 件発覚。家老が dashboard 更新時に YAML status も同時 Edit するルールが未明文化
2. **「非公開アップ完了 = cmd 完了」の判定自動化なし**: ntfy で「🎬 YouTube非公開アップ: ... URL」が送られた時点で対応 cmd の status を自動 done 化する hook が未実装
3. **重複 status:キー の lint 検知なし**: cmd_1348/1393 のような重複フィールドが入っても誰も気付かない（YAMLは valid だが意味的に NG）
4. **command ヒアドキュメント内に YAML 風文字列混入の検知なし**: cmd_1393 の `  status: done` 紛れ込みは「インデント2スペース＋既知フィールド名」の正規表現で機械検知可能だが未実施
5. **on_hold / pending の自動escalation がない**: cmd_1412 (on_hold) は1週間放置されても何の通知も来ない。「on_hold 7日超 → ntfy で殿に判断仰ぐ」自動再起動ルールが欲しい
6. **cmd 救出メタcmd（cmd_1417タイプ）の自動close なし**: 「他cmdを救出する目的のcmd」は救出対象が done になった瞬間に purpose moot になるが、自動でリンクして close する仕組みがない
7. **`scripts/dingtalk_qc_loop.py` が gitignored**: cmd_1348 AC#4「git commit & push済」が満たせない構造的問題。`.gitignore` whitelistに `!scripts/dingtalk_qc_loop.py` 追加が漏れている

---

## アイデア（7項目）

### 即時対応（Phase B subtask 化推奨）

1. **shogun_to_karo.yaml status 一括更新（即時実行可）**
   下記5件を done 化する単発タスクを切る:
   - cmd_1393 → done（重複status除去含む）
   - cmd_1412 → done
   - cmd_1417 → done（cmd_1415 完了で purpose 達成、resolution 欄に「cmd_1415完了で moot」記載）
   - cmd_1420 → done
   - cmd_1424 → done
   cmd_1348 は別途（gitignore whitelist追加 → git commit → done化の3段階必要）。
   `cmd_1334` の重複 cancelled キーも同時クリーンアップ。

2. **cmd_1348 救出（dingtalk_qc_loop.py 正規追跡化）**
   - `.gitignore` に `!scripts/dingtalk_qc_loop.py` 追記
   - git add scripts/dingtalk_qc_loop.py + commit「feat(cmd_1348): dingtalk_qc_loop.py を whitelist化（『エラーあり』フロー廃止対応）」
   - shogun_to_karo.yaml cmd_1348 status を done に更新（重複 status:cancelled 除去）

### 仕組み化（再発防止）

3. **「ntfy🎬完了 → YAML status 自動 done 化」hook**
   `scripts/ntfy.sh` を wrap して「🎬 YouTube非公開アップ」「✅ cmd_XXXX 完了」パターン検知時に対応 cmd_id を抽出 → `shogun_to_karo.yaml` の該当 cmd の `status:` を done に sed 置換。家老の手動更新漏れ対策。

4. **YAML lint hook（PreToolUse）追加**
   `scripts/pretool_check.sh` に shogun_to_karo.yaml Edit 時の以下チェック追加:
   - 同一 cmd 配下に `status:` キーが2回出現 → BLOCKED
   - command ヒアドキュメント内に `^  status: ` 行がある → WARNING（インデント崩れ疑い）
   実装は yq + awk で30行以下。

5. **dashboard_archive ↔ shogun_to_karo.yaml 整合性 nightly check**
   nightly_audit に「dashboard_archive で `✅` 付きの cmd_XXXX が shogun_to_karo.yaml で done になっているか」突合チェック追加。乖離検知時は ntfy 通知。

6. **on_hold/pending の自動 escalation cron**
   `scripts/cmd_status_aging_check.sh` 新設。`status: on_hold` または `status: pending` が timestamp から7日超のcmdを検出 → 朝一 ntfy で殿に「cmd_XXXX を done/cancel/再駆動 のどれにするか」確認通知。

### メタcmd 改善

7. **救出メタcmd の自動 close リンク**
   cmd YAMLに `resolves_cmd: cmd_XXXX` フィールド追加。対象 cmd が done になった瞬間に親 cmd（救出側）も自動 done 化。今回 cmd_1417 → cmd_1415 のような関係を機械的に解消。

---

## まとめ（Phase B への引継ぎ）

- **本md内訳**: 現状（6cmd実態確認 + YAMLデータ整合性2件） / やれてないこと（7項目） / アイデア（7項目・即時2件＋仕組化4件＋メタ改善1件）
- **緊急度高**: アイデア①（5cmd 一括 done 化）は即時実行可・15分作業・他Phase進行中も並列で潰せる
- **横断インパクト大**: アイデア③（ntfy → status 自動 done）と④（YAML lint）はカテゴリj（軍師横断）と重複する可能性あり → Phase B 統合時に gunshi_j.md と突合
- **構造的問題**: `scripts/` whitelist 運用は新規追加忘れリスクが高い（cmd_1348 が実例）。カテゴリc（ファイル蓄積整理）と協調検討推奨

優先度判定は Phase A スコープ外。subtask_1441_phaseB の統合作業で他足軽 a/c-i + 軍師 j + 将軍 horizontal の ideas と突合し、3軸評価（緊急度/コスト/効果）で並列化する。

以上。
