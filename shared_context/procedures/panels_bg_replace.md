# panels_odai_05 背景指示差し替え手順

## 概要
panels_odai_05_edited.jsonの全8パネルのdirector_notesの「背景:」セクションをバラエティ演出背景に差し替える。
背景以外（キャラ・表情・ポーズ・禁止事項）は一切変更しない。

## 対象ファイル
```
projects/dozle_kirinuki/work/20260406_仲間の気持ちがわかればチートになる世界でエンドラ討伐！【マイクラ】/output/manga_odai/panels_odai_05_edited.json
```

## Step 1: advisor()呼び出し（実装前）

## Step 2: JSONを読んで現状確認
対象ファイルをReadし、各パネルのdirector_notes内の「背景:」記述箇所を確認する。

## Step 3: 差し替え実施
各パネルのdirector_notesの「背景:」セクションのみを以下に書き換える。
新規.py禁止。Editツールで直接編集のみ。

| パネルID | 背景指示（殿承認済み） |
|---------|------------------|
| p1_qnly_scheme | 暗い会議室風の空間にスポットライトが当たる演出。密談・策略の緊張感。 |
| p2_bon_depressed | どんよりした雨の窓辺。暗いトーン。鬱モード演技の陰鬱な空気を最大化する背景。 |
| p3_oomen_yakiniku | 焼肉の煙と炎が背景にドーンと広がる。集中線エフェクト。空気読まない突進感・食欲全開の勢い。 |
| p4_dozle_worried | 柔らかいパステルカラーの背景。心配の波紋エフェクト。ドズルの優しさが伝わる温かみ。 |
| p5_dozle_listening | 夕焼けグラデーション背景。暖色の柔らかい光。兄貴分の包容力・「話聞くよ」の安心感。 |
| p6_bon_guilt_trip | 斜め分割に合わせた対比背景。ぼんじゅうる側=策略の暗い紫トーン、ドズル側=怒りの赤い炎背景。温度差を演出。 |
| p7_climax_invitation | 勢いのある集中線。期待感の明るいトーン。「行く！」の勢いは出すが過剰にしない。P8への助走。 |
| p8_dozle_confused | 最大演出。金色の紙吹雪＋大きな「失敗」赤スタンプ＋衝撃エフェクト＋ヒビ割れ。バラエティのオチ演出。クライマックスの爆発力を全振り。 |

**注意**: situationフィールドは変更不要（ゲーム内状況説明であり背景指示ではない）

## Step 4: JSONパース確認
```bash
python3 -c "import json; json.load(open('projects/dozle_kirinuki/work/20260406_仲間の気持ちがわかればチートになる世界でエンドラ討伐！【マイクラ】/output/manga_odai/panels_odai_05_edited.json')); print('OK')"
```
エラーが出たら修正してから次へ。

## Step 5: advisor()呼び出し（完了前）

## Step 6: git commit
```bash
git add "projects/dozle_kirinuki/work/20260406_仲間の気持ちがわかればチートになる世界でエンドラ討伐！【マイクラ】/output/manga_odai/panels_odai_05_edited.json"
git commit -m "fix(cmd_1376): panels_odai_05 背景指示をバラエティ演出に差し替え"
```

## Step 7: 完了報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽1号、subtask_1376a完了。panels_odai_05_edited.json全8パネルの背景指示差し替え済み・JSONパースOK・commit済み。" report_completed ashigaru1
```
