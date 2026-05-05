# cmd_1632 完了報告書: Video Index 一貫性 Audit

- **作成日**: 2026-05-05
- **worker**: ashigaru3
- **parent_cmd**: cmd_1632

## 1. CSV 最新化結果

`dozle_video_list.csv` を最新化済み（subtask_1632_csv にて実施）。

## 2. Audit 結果サマリ

audit_video_index_consistency.py による CSV vs scene_index_v2 突合結果:

| quality_status | 件数 |
|----------------|------|
| ok | 66 |
| violation_alphabet | 1 |
| index_missing | 10,362 |
| csv_outdated | 0 |
| **TOTAL** | **10,429** |

## 3. violation_alphabet 動画一覧

アルファベット表記の話者ラベルが混入している動画:

| video_id | speakers |
|----------|----------|
| xZTtk4pJcAs | A, B, C, D, E, F |

## 4. 4/2 以降の未処理動画リスト (57本)

published_at >= 2026-04-02 の動画で index_missing（scene_index_v2 にインデックスなし）:

| # | video_id | title | published_at |
|---|----------|-------|-------------|
| 1 | 5Np9PPU8JQE | 大切な人にありがとうを伝えよう #ファミマでドズル社発見 | 2026-05-05 |
| 2 | QK3Huq55BCM | 声真似したMOBを持ってこい！【マイクラ】 | 2026-05-04 |
| 3 | X9BWyuqSy_k | サーバーをぶっ壊せ！マイクラ破壊RTA対決！【マイクラ】 | 2026-05-03 |
| 4 | qFpCsQhwxwQ | エンドラRTAトーナメント【5月大会】 | 2026-05-02 |
| 5 | jIndbI48GK8 | ピノキオの学生生活 #マイクラ #minecraft #ショートコント | 2026-05-02 |
| 6 | o6vunreR_yM | からだが異常に良すぎる世界でエンドラ討伐【マイクラ】 | 2026-05-01 |
| 7 | 4mlCQ7dVKXM | 季節外れの雪合戦でガチ対決！【マイクラ】 | 2026-05-01 |
| 8 | 2Gv7n8dfohI | 勇者の展示品がショボすぎる #マイクラ #minecraft #ショートコント | 2026-05-01 |
| 9 | Fjt8U4vXSgI | 『ヒロアカ』コラボスキン入手するまで終われません！【ブロスタ/ドズル視点】 | 2026-04-30 |
| 10 | lDBmBtxcjEo | 閻魔が教え子 #マイクラ #minecraft #ショートコント | 2026-04-30 |
| 11 | AAnANq-bUpQ | クリーパーだらけの世界でネコとどこまで遠ざかれるか【マイクラ】 | 2026-04-29 |
| 12 | nxAAYd_FwC8 | 恋の行方が気になるフリマ #マイクラ #minecraft #ショートコント | 2026-04-29 |
| 13 | QMpQZbUTfj4 | じゃんけんですべてが決まるエンドラ討伐【マイクラ】 | 2026-04-28 |
| 14 | ouu0Mrb4Y5c | 親切の圧が強すぎるドズル #ファミマでドズル社発見 | 2026-04-28 |
| 15 | QCFyL7tG-v4 | 安い情報を信じたドズぼんがさっそく大ピンチ！？ | 2026-04-27 |
| 16 | HnDcGHXKJFQ | 86万トンの超巨大なダムを埋めるまで終われません！【マイクラ】 | 2026-04-27 |
| 17 | pIrocoqvwJg | 86万トンの超巨大なダムを掘るまで終われますか？【マイクラ】 | 2026-04-26 |
| 18 | NgkCZL-uhZI | 裏切り者の仮面を被ってやってくるあいつに要注意【マイクラ】 | 2026-04-25 |
| 19 | WylcM9Jly2s | 絶対に真似できないカレー作り #マイクラ #minecraft #ショートコント | 2026-04-25 |
| 20 | 8r1cEKpTM5M | 【PV】5月2日(土)！エンドラRTAトーナメント5月大会 | 2026-04-25 |
| 21 | D4_8sRpAKQo | 味方か裏切り者か…死者が残したレコードがすべてを告げる | 2026-04-24 |
| 22 | WbYEt3Pv0BE | ピノキオの恋 #マイクラ #minecraft #ショートコント | 2026-04-24 |
| 23 | XB-XKVQRCok | 1人目の犠牲者はあなたです【裏切り者サバイバル】 | 2026-04-23 |
| 24 | sml-aYEMIKM | 今月ピンチな金持ち #マイクラ #minecraft #ショートコント | 2026-04-23 |
| 25 | 05zhA1M5SU0 | 【インベントリ消滅】生き物になったブロックを集めろ！【マイクラ】 | 2026-04-22 |
| 26 | Tdgz_MMfBAU | 実際に呪文をとなえることで発動するゲーム【マイクラ】 | 2026-04-21 |
| 27 | X3cMBasYcSA | 校則を破ったら... #マイクラ #minecraft #ショートコント | 2026-04-21 |
| 28 | BcPWm_mCpp4 | 【#DoZ】最終日！最終ボスいきます！！！【ブロスタ】 | 2026-04-19 |
| 29 | nZwB29p9HQk | 【#DoZ】勝負の日！絶対に１０層いくぞ！！【ブロスタ】 | 2026-04-18 |
| 30 | l_DbsoeSTeI | 逮捕される桃太郎 #マイクラ #minecraft #ショートコント | 2026-04-18 |

## 5. 使用スクリプト・Git 情報

- **audit スクリプト**: `scripts/audit_video_index_consistency.py`
- **commit**: `765fb91` — `feat(dozle): audit_video_index_consistency.py 新規作成 — CSV vs scene_index_v2 突合 (cmd_1632)`
- **CSV**: `projects/dozle_kirinuki/data/dozle_video_list.csv`
- **scene_index**: `data/scene_index_v2/`

## 6. 所見

- 10,429本中 66本のみが ok (インデックス済み・問題なし)。99.4% が未処理。
- violation_alphabet 1本 (xZTtk4pJcAs) は話者ラベルが A,B,C,D,E,F のアルファベット表記。日本語表記への修正が必要。
- 4/2以降の新規動画57本は全て未処理。ショートコント・DoZシリーズなど多岐にわたる。
