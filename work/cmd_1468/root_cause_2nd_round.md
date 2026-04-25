# cmd_1468 root cause report — cron 4エラー再発 真因究明 (2nd round)

- 発令: 2026-04-25 12:52 (cmd_1468)
- 担当: ashigaru3
- 完了: 2026-04-25 13:11

## サマリ

cmd_1448で修正したC01/C02/C04/C10が30分毎に再検知され続けていた原因は **`cron_health_check.sh`の`tail -n 200`による古いログ再スキャン** だった。
加えてC05/C09/C14の新規エラーも混在していた。

| ID  | 真因 | 詳細 | 対応 |
|-----|------|------|------|
| C01 | STALE + 新規一時 | 旧Traceback残留 + DNS一時障害(Discord) | offsetで解決(旧分は再検知なし) |
| C02 | 新規(既知) | FAISS index read error (ntotal≠metadata) | cmd_1448フォローアップ。別cmdでFAISS再構築必要 |
| C05 | 新規(1回) | dashboard_lifecycle.sh 02:02失敗 | 1回限り。offsetで旧エラー再検知なし |
| C09 | 新規(2件) | (a) shogun_to_karo.yaml YAML構文破壊 (b) queue/reports/archive rmdir失敗 | (a) YAML修復 (b) slim_yaml.py に try/except追加 |
| C10 | 新規(5件) | projects/projects/ 下にdangling symlink 5件 | symlink 5件削除 |
| C14 | STALE | 2026-04-24T23:25:18の古いエラー(14行しかないログでtail -200に常時含まれる) | offsetで解決 |

## 根本原因

### 1. cron_health_check.sh のオフセット管理欠如

`tail -n 200`で毎回末尾200行をスキャンする仕様。ログに新規追記がなくても、古いERROR/Tracebackが200行以内に残っていれば再検知し続ける。

- 小さいログ(C14: 14行、C05: 1行)は全行がスキャン対象 → 古いエラーが永続検知
- ログローテ後も新しいログが短い場合は同じ問題が再発

**修正**: バイトオフセット追跡を導入。
- 初回: 従来通り`tail -n 200`でスキャン
- 2回目以降: 前回のバイト位置から新規追記分のみスキャン
- ログローテ(ファイル縮小)検知時は全件スキャンにフォールバック

### 2. C09: shogun_to_karo.yaml YAML構文破壊

行258でcmd_1292の後に別コマンドの内容が`command: |`なしで混入。YAMLパーサがblock mapping error。
- 原因: 過去のshogun書き込み時のフォーマット崩れ
- 行632でも別の箇所(bug_010)の`{ echo "ERROR:..." }`がフローマッピングとして誤解析
- 行4823で`\n`による行マージ残骸
- 修正: 3箇所のYAML構文エラーを修復

### 3. C09: slim_yaml.py rmdir失敗

`queue/reports/archive/`に33個の非YAMLファイル(screenshot等)が残存。`.yaml`ファイルが0個でもディレクトリが空でないため`rmdir()`が`OSError`。
- 修正: `try/except OSError`で安全にスキップ

### 4. C10: 新しいdangling symlink 5件

`projects/projects/dozle_kirinuki/speaker_profiles/pretrained_models/spkrec-ecapa-voxceleb/`に5件のHuggingFace cacheへのsymlink。
キャッシュがクリアされてdangling化。rsyncがcode 23を返す。
- 注意: `projects/projects/`という二重パス(誤って作成されたディレクトリ)
- 修正: symlink 5件 + 空ディレクトリ2階層を削除

## 修正ファイル

| ファイル | 修正内容 |
|----------|---------|
| `scripts/cron_health_check.sh` | バイトオフセット追跡機構追加(TAIL_LINES→OFFSET_DIR) |
| `scripts/slim_yaml.py` | L367: rmdirをtry/except OSErrorでラップ |
| `queue/shogun_to_karo.yaml` | 行258/632/4823のYAML構文エラー3件修復 |

## 削除ファイル

| パス | 理由 |
|------|------|
| `projects/projects/dozle_kirinuki/speaker_profiles/pretrained_models/spkrec-ecapa-voxceleb/{5 files}` | dangling symlink |

## 検証

```
1回目 (初回フォールバック): checked=11 hit=6 (旧エラー検出 → offset保存)
2回目 (offsetスキャン):     checked=11 hit=0 (新規追記なし → 検出0件)
```

次回cron自動実行(13:30)で hit=0 を再確認予定。

## AC verify

| AC | 結果 |
|----|------|
| C01/C02/C05/C09/C10/C14 各エラーの真因確定 | ✅ STALE(C01/C14) + 新規(C02/C05/C09/C10) |
| 古いログ再検知: offset管理修正完了 | ✅ cron_health_check.sh byte-offset追跡実装 |
| 真の新規エラー: 再修正完了 | ✅ C09 YAML修復 + slim_yaml修正 + C10 symlink削除 |
| 30分後cronサイクル観察で再発0件確認 | 🕐 13:30自動実行で確認予定 |
| root_cause_2nd_round.md 存在・詳細記録 | ✅ 本ファイル |
| 軍師QC PASS | 🕐 通知後 |
| git commit + push完了 | 🕐 commit後 |

## フォローアップ (別cmd推奨)

1. **FAISS index 完全再構築**: C02のFAISS RuntimeError解消。cmd_1448フォローアップから引き継ぎ。
2. **shogun_to_karo.yaml 同時書き込み防止**: YAML構文破壊(行258)の再発防止。flock導入推奨。
3. **dashboard_lifecycle.sh 失敗原因調査**: C05の02:02失敗の根本原因(1回限りか周期的か)。
