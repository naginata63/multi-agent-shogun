# 夜間監査修正: インフラスクリプト（cmd_1415b）

## 対象
scripts/fix_panes.sh, shutsujin_departure.sh, scripts/ntfy_listener.sh, scripts/posttool_yaml_check.sh

## 参照レポート
queue/reports/gunshi_report_nightly_audit_20260418_infra.yaml
queue/reports/gunshi_report_nightly_audit_20260415_infra.yaml

## 修正内容

### NEW-01: fix_panes.sh CLI Adapter連携
- 現状: L54-72でcli_adapter.shを読み込み済みだが、実際のGLM判定は機能しているか要確認
- 確認: fix_panes.shがlib/cli_adapter.shをsourceしており、build_cli_command()を呼んでいることを確認
- もし既に実装済みなら修正不要（確認のみ）

### NEW-02: shutsujin_departure.sh clean mode YAML形式
- L356-366: dict形式 `task:\n  task_id: null` をlist形式に変更
- 修正後:
```yaml
# 足軽N専用タスクファイル
tasks:
- task_id: null
  parent_cmd: null
  description: null
  target_path: null
  status: idle
  timestamp: ""
```
- gunshi.yamlも同様にlist形式に

### 既報1: ntfy_listener.sh L238
- `${NTFY_TOKEN:-${NTFY_USER:-none}}` の実値がログに出力される問題
- ログ出力行の該当部分を `${NTFY_TOKEN:+<set>}/${NTFY_USER:+<set>}` のようにマスク化

### 既報2: posttool_yaml_check.sh
- L3: `CLAUDE_TOOL_INPUT`環境変数→stdin方式に変更
- `python3`→`.venv/bin/python3`に統一

## テスト手順
```bash
bash -n scripts/fix_panes.sh
bash -n shutsujin_departure.sh
bash -n scripts/ntfy_listener.sh
bash -n scripts/posttool_yaml_check.sh
# fix_panes.shでGLM pane検出時のget_cli_type()戻り値確認
source lib/cli_adapter.sh && get_cli_type ashigaru1  # "glm"が返ること
```

## Git
```bash
git add scripts/fix_panes.sh shutsujin_departure.sh scripts/ntfy_listener.sh scripts/posttool_yaml_check.sh
git commit -m "fix(cmd_1415b): インフラスクリプトGLM対応+YAML形式+stderr統一"
```

## advisor()必須
実装前と完了前の2回呼ぶこと。
