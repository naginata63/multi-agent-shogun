---
name: senkyou
description: |
  将軍が殿に戦況（現況）を報告するスキル。MCPダッシュボード+ntfyログから情報収集し、
  完了cmd・進行中cmd・殿の判断待ち事項をまとめて報告する。
  「状況は」「どうなった」「戦況」「進捗」で起動。
  Do NOT use for: 個別のpane確認やエージェント操作（それはcmd発令で行う）。
allowed-tools: Read, Bash, Grep
---

# /senkyou — 戦況報告

将軍の情報源は**MCPダッシュボードを第一ソース**とする。dashboard.mdとntfyログは補助。pane captureは不要。

## 第一ソース: MCPダッシュボード

**http://192.168.2.7:8770/** — エージェント稼働状況・タスク状態・アラートをリアルタイム表示。

```bash
# ダッシュボードが起動していない場合
python3 work/cmd_1068/dashboard/server.py &
```

## 動的コンテキスト

### 直近のntfy通知（補助）
!`tail -20 queue/ntfy_sent.log 2>/dev/null || echo "(ログなし)"`

### pending cmd
!`grep -B5 "status: pending" queue/shogun_to_karo.yaml 2>/dev/null | grep "id:" || echo "(なし)"`

## 手順

### Step 1: MCPダッシュボードを確認（第一ソース）
- ブラウザで http://192.168.2.7:8770/ を開く
- エージェント状態・アラート・最新タスク一覧を把握

### Step 2: 上の動的コンテキストを読む（補助）
- ntfyログの✅ → cmd完了
- ntfyログの🚨 → 要対応
- pending cmd → まだ家老に渡したが未完了

### Step 3: dashboard.mdを読む（補助）
```
Read dashboard.md
```
- 🚨要対応 → 殿の判断待ち
- ✅完了 → 殿に未報告のものがないか
- 足軽状態テーブル → 全体の稼働状況

### Step 4: 以下のフォーマットで殿に報告

```
### 完了
| cmd | 内容 | 完了時刻 |

### 進行中
| cmd | 内容 |

### 殿のご判断待ち
1. xxx
2. xxx
```

## 禁止事項
- **pane captureで状況を確認すること**
- MCPダッシュボードを確認せずに報告すること
- ntfyログを確認せずに報告すること
