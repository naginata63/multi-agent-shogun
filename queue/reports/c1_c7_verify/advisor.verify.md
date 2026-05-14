公式仕様を取得完了。判定する。

## 致命傷 C6 判定

- **judgment**: ✅実在
- **official_fact**:
  - **type ID**: 公式 Tool parameters 表に `Must be "advisor_20260301".` と明記。全 SDK サンプルコード (cURL/Python/TypeScript/Ruby/PHP/Go) も `"type": "advisor_20260301"` で統一。
  - **anthropic-beta header**: 公式 Note ブロックに `Include the beta header `advisor-tool-2026-03-01` in your requests.` と明記。全 SDK サンプル (cURL header / Python `betas=["advisor-tool-2026-03-01"]` / TypeScript `betas: ["advisor-tool-2026-03-01"]` 等) も統一。
- **講座記述の問題**: なし。中06/10 の記述「advisor_20260301」「advisor-tool-2026-03-01」は **公式ドキュメントと文字列完全一致** (ハイフン位置・日付形式・命名規則すべて一致)。
- **推奨修正**: 修正不要。**強化策として** (任意):
  - 「2026-03-01 時点 beta 機能」の旨を補足注記しておくと、将来 GA 化されて beta header が不要になった際に学習者が混乱しない (公式が "The advisor tool is in beta." と明記しているため)
  - 「Claude API + Claude Platform on AWS のみ対応・Bedrock/Vertex AI/Foundry 非対応」も併記すると企業内導入時の事故防止に有用
- **priority**: 低 (修正不要)

---

**補足知見** (講座記述検証時の boundary 事実):
- Executor/Advisor の組合せ制約: 講座でこの 4組合せ表 (Haiku 4.5 / Sonnet 4.6 / Opus 4.6 / Opus 4.7 → 全て Advisor=Opus 4.7) を扱っているなら別途整合 verify が必要
- Platform 制約: Bedrock/Vertex AI/Foundry 非対応の事実
