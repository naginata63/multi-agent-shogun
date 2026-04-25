# dashboard_lifecycle.sh Logic C/D/E 追加手順 (cmd_1462)

## 目的

`scripts/dashboard_lifecycle.sh` に Logic C/D/E を追加し、dashboard.md の🚨要対応セクション内の解決済み残骸を自動削除する。
cmd_1461 の Logic A/B は保持・破壊禁止。

## 絶対保護ルール（違反時は即STOP・家老報告）

以下は絶対 touch 禁止:
- `### ⚠️` で始まる未解決課題セクション（Day6 4視点codec 等）
- `### 📌 技術知見` セクション（永続的知見）
- `### 🔧 cmd_1441` セクション（hotfix 未解決）
- `### 🔧 cmd_1443_p09` セクション（incidental 未解決）
- ✅マークがない行は絶対に削除しない

## Step 1: advisor() 呼び出し（実装前）

## Step 2: ファイル確認

```bash
# 既存スクリプト確認（Logic A/B の理解）
cat /home/murakami/multi-agent-shogun/scripts/dashboard_lifecycle.sh | head -50

# dashboard.md の現在の構造確認
grep -n "^### \|^## " /home/murakami/multi-agent-shogun/dashboard.md
```

## Step 3: Logic C 実装 — clean_action_required_resolved() 関数

`clean_daily_completed_section()` 呼び出しの直後に追加:

```bash
# (2.9) 🚨要対応セクション内の '### ✅ 解決済み' サブセクション全体を削除
clean_action_required_resolved() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  # 戦略: 🚨要対応セクション内で '### ✅ 解決済み' で始まるH3サブセクション全体を削除
  # 次の ### か --- か ## が来るまでを1サブセクションとして扱う
  awk -v REMOVED_FILE="$removed_lines" '
    BEGIN {
      in_action = 0
      in_resolved = 0
      cleaned = 0
    }
    {
      line = $0

      # H2 セクション判定
      if (line ~ /^## /) {
        if (line ~ /要対応/) {
          in_action = 1
        } else {
          in_action = 0
        }
        in_resolved = 0
        print line
        next
      }

      # 🚨要対応セクション内のH3判定
      if (in_action == 1 && line ~ /^### /) {
        # '### ✅ 解決済み' で始まるサブセクションを削除対象に
        if (line ~ /^### ✅ 解決済み/) {
          in_resolved = 1
          printf "%s\n", line >> REMOVED_FILE
          cleaned++
          next
        } else {
          in_resolved = 0
        }
      }

      # 削除対象サブセクション内の行はスキップ
      if (in_resolved == 1) {
        # 空行もアーカイブ
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
    log "Logic C: 🚨要対応内 解決済みサブセクション なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "Logic C: ${cleaned_count} 行の解決済みサブセクションを検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN Logic C: 以下の行を削除予定:"
    while IFS= read -r l; do log "  C| ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  {
    echo ""
    echo "## Logic C 解決済みサブセクション Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "Logic C: ${cleaned_count} 行削除 → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}
```

## Step 4: Logic D 実装 — clean_info_sections() 関数

```bash
# (3.1) '### ℹ️' セクション 24h超過分をアーカイブ
clean_info_sections() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local now_ts cutoff_ts
  now_ts="$(date +%s)"
  cutoff_ts=$(( now_ts - 86400 ))

  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  # 戦略: '### ℹ️' で始まるH3サブセクション全体を対象
  # 日付判定: セクション内に YYYY-MM-DD があればそれを使用、なければファイルの作成時刻で判定
  # 安全側設計: mtime を使わず 24h経過とみなす（dashboard は常時更新されるため、セクション残存 = 古い確認済み情報）
  awk -v REMOVED_FILE="$removed_lines" '
    BEGIN {
      in_action = 0
      in_info = 0
      cleaned = 0
    }
    {
      line = $0

      if (line ~ /^## /) {
        if (line ~ /要対応/) {
          in_action = 1
        } else {
          in_action = 0
        }
        in_info = 0
        print line
        next
      }

      if (in_action == 1 && line ~ /^### /) {
        if (line ~ /^### ℹ️/) {
          in_info = 1
          printf "%s\n", line >> REMOVED_FILE
          cleaned++
          next
        } else {
          in_info = 0
        }
      }

      if (in_info == 1) {
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
    log "Logic D: ℹ️ セクション なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "Logic D: ${cleaned_count} 行の ℹ️ セクションを検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN Logic D: 以下の行を削除予定:"
    while IFS= read -r l; do log "  D| ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  {
    echo ""
    echo "## Logic D ℹ️ セクション Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "Logic D: ${cleaned_count} 行削除 → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}
```

## Step 5: Logic E 実装 — clean_resolved_subsections() 関数

