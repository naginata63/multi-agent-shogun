# cmd_1684-A: dashboard_api_usage.md 全面更新 — 報告書

## 成果物

- `shared_context/procedures/dashboard_api_usage.md` 更新 (+98行)

## 更新内容

### GET系 追加 (5エンドポイント)

| エンドポイント | 用途 |
|---------------|------|
| `/api/cmd_next_id` | 次cmd_id自動採番 (家老がcmd起票時に使用) |
| `/api/inbox_stream` | SSE inboxリアルタイム配信 (Monitor起動用) |
| `/api/list_panels_json` | manga panels JSONファイル一覧 |
| `/api/load_raw_candidates` | 候補生JSONファイル読込 |
| `/api/load_panels_json` | panels JSONファイル読込 |

### POST系 追加 (6エンドポイント)

| エンドポイント | 用途 |
|---------------|------|
| `/api/cmd_status_change` | cmd status変更 (殿/将軍用。8状態対応) |
| `/api/cmd_cancel` | cmd cancel + 関連subtask全件自動cancelled + agent inbox通知 |
| `/api/task_update` | タスクstatus更新 (blocked時はblocked_reason自動記録) |
| `/api/generate_panels_llm` | LLM panels生成 |
| `/api/regenerate_partial_with_gemini` | Gemini部分再生成 |
| `/api/suggest_director_notes` (詳細化) | director_notes LLM生成 |

### 追加セクション

- 各endpointの **payload例** (curl実行例に追記)
- 各endpointの **response例** (JSON形式で新規セクション追加)
- **部下別推奨シナリオ** 更新 (家老: cmd_status_change/task_update, 足軽: cmd_next_id, 将軍: cmd_cancel)
- **キー名サマリ表** 更新 (10エンドポイント→12エンドポイント)

## grep点検: server.py 全27エンドポイント確認

| # | Path | Method | 旧doc記載 | 新doc記載 |
|---|------|--------|----------|----------|
| 1 | /api/dashboard | GET | ✓ | ✓ |
| 2 | /api/job_status | GET | ✓ | ✓ |
| 3 | /api/cmd_list | GET | ✓ | ✓ |
| 4 | /api/cmd_detail | GET | ✓ | ✓ |
| 5 | /api/task_list | GET | ✓ | ✓ |
| 6 | /api/inbox_messages | GET | ✓ | ✓ |
| 7 | /api/dashboard_md | GET | ✓ | ✓ |
| 8 | /api/cmd_next_id | GET | ✗ | ✓ (追加) |
| 9 | /api/report_detail | GET | ✓ | ✓ |
| 10 | /api/report_list | GET | ✓ | ✓ |
| 11 | /api/list_panels_json | GET | ✗ | ✓ (追加) |
| 12 | /api/load_raw_candidates | GET | ✗ | ✓ (追加) |
| 13 | /api/load_panels_json | GET | ✗ | ✓ (追加) |
| 14 | /api/agent_health | GET | ✓ | ✓ |
| 15 | /api/inbox_stream | GET (SSE) | ✗ | ✓ (追加) |
| 16 | /api/save_panels_json | POST | △(1行) | ✓ (詳細化) |
| 17 | /api/suggest_director_notes | POST | △(1行) | ✓ (詳細化) |
| 18 | /api/generate_panels_llm | POST | ✗ | ✓ (追加) |
| 19 | /api/regenerate_partial_with_gemini | POST | ✗ | ✓ (追加) |
| 20 | /api/cmd_create | POST | ✓ | ✓ |
| 21 | /api/cmd_status_change | POST | ✗ | ✓ (追加) |
| 22 | /api/cmd_cancel | POST | ✗ | ✓ (追加) |
| 23 | /api/inbox_write | POST | ✓ | ✓ |
| 24 | /api/task_create | POST | ✓ | ✓ |
| 25 | /api/task_update | POST | ✗ | ✓ (追加) |
| 26 | /api/dashboard_update | POST | ✓ | ✓ |
| 27 | /api/report_create | POST | ✓ | ✓ |
| 28 | /api/inbox_mark_read | POST | ✓ | ✓ |

## Acceptance Criteria チェック

- [x] server.py の全 /api/ エンドポイントが dashboard_api_usage.md に記載
- [x] cmd_status_change/cmd_cancel/task_update/cmd_next_id の payload例・response例あり
- [x] 部下別推奨シナリオ更新済
- [x] git commit 済 (2295f2c)
- [x] 報告書 queue/reports/2026-05-12_cmd_1684_a_api_manual.md 格納
