# cmd_1607 完了報告書

**日時**: 2026-05-04  
**cmd**: cmd_1607  
**担当**: ashigaru2 (実装×3) / gunshi (QC×3) / karo (完了処理)

## 概要
殿/家老発言時に自動セマンティック検索 (claude-mem FAISS) を走らせ、
関連 procedure/script の path + 1行 snippet を将軍 context に注入する
UserPromptSubmit hook を実装・4欠陥修正の末 QC PASS。

## 修正履歴

| subtask | 内容 | 結果 |
|---------|------|------|
| subtask_1607a | 初期実装 | QC FAIL (D1-D4) |
| subtask_1607a2 | D1-D4修正 (timeout/stderr/threshold) | QC FAIL (D5発見) |
| subtask_1607a3 | D5修正 (source; 区切り) | QC PASS ✅ |

## smoke test 最終結果 (6/6 PASS)
- ffmpeg query: 10.97s / 5 hits ✅
- review.html query: 12.71s / 5 hits ✅
- agent filter: gunshi/ashigaru 無出力 ✅
- 短文skip: 0.04s ✅

## commit
- 35dfc1a: fix(hook) D5 ~/.bashrc 短絡修正

## 残課題 (別cmd推奨)
- D6: procedures corpus が全体の1%・logs 92%偏りで top5 未掲載
  → faiss reconstruct fix / logs corpus 除外 / source 重み付け

## hookの動作確認
本日 UserPromptSubmit hook が複数回実際に発火 (score 0.58-0.62) ✅
