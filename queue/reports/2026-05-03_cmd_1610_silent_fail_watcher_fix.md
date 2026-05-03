# cmd_1610 完了報告: silent_fail_watcher.sh false positive 撲滅 + 多重起動防止

## 概要

silent_fail_watcher.sh が advisor 応答テキスト中の平文 "error" 語句を誤検知し、大量の ntfy 通知を送信していた問題を修正。併せて二重起動防止を強化。

## 修正内容

### 1. ERROR_REGEX 厳格化

**旧 (誤検知あり):**
```bash
ERROR_REGEX='(^|[^A-Za-z])(ERROR|Error|error|FAIL|Fail|fail|FATAL|Fatal|CRITICAL|Critical|COST|Cost|BILLING|Billing|billing)([^A-Za-z]|$)'
```

**新 (構造化ログのみ検知):**
```bash
ERROR_REGEX='^[0-9]{4}-[0-9]{2}-[0-9]{2}.*\[(ERROR|FATAL|CRITICAL|COST|BILLING)\]|^Traceback \(most recent call last\)'
```

変更理由:
- 旧 regex は advisor 応答中の "Error handling" "ffprobe -v error" 等の平文を誤検知
- 新 regex は `[ERROR]` 等の構造化ログ形式 (timestamp付き) + Python Traceback のみ検知
- 大文字・小文字の列挙 (`Error|error|FAIL|fail`) を廃止し、ブラケット表記 `[ERROR]` のみに絞り込み

### 2. PID 二重起動防止: flock 化

**旧 (TOCTOU 競合あり):**
```bash
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" ...)
    if kill -0 "$OLD_PID" ...; then exit 0; fi
fi
```

**新 (アトミックロック):**
```bash
exec 200>"$PID_FILE"
if ! flock -n 200; then
    OLD_PID=$(cat "$PID_FILE" ...)
    exit 0
fi
```

変更理由:
- 旧方式は PID ファイル存在確認と kill -0 の間に race condition (TOCTOU)
- flock -n はカーネルレベルのアトミックロック → 競合不可能
- cleanup で `rm -f "$PID_FILE"` を削除 (flock が fd close で自動解放)

### 3. 除外リスト追加

- `*/advisor_proxy_stdout.log` → advisor 応答本文を含む (INFO レベル)
- `*/advisor_proxy_stderr.log` → advisor エラー出力 (INFO レベル)

## テスト結果

### false positive テスト
```bash
echo 'ffprobe -v error ...' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}.*\[(ERROR|FATAL|CRITICAL|COST|BILLING)\]|^Traceback \(most recent call last\)'
# → 0件 (PASS)
```

### true positive テスト
```bash
echo 'Traceback (most recent call last)' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}.*\[(ERROR|FATAL|CRITICAL|COST|BILLING)\]|^Traceback \(most recent call last\)'
# → 1件 (PASS)
```

### 重複プロセス確認
```bash
pgrep -a silent_fail_watcher
# → 0件 (running instances = 0)
```

## 重複起動原因 (F1)

旧 daemon が shutdown した後、PID ファイルが残存し新インスタンスが起動できない問題があった。
flock 化により PID ファイル残存問題を解消。

## F2: 旧 daemon 再起動要否

**現在 watcher daemon は停止中** (`pgrep -a silent_fail_watcher` → 0件)。

本修正を本番反映するには daemon の再起動が必要:
```bash
# tmux 内で実行 (バックグラウンド)
nohup bash /home/murakami/multi-agent-shogun/scripts/silent_fail_watcher.sh &
```

※ 家老に daemon 再起動要否を確認すること。

## 変更ファイル

| ファイル | 変更 |
|---------|------|
| scripts/silent_fail_watcher.sh | +10/-9 行 |

## Commit

- **Hash**: `a3a0f6af229a89c31590e99355e69a037b5f11e3`
- **Message**: `fix(watcher): cmd_1610 silent_fail_watcher false positive 撲滅 + flock二重起動防止`
- **Author**: naginata63
- **Date**: 2026-05-03 20:44:26 +0900
