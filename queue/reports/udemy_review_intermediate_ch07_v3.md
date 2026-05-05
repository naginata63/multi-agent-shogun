# Udemy Review: intermediate_v4_ch07 (v3)

## 対象
- ファイル: `projects/udemy_course/drafts/lectures/intermediate_v4_ch07_restart_resilience.md`
- 章: 第7章「AIの記憶を引き継ぐ技術」
- レビュー日: 2026-05-05
- レビュアー: udemy-checker v2 (観点E対応版)

## 総合判定: 🟢

### 観点A: 難易度
- 用語表あり・比喩（絶望感のつかみ）が効果的
- YAML が用語表にないが「作業リスト」説明で大意は通る（致命的ではない）
- 「公式機能/カスタム機能」の境界が曖昧だが推測可能

### 観点B: 論理展開
- 飛躍・破綴なし
- 体験談→3パターン分類→4段階復旧→保存→失敗パターン→まとめ の流れが筋通り

### 観点C: 詰まる箇所
- なし

### 観点D: 良かった箇所
- 「AIが初めましてと言ってきた絶望感」のつかみが強い
- 「Compress = 重要な情報だけを残す」の定義が腑に落ちる
- 「復旧の質は保存の質で決まる」が章のメッセージを集約

### 観点E: 商品汎用性
- 🟢 問題なし
- ashigaru / karo / gunshi / multi-agent-shogun / cmd_XXX / queue/tasks/*.yaml 等の固有記法は一切含まれていない
- CLAUDE.md / memory/*.md / instructions/*.md は Claude Code 製品機能名として妥当

### 改善提案 (非ブロッキング)
1. 用語表に YAML の説明追加
2. 「公式機能/カスタム機能」の定義を1文で追加
3. 確認問題の解答と問題の間に改ページ追加

## 修正履歴
- cmd_042 → task-042 に変更 (line 198)
- .html も同期更新済み
