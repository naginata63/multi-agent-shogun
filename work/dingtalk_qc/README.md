# DingTalk QCスクリプト 起動方法

## 前提条件

ChromeをCDPモードで起動し、scale.dingtalkにログイン済みであること。

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-cdp &
```

ブラウザで `https://scale.dingtalk.com` を開いてログインしておく。

---

## スクリプト一覧

| スクリプト | 用途 |
|-----------|------|
| `scripts/dingtalk_qc_auto.py` | 1件処理・半自動（判定は手動） |
| `scripts/dingtalk_qc_loop.py` | 複数件・全自動ループ |

---

## 起動コマンド

### 自動ループ（N件）

```bash
cd /home/murakami/multi-agent-shogun
python3 scripts/dingtalk_qc_loop.py 20
```

### 2窓並行実行

2つ目のChromeを別ポートで起動:
```bash
google-chrome --remote-debugging-port=9223 --user-data-dir=$HOME/.chrome-cdp2 &
```

DingTalkにログイン→QC画面を開いてからスクリプト起動:
```bash
# 1窓目（ポート9222、デフォルト）
python3 scripts/dingtalk_qc_loop.py 100

# 2窓目（ポート9223）
python3 scripts/dingtalk_qc_loop.py 100 --port 9223
```

### バックグラウンド実行（ログ付き）

```bash
cd /home/murakami/multi-agent-shogun
nohup python3 scripts/dingtalk_qc_loop.py 5000 > work/dingtalk_qc/loop_output.log 2>&1 &

# 2窓目
nohup python3 scripts/dingtalk_qc_loop.py 5000 --port 9223 > work/dingtalk_qc/loop_output_9223.log 2>&1 &

# 進捗確認
tail -f work/dingtalk_qc/loop_output.log
```

### 停止

```bash
pkill -f dingtalk_qc_loop
```

---

## 自動ループの判定ロジック

| 条件 | アクション |
|------|-----------|
| 類似度80%以上 | 確認済み[T] → 修正して承認 ✅ |
| 音量 < -35dB | 無効[2] → 聞き取れない[3] → 修正済み[e] → 修正して承認 ✅ |
| 無音2.5秒以上 | 無効[2] → 聞き取れない[3] → 修正済み[e] → 修正して承認 ✅ |
| 類似度80%未満 | 無効[2] → 聞き取れない[3] → 修正済み[e] → 修正して承認 ✅ |
| 5件連続失敗 | 自動停止 🛑 |

**重要: 「エラーあり」は絶対に使わない**（クライアント指示。権限剥奪リスクあり）

---

## ログ・出力ファイル

| ファイル | 内容 |
|---------|------|
| `work/dingtalk_qc/qc_log_{ポート}.jsonl` | 処理ログ（追記・ポート別） |
| `work/dingtalk_qc/current_audio_{ポート}.wav` | 直前の音声ファイル（ポート別） |

---

## よくあるエラー

| エラー | 対処 |
|--------|------|
| `scale.dingtalkのページが見つかりません` | ChromeでDingTalkを開く |
| `AssemblyAI error` | `config/assemblyai_key.env` を確認 |
| CDP接続失敗 | `--user-data-dir=$HOME/.chrome-cdp` つきでChrome再起動 |
| 2窓目が動かない | `--port 9223` を指定しているか確認 |