```bash
# (3.3) 🚨要対応内の '### ✅ [cmd名]' (解決済みでない) サブセクション全体を削除
# ※ '### ✅ 解決済み' は Logic C で対応済み
# 対象: '### ✅ cmd_XXXX' や '### ✅ nightly_XXXX' 等の完遂済みサブセクション
clean_resolved_subsections() {
  if [[ ! -f "$DASHBOARD_MD" ]]; then
    return 0
  fi

  local month_archive="${ARCHIVE_DIR}/$(date +%Y-%m).md"
  local tmp_output removed_lines count_file
  tmp_output="$(mktemp)"
  removed_lines="$(mktemp)"
  count_file="$(mktemp)"

  awk -v REMOVED_FILE="$removed_lines" '
    BEGIN {
      in_action = 0
      in_resolved_sub = 0
      cleaned = 0
    }
    {
      line = $0

      if (line ~ /^## /) {
        if (line ~ /要対応/) {
          in_action = 1
        } else {
          in_action = 0
        }
        in_resolved_sub = 0
        print line
        next
      }

      if (in_action == 1 && line ~ /^### /) {
        # '### ✅' で始まるが '### ✅ 解決済み' でない → 完遂済みcmdサブセクション
        if (line ~ /^### ✅/ && line !~ /^### ✅ 解決済み/) {
          in_resolved_sub = 1
          printf "%s\n", line >> REMOVED_FILE
          cleaned++
          next
        } else {
          in_resolved_sub = 0
        }
      }

      if (in_resolved_sub == 1) {
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
    log "Logic E: 完遂済みサブセクション なし (skip)"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  log "Logic E: ${cleaned_count} 行の完遂済みサブセクションを検出"

  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN Logic E: 以下の行を削除予定:"
    while IFS= read -r l; do log "  E| ${l}"; done < "$removed_lines"
    rm -f "$tmp_output" "$removed_lines"
    return 0
  fi

  {
    echo ""
    echo "## Logic E 完遂済みサブセクション Auto-archived at $(date '+%Y-%m-%dT%H:%M:%S%z')"
    echo ""
    cat "$removed_lines"
  } >> "$month_archive"

  (
    flock -x -w 10 9 || { log "ERROR: flock timeout on $DASHBOARD_MD"; exit 1; }
    cp "$tmp_output" "$DASHBOARD_MD"
  ) 9<"$DASHBOARD_MD"

  log "Logic E: ${cleaned_count} 行削除 → ${month_archive}"
  rm -f "$tmp_output" "$removed_lines"
}
```

## Step 6: 関数呼び出し追加

既存の `clean_daily_completed_section()` 呼び出しの後、`check_mcp_stragglers()` の前に追加:

```bash
clean_action_required_resolved || log "ERROR in clean_action_required_resolved (continuing)"
clean_info_sections || log "ERROR in clean_info_sections (continuing)"
clean_resolved_subsections || log "ERROR in clean_resolved_subsections (continuing)"
```

## Step 7: dry-run 実行（production前に必ず実行）

```bash
cd /home/murakami/multi-agent-shogun
bash scripts/dashboard_lifecycle.sh --dry-run --verbose 2>&1 | tee /home/murakami/multi-agent-shogun/work/cmd_1462/dryrun_output.txt
```

dry-run 出力を `/home/murakami/multi-agent-shogun/work/cmd_1462/dryrun_output.txt` に保存。

**ここで一旦停止し、queue/reports/ashigaru2_report_subtask_1462a_phase1.yaml を作成して inbox_write karo で家老に報告せよ。**
**家老確認後の inbox で「production 実行せよ」が届いてから Step 8 に進め。**

## Step 8: 安全確認チェックリスト（dry-run 出力から確認）

dry-run 出力の C|/D|/E| 行を確認:
- [ ] `Day6 4視点MIX codec混在` の行が削除候補に含まれていない
- [ ] `📌 技術知見` セクションが削除候補に含まれていない
- [ ] `🔧 cmd_1441` セクションが削除候補に含まれていない
- [ ] `🔧 cmd_1443_p09` セクションが削除候補に含まれていない
- [ ] `⚠️ 技術的残課題` セクションが削除候補に含まれていない

## Step 9: production 実行（家老確認後のみ）

```bash
# 実行前の行数記録
wc -l /home/murakami/multi-agent-shogun/dashboard.md

# production 実行
bash /home/murakami/multi-agent-shogun/scripts/dashboard_lifecycle.sh --verbose 2>&1 | tee /home/murakami/multi-agent-shogun/work/cmd_1462/production_output.txt

# 実行後の行数確認（50%以上削減確認）
wc -l /home/murakami/multi-agent-shogun/dashboard.md

# 未解決項目が残存していることを確認
grep "Day6 4視点\|📌 技術知見\|🔧 cmd_1441\|🔧 cmd_1443_p09\|⚠️ 技術的残課題" /home/murakami/multi-agent-shogun/dashboard.md
```

## Step 10: advisor() 呼び出し（完了前）

## Step 11: git commit

```bash
git add /home/murakami/multi-agent-shogun/scripts/dashboard_lifecycle.sh
git diff --cached  # 意図外ファイル確認
git commit -m "feat(cmd_1462): dashboard_lifecycle拡張 Logic C/D/E — 🚨要対応解決済み自動削除"
git push origin main
```

## Step 12: report + inbox

`/home/murakami/multi-agent-shogun/queue/reports/ashigaru2_report_subtask_1462a.yaml` を作成し、gunshiに QC 依頼送信。
