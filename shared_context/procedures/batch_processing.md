# Batch Processing Protocol

大量データセット処理 (30+ 件・各 web search/API call/LLM 生成) の標準手順。skip するとtokensを repeated バッチで浪費する。

## 標準ワークフロー (大規模タスク必須)

```
① Strategy → 軍師 review → incorporate feedback
② Execute batch1 ONLY → 将軍 QC
③ QC NG → 全 agents 停止 → 根本原因分析 → 軍師 review
   → 指示修正 → clean state 復元 → ② へ戻る
④ QC OK → batch2+ 実行 (per-batch QC は不要)
⑤ 全 batches 完了 → Final QC
⑥ QC OK → 次 phase (① へ) or Done
```

## ルール

1. **Never skip batch1 QC gate**: 不正アプローチが 15 batches で repeat = 15× 浪費
2. **Batch size limit**: 30 items/session (>60K tokens なら 20)・batches 間で /new or /clear
3. **Detection pattern**: 各 batch task に未処理 item 識別 pattern を含めよ・restart 後 auto-skip
4. **Quality template**: 全 task YAML に quality rules (web search 必須・捏造禁止・unknown は fallback)
5. **State management on NG**: retry 前にデータ state 検証 (git log・entry counts・integrity)・破損時は revert
6. **軍師 review scope**: ① feasibility/token math/失敗シナリオ・③ 根本原因/fix 検証
