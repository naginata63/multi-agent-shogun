# dashboard_lifecycle.sh 拡張手順 (cmd_1461)

## 目的
`scripts/dashboard_lifecycle.sh` に Logic A/B を追加し、dashboard.md の完了 cmd 自動削除を実装する。

## 前提条件
- `scripts/dashboard_lifecycle.sh` 既存コード把握（Read必須）
- `dashboard.md` の `## 🔄 進行中` セクション構造把握
- `dashboard_archive/` 配下へのアーカイブ方式（既存コード参照）

## Step 1: advisor() 呼び出し（実装前）

## Step 2: ファイル確認
```bash
# 既存スクリプト確認
cat scripts/dashboard_lifecycle.sh

# 進行中テーブル構造確認
grep -n "進行中\|## " dashboard.md | head -20
```

## Step 3: Logic A 実装 — clean_inprogress_table() 関数

`scripts/dashboard_lifecycle.sh` の `clean_dashboard_md` 呼び出しの直後、`check_mcp_stragglers` の前に追加せよ。

```bash
# (2.5) 進行中テーブルの✅完了行を削除
clean_inprogress_table() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    log "dashboard.md not found (skip clean_inprogress_table)"
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  awk -v REMOVED_FILE="$removed_lines" '
    BEGIN { in_inprogress = 0; cleaned = 0 }
    {
      line = $0

      # セクション判定
      if (line ~ /^## /) {
        if (line ~ /進行中/) {
          in_inprogress = 1
        } else {
          in_inprogress = 0
        }
        print line
        next
      }

      # 進行中セクション内のテーブル行で✅を含む行を削除対象とする
      # 除外条件:
      #   - 足軽/軍師ステータス行: | [0-9]号 | パターン
      #   - 仕切り行: |---
      #   - ヘッダ行: cmd_id|担当|状態 等のテキスト（✅を含まない）
      if (in_inprogress == 1 \
          && line ~ /^\|/ \
          && line ~ /✅/ \
          && line !~ /^\|[-]+/ \
          && line !~ /^\| *[0-9]号 *\|/ \
          && line !~ /^\| *[a-z_A-Z]* *\|/ ) {
        printf "%s\n", line >> REMOVED_FILE
        cleaned++
        next
      }

      print line
    }
    END { print cleaned > "/dev/stderr" }
  ' "$DASHBOARD_MD" > "$tmp_output" 2> >(read n; echo "$n" > "$count_file"; wait)

  wait
  local cleaned_count
  cleaned_count="$(cat "$count_file" 2>/dev/null || echo 0)"
  rm -f "$count_file"

  if [[ "$cleaned_count" == "0" ]]; then
    log "進行中テーブル: 完了✅行なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "進行中テーブル: ${cleaned_count} 件の✅完了行を検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN: 以下の行を削除予定:"
    while IFS= read -r l; do log "  - ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  # アーカイブ追記
  {
    echo ""
    echo "## 進行中テーブル✅完了行 Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  # flock保護で差し替え
  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "進行中テーブル: ${cleaned_count} 件削除・アーカイブ済み → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}
```

**重要な注意点**:
- awk の `line !~ /^\| *[a-z_A-Z]* *\|/` は足軽ヘッダ行除外のため。
  実際のヘッダ行は `| cmd_id | 担当 | 状態 |` の形。✅を含まないのでこの条件なしでも安全だが念のため。
- `| 2号 |` パターンで足軽ステータス行を除外する。
- 実際の dashboard.md を読んで除外パターンが正しいか確認せよ。

## Step 4: Logic B 実装 — clean_daily_completed_section() 関数

