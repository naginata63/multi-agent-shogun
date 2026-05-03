# cmd_1612 完了報告書

**日時**: 2026-05-04  
**cmd**: cmd_1612  
**担当**: ashigaru1 (実装) / gunshi (QC) / karo (完了処理)

## 概要
pretool_check.sh に CHK11 を追加し、`curl --data @/tmp/*.json` 形式の API 投入を永久 BLOCK。
全 payload を `queue/cmd_payloads/` に集約し git で監査追跡可能にした。

## 実施内容

| # | 内容 | 結果 |
|---|------|------|
| CHK11実装 | `scripts/pretool_check.sh:682-692` — -d/--data/--data-raw/--data-binary 4フラグ対応 | ✅ |
| /tmp migration | `/tmp/*.json` 44件 → `queue/cmd_payloads/archive_20260504_tmp_migration/` | ✅ |
| ドキュメント追記 | `shared_context/procedures/dashboard_api_usage.md L94` payload必須ルール | ✅ |
| 全員通知 | ashigaru1-7 + gunshi に /tmp禁止 cmd_correction 送信 | ✅ |

## QC結果
gunshi QC PASS (AC 5/5) — commit dc75fff → push完了

## Follow-up (LOW)
- F1: inbox_write 短文200文字例外がCHK10で実装済か別途確認推奨
- F2: archive は .gitignore でローカル保全のみ (git管理外)
