# /restore-panes — tmux pane復元スキル

消失・崩壊したtmux paneを検出し、正しい配置・エージェント・モデル・bypass permissionsで復元する。

## いつ使うか
- 「誰かがいなくなっている」「paneが消えた」と殿が言った時
- 戦況確認でpane数が9未満の時
- agent_idとpane番号がズレている時

## 手順

### Step 1: 現状診断
```bash
# pane数確認
tmux list-panes -t multiagent:0 | wc -l

# 各paneのagent_id・モデル・bypass確認
for i in 0 1 2 3 4 5 6 7 8; do
  id=$(tmux display-message -t multiagent:0.$i -p '#{@agent_id}' 2>/dev/null || echo "MISSING")
  echo "0.$i = $id"
done
```

### Step 2: fix_panes.sh実行
```bash
bash scripts/fix_panes.sh
```
このスクリプトが自動で:
- 足りないpaneを作成
- bashのpaneにClaude CLIを起動（`--dangerously-skip-permissions`付き）
- karo/gunshi → `opus[1m]`、足軽 → `sonnet` で起動
- 全paneにagent_idを設定

### Step 3: レイアウト修復（shutsujinと同じ3列×3行にする場合）
```bash
# tiledで均等配置
tmux select-layout -t multiagent:0 tiled

# shutsujin列優先にするならswap
tmux swap-pane -s multiagent:0.1 -t multiagent:0.3
tmux swap-pane -s multiagent:0.2 -t multiagent:0.6
tmux swap-pane -s multiagent:0.5 -t multiagent:0.7
```

### Step 4: 検証
```bash
for i in 0 1 2 3 4 5 6 7 8; do
  id=$(tmux display-message -t multiagent:0.$i -p '#{@agent_id}')
  model=$(tmux capture-pane -t multiagent:0.$i -S -8 -p 2>/dev/null | grep -oE '(Opus|Sonnet) [0-9.]+' | tail -1)
  bypass=$(tmux capture-pane -t multiagent:0.$i -S -8 -p 2>/dev/null | grep -c "bypass permissions on")
  echo "0.$i = $id | $model | bypass=$bypass"
done
```

### Step 5: モデルがズレている場合
```bash
# inbox_writeでmodel_switchを送る
bash scripts/inbox_write.sh {agent_id} "/model sonnet" model_switch shogun
# または直接
tmux send-keys -t multiagent:0.{N} '/model sonnet' Enter
```

## 正しい配置

| pane | agent | モデル |
|------|-------|--------|
| 0.0 | karo | opus[1m] |
| 0.1 | ashigaru1 | sonnet |
| 0.2 | ashigaru2 | sonnet |
| 0.3 | ashigaru3 | sonnet |
| 0.4 | ashigaru4 | sonnet |
| 0.5 | ashigaru5 | sonnet |
| 0.6 | ashigaru6 | sonnet |
| 0.7 | ashigaru7 | sonnet |
| 0.8 | gunshi | opus[1m] |

## shutsujinのレイアウト（列優先3×3）
```
左列           中列           右列
karo(0.0)     a3(0.3)       a6(0.6)
a1(0.1)       a4(0.4)       a7(0.7)
a2(0.2)       a5(0.5)       gunshi(0.8)
```

## 注意
- `--dangerously-skip-permissions`なしで起動するとbypassにならない。後からShift+Tabでは切り替わらないことがある
- swap-paneで物理位置を入れ替えるとagent_idラベルもpaneについて移動する
- paneの中のCLIプロセスが古いagent用のcontextを持っている場合、/clearでSession Startさせること

## 関連ファイル
- scripts/fix_panes.sh — 復元スクリプト本体
- shutsujin_departure.sh — 正式な全環境起動スクリプト
- config/settings.yaml — エージェント・モデル設定