```bash
# (2.7) 「本日の完了」セクションの24h超過分アーカイブ
clean_daily_completed_section() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local now_ts
  now_ts="$(date +%s)"
  local cutoff_ts=$(( now_ts - 86400 ))  # 24h前

  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  awk -v REMOVED_FILE="$removed_lines" -v CUTOFF="$cutoff_ts" '
    BEGIN { in_daily = 0; cleaned = 0; section_empty = 1 }
    {
      line = $0

      if (line ~ /^## /) {
        if (line ~ /本日の完了/) {
          in_daily = 1
          print line
          next
        } else {
          in_daily = 0
        }
        print line
        next
      }

      if (in_daily == 1) {
        # 日付パターン YYYY-MM-DD を検索
        if (match(line, /[0-9]{4}-[0-9]{2}-[0-9]{2}/)) {
          date_str = substr(line, RSTART, RLENGTH)
          cmd = "date -d " date_str " +%s 2>/dev/null"
          cmd | getline line_ts
          close(cmd)
          if (line_ts != "" && line_ts+0 < CUTOFF+0) {
            printf "%s\n", line >> REMOVED_FILE
            cleaned++
            next
          }
        }
        # 日付なし行はそのまま保持
        section_empty = 0
        print line
        next
      }

      print line
    }
    END { print cleaned > "/dev/stderr" }
  ' "$DASHBOARD_MD" > "$tmp_output" 2> >(read n; echo "$n" > "$count_file"; wait)

  wait
  local cleaned_count
  cleaned_count="$(cat "$count_file" 2>/dev/null || echo 0)"
  rm -f "$count_file"

  if [[ "$cleaned_count" == "0" ]]; then
    log "本日の完了セクション: 24h超過行なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "本日の完了セクション: ${cleaned_count} 件の24h超過行を検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    while IFS= read -r l; do log "DRY-RUN:  - ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  {
    echo ""
    echo "## 本日の完了セクション24h超過分 Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "本日の完了セクション: ${cleaned_count} 件削除 → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}
```

## Step 5: --immediate フラグ追加

既存の引数解析ループ内に追加:
```bash
    --immediate) : ;;  # dry_run=0 で即実行（デフォルトと同じだが明示フラグ）
```

## Step 6: 関数呼び出し追加

`clean_dashboard_md || log "ERROR..."` の後、`check_mcp_stragglers` の前に追加:
```bash
clean_inprogress_table || log "ERROR in clean_inprogress_table (continuing)"
clean_daily_completed_section || log "ERROR in clean_daily_completed_section (continuing)"
```

## Step 7: dry-run テスト
```bash
bash scripts/dashboard_lifecycle.sh --dry-run --verbose 2>&1 | tail -30
```
ログに Logic A/B の検出件数が出力されること確認。

## Step 8: production 実行
```bash
bash scripts/dashboard_lifecycle.sh --verbose 2>&1 | tail -30
```
dashboard.md の進行中テーブルから✅完了行が削除されていること確認:
```bash
grep -c "✅" dashboard.md  # production実行前後で比較
```

## Step 9: crontab 更新
```bash
# 現在のcrontabを確認
crontab -l

# 1h おきを追加（重複チェック）
(crontab -l 2>/dev/null; echo "0 * * * * bash /home/murakami/multi-agent-shogun/scripts/dashboard_lifecycle.sh") | sort -u | crontab -
```

## Step 10: memory ファイル作成

`memory/feedback_dashboard_completed_cleanup.md` を新規作成:
```markdown
---
name: dashboard完了cmd自動削除ルール
description: dashboard.md進行中テーブルの✅完了行は自動アーカイブされる・手動で残すな
type: feedback
---

dashboard.md の進行中テーブルに✅完了行を残してはならない。
`scripts/dashboard_lifecycle.sh` が自動削除する (Logic A/B)。

**Why:** 殿指摘(2026-04-25 10:05)「なんで完了したものにマークしてのこすの・仕組み化しろ」。
家老の「見える化」思想で完了済cmd をマーク付き残存させていた慢性問題を是正。

**How to apply:**
- cmd完了時に家老が進行中テーブルから削除する必要なし（lifecycle.sh が自動処理）
- ただし「殿判断要」などアクティブな 🚨 要対応 行は手動管理継続
- 1h おき cron で自動削除 (追加: `0 * * * *`)
- アーカイブ: `dashboard_archive/YYYY-MM.md` に移動済み
```

## Step 11: advisor() 呼び出し（完了前）

## Step 12: git commit
```bash
git add scripts/dashboard_lifecycle.sh memory/feedback_dashboard_completed_cleanup.md memory/MEMORY.md
git diff --cached  # 意図外ファイルがないか確認
git commit -m "feat(cmd_1461): dashboard_lifecycle拡張 — 進行中✅完了行自動削除+1hcron"
git push origin main
```

## Step 13: report 作成・inbox 送信
`queue/reports/ashigaru2_report_subtask_1461a.yaml` を作成し、gunshiに QC 依頼送信。
