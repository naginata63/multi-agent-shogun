# Lecture Design Rules — Udemy講義スライド量産ルール

この文書は「Claude Code はじめての一歩」講座のスライド量産における設計ルールを定める。
すべてのスライド作成タスク（足軽へのsubtask）は本ルールに従うこと。

## 1. スライド枚数ルール

**基本: 1スライドあたり 1.5〜2.5分**

| 章の想定時間 | 目安枚数 |
|-------------|---------|
| 15 min | 6〜10枚 |
| 25 min | 10〜16枚 |
| 30 min | 12〜20枚 |

- cover（表紙）・summary（まとめ）・questions（確認問題）・end cover（完了）は枚数に含める
- 本文スライドがこの範囲を逸脱する場合、内容の分割・統合を検討すること
- 参照: 既存スライド実績（ch00=11枚/15min, ch01=10枚/15min, ch02=16枚/30min, ch06=17枚/30min）

## 2. プロンプト指導ルール — 自然言語のみ・XML禁止

Claude Codeへのスライド作成指示は **自然言語ベース** で書くこと。
XMLタグ（`<input>`, `<task>`, `<output_format>` 等）を使った構造化プロンプトは **禁止**。

### 理由

- XMLタグ構造化は **API利用者（開発者）向け** の手法
- Claude Code CLIは自然言語で十分に精度が出る
- XMLで書くとかえって可読性が下がり、後からの修正コストが増す
- 本講座の第1章でXMLタグを「教える」ことと、スライド作成指示にXMLを使うことは別物

### NG例（XML構造化プロンプト）

```
<input>
curriculum_beginner_v3_marp.md の第4章セクション
</input>

<task>
inputの内容に基づき、Marp形式の講義スライドを作成せよ。
</task>

<output_format>
Markdown形式。speaker notesを全スライドに含めること。
</output_format>
```

### OK例（自然言語プロンプト）

```
curriculum_beginner_v3_marp.md の第4章セクションを読んで、
Marp形式の講義スライドを作成してください。
全スライドにspeaker notes（HTMLコメント形式）を含めてください。
beginner_ch00_intro.md を形式の参考にしてください。
```

## 3. Speaker Notes ルール

- **全スライドに必須** — 1枚も欠けてはならない
- 形式: HTMLコメント `<!-- ... -->`
- 内容: 講師が話す台本（1スライドあたり3〜8文）
- cover（表紙）・end cover（完了ページ）にもspeaker notesを書くこと
- speaker notesの先頭行は `スピーカーノート:` で始める（coverページのみ）

## 4. 受講者操作語句 禁止ルール

スライド本文に以下のような **受講者に操作を促す語句** を含めてはならない。

### 禁止語句の例

- 「〜してください」「〜してみましょう」「〜を入力してください」
- 「まず〇〇をインストールして」
- 「ターミナルを開いて」
- 「以下のコマンドを実行してください」

### 例外

- 「Claude Codeにこう伝えると〜」という **説明文** 内での引用は可
- 確認問題の「答えよ」は可（問題形式として不自然でない場合）

### 理由

本講座は **動画講義** であり、受講者がリアルタイムで操作することを前提としていない。
視聴専用でも成立する内容にすること。

## 5. 量産フォーマット — Marp共通スタイル

すべてのスライドは以下のMarp frontmatterを使用すること。

```yaml
---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 1.7em; padding: 50px 70px; background: #fafafa; display: flex !important; flex-direction: column !important; justify-content: flex-start !important; align-content: flex-start !important; align-items: stretch !important; }
  section h1:first-child, section h2:first-child { margin-top: 0; }
  section.cover { background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%); color: #fff; text-align: center; justify-content: center !important; align-items: center !important; }
  section.cover h1 { font-size: 1.6em; color: #fff; border: none; }
  section.cover h2 { font-size: 1.0em; color: #fde68a; }
  section.cover .meta { font-size: 0.7em; opacity: 0.85; margin-top: 1.5em; }
  h1 { color: #1e3a8a; border-bottom: 3px solid #1e3a8a; padding-bottom: 0.2em; font-size: 1.4em; }
  h2 { color: #2563eb; font-size: 1.1em; }
  h3 { color: #4b5563; font-size: 1.0em; }
  blockquote { border-left: 4px solid #f59e0b; background: #fffbeb; padding: 0.4em 0.8em; font-style: italic; color: #78350f; }
  code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  pre { background: #1e293b; color: #f1f5f9; padding: 0.6em; font-size: 0.7em; border-radius: 6px; }
  table { font-size: 0.78em; border-collapse: collapse; }
  th { background: #1e3a8a; color: #fff; padding: 0.4em 0.8em; }
  td { padding: 0.4em 0.8em; border: 1px solid #ddd; }
  .big { font-size: 1.6em; font-weight: bold; color: #1e3a8a; }
  .free { background: #facc15; color: #78350f; padding: 2px 8px; border-radius: 4px; font-size: 0.65em; font-weight: bold; }
---
```

**必須項目**:
- `font-size: 1.7em` — 統一文字サイズ
- `display: flex !important` — レイアウト制御
- `section.cover` — 表紙・完了ページ用グラデーション背景

## 6. スライド構成テンプレート

各章は以下の構成に従うこと。

1. **cover** — 章タイトル・所要時間・講師名
2. **goals** — 「この章で学ぶこと」（箇条書き3〜5項目）
3. **main content** — 本文スライド（10〜15枚）
4. **summary** — 章のまとめ（学んだことの箇条書き）
5. **questions** — 確認問題（3問・回答付き）
6. **end cover** — 完了ページ（到達点のチェックリスト + 次章予告）

## 7. 禁止事項

- **ASCII罫線アート** — box drawing文字（─│┌┐└┘├┤┬┴┼╔╗╚╝║═等）による装飾は禁止
- **長すぎるコードブロック** — 1スライドに10行を超えるコードは避ける
- **過度なアニメーション指示** — Marpの標準機能のみ使用

## 8. 3階層骨格ルール (L1/L2/L3)

初級編 v4 はAI開発の知識を3つの階層で整理する。各スライド章は対応する階層ラベルを明示すること。

### 階層定義

| 階層 | 名称 | 対応章 | 役割 |
|------|------|--------|------|
| **L1** | プロンプト | ch01 | AIに指示を確実に伝える — 会話レベルの操作 |
| **L2** | コンテキスト | ch02, ch03, ch04 | プロジェクト知識をAIに共有する — .mdファイル群による設定 |
| **L3** | ハーネス | ch05 | AIの動作を安全に制御する — hookによる安全装置 |

### ラベル明示ルール

- 本文スライド章（ch01〜ch05）は、**スライドタイトルまたは冒頭スライド**に `[L1]` `[L2]` `[L3]` ラベルを記載すること
- 序章（ch00）・終章（ch06）はラベル不要
- 1章が複数階層にまたがる場合（例: ch02-ch04 はすべてL2）、章の冒頭スライドに `[L2]` を明示

### 例

```
# プロンプト基礎 — AIに確実に伝える技術 [L1: Apply]
# CLAUDE.md ミニマム — プロジェクトの「説明書」 [L2: Apply]
# hookの入門 — AIの安全装置を作る [L3: Apply]
```
