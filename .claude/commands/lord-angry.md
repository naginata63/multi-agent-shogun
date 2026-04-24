---
name: lord-angry
description: |
  殿激怒発言から memory/feedback_*.md 草稿と MEMORY.md 追記候補を半自動生成するスキル。
  草稿を提示→殿・将軍・家老が y(承認) / e(修正) / n(破棄) を選択するレビュー方式。
  auto-commit 禁止・承認後のみ Write+commit（push は禁止、家老の責務）。
  「殿激怒」「lord-angry」「feedback追加」「殿の教訓」「激怒反映」で起動。
  Do NOT use for: 殿の褒め言葉・中立判断の記録（それは別途 project memory か observation）。
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# /lord-angry — 殿激怒 → memory 自動反映（レビュー方式）

殿から激怒・叱責・強い指摘を受けた際、その発言を引数として渡すことで
`memory/feedback_{slug}.md` の草稿と `memory/MEMORY.md` への追記候補を下書き生成する。
**auto-commit は不可**。承認応答を受領してから初めて Write/commit を実行する。

## 使い方

```
/lord-angry 殿の発言抜粋をここに貼る（1〜3 文程度）
```

引数を省略した場合、起動直後に発言抜粋の入力を求めること。入力が得られるまで下書き生成に進んではならない。

## いつ使うか
- 殿が「〜するな」「〜しろ」「なぜ〜した」等の強い口調で指摘した直後
- 殿が過去事例と紐付けて再発防止を命じた時
- 家老・軍師が殿の同種発言を 2 回以上観測した時（鉄則化の必要ありと判断）

## いつ使わないか
- 殿の中立的な確認・質問（例「どうなった」「確認せよ」）→ skip
- 既存 feedback と同趣旨の発言（まず memory/ を grep してから判断）
- 殿が未発言の「推測される意向」→ 絶対に書き起こすな

## 手順

### Step 1: 引数の受領と検証

`$ARGUMENTS` を殿の発言抜粋として受領する。空または 5 文字未満の場合、以下を質問して入力を待て：

```
殿の発言抜粋を貼ってくだされ。1〜3 文・原文ママが望ましい。
```

発言を得るまで以降の Step に進むな。

### Step 2: 既存 feedback との重複チェック

発言からキーワードを 2〜3 個抽出し、以下で検索：

```bash
grep -l -i -E "<keyword1>|<keyword2>" /home/murakami/multi-agent-shogun/memory/feedback_*.md 2>/dev/null
ls /home/murakami/multi-agent-shogun/memory/ | grep -i "<keyword_slug_candidate>"
```

ヒットした feedback があれば：
- 既存ファイルを Read し、今回の発言がその拡張・強化か、別ルールかを判断
- **拡張の場合**: 既存ファイルに追記提案を作れ（Step 3 の slug は既存名を採用）
- **別ルール**: 新規 slug を採用（Step 3 へ）
- 完全重複と判断したら、ユーザに「既存 memory/feedback_{name}.md と重複のため新規作成を見送り、既存の参照日更新のみ提案する」と伝えて Step 3 は skip

### Step 3: slug 命名

発言内容から snake_case 3〜5 単語の slug を決定せよ。

- 例: 殿「走っている最中にYAMLを弄るな」→ `no_edit_while_running`
- 例: 殿「panels JSON は絶対パスで書け」→ `panel_refs_absolute`
- 名前は rule/constraint を表す名詞句。動作主語（shogun/karo）を含めるのは混同回避が必要な時のみ。

命名後、再度 `ls memory/feedback_{slug}*.md` で衝突確認。衝突時は日付サフィックス（例: `_20260424`）を付与し、レビュー時に旗を立てる。

### Step 4: 草稿生成（下書きのみ・Write しない）

以下 2 種を**テキストとして表示する**。まだファイルには書かない。

#### (A) `memory/feedback_{slug}.md` 草稿

CLAUDE.md 記載の feedback 構造に厳密に従え：

```markdown
---
name: {1 行・日本語 20 字以内のルール名}
description: {1 行・検索用に具体的に。ルール本体を思い出せる文言}
type: feedback
---

{ルール本体を 1 行で明言（命令形）}

**Why:** {殿がこのルールを課した理由。可能なら過去 cmd_XXX・具体事象を引用}

**How to apply:** {いつ・どこで・どう適用するか。箇条書き 2〜4 項目推奨}
```

- 既存 `memory/feedback_*.md` と同じ トーン・粒度に揃えよ。3 単語で済むことを 3 文にするな。
- 殿原文の威勢は残せ（「〜するな」は「〜禁止」等に薄めない）。

#### (B) `memory/MEMORY.md` 追記候補

MEMORY.md の章構成（`### cmd発令ルール` / `### QCルール` / `### 完了判定ルール` / `### ショート制作ルール` / `### 将軍の行動ルール` / `### エージェント管理ルール` / `### LLM選定ルール` / `### 技術的教訓`）から**適切な章を 1 つ提案**せよ。該当章がなければ新設章名も併記。

追記候補は以下 1 行フォーマット：

```markdown
- **{ルール短縮名}**: {1〜2 文要約} [詳細: memory/feedback_{slug}.md] [{YYYY-MM-DD} {事象短縮・例: 殿激怒}]
```

### Step 5: レビュー提示と停止（**HALT POINT**）

Step 4 で生成した (A) と (B) を以下の体裁で表示せよ：

```
━━━━━━━━━━━━━━━━━━━━━━
【殿激怒 feedback 草稿レビュー】
━━━━━━━━━━━━━━━━━━━━━━

■ 新規ファイル: memory/feedback_{slug}.md
──────────────────────────
{(A) の草稿全文}
──────────────────────────

■ MEMORY.md 追記候補（章: {章名}）
──────────────────────────
{(B) の 1 行}
──────────────────────────

■ 重複チェック結果
{Step 2 の結果: hit 無し / hit: memory/feedback_XXX.md}

■ 選択肢
  y  承認 → Write 2 件 + git add 明示 + commit（push は家老責務・実行しない）
  e  修正 → 修正指示を聞き草稿再生成（Step 4 に戻る）
  n  破棄 → no-op・ファイル未作成・commit 無し
```

**ここで必ず停止し、殿・将軍・家老の `y` / `e` / `n` 返答を待て。**
返答を受領する前に Write / Edit / git 系コマンドを実行してはならない（F002 違反）。
勝手な「確認のため保存しておく」等の先回りは厳禁。

### Step 6: 分岐処理

#### y（承認）

1. 草稿 (A) の内容で `Write memory/feedback_{slug}.md`
2. MEMORY.md の該当章末尾に (B) の 1 行を `Edit` で追記（`replace_all=false`・該当章見出しを含む unique anchor で置換）
3. git add は明示的に限定：
   ```bash
   git add /home/murakami/multi-agent-shogun/memory/feedback_{slug}.md \
           /home/murakami/multi-agent-shogun/memory/MEMORY.md
   git commit -m "feedback: {ルール短縮名}（殿激怒{YYYY-MM-DD}）"
   ```
4. `git add .` や `git add memory/` は禁止（他ファイル巻き込み防止）
5. `git push` は実行するな。家老が cmd 完了時に push する
6. 承認者に「commit hash: {short_hash} 完了。push は家老に委譲」と報告

#### e（修正）

1. 「どの箇所をどう直すか」を質問し、修正指示を受領
2. Step 4 に戻り草稿を再生成
3. Step 5 の HALT POINT に再度到達・再度 y/e/n を待つ
4. このループは回数無制限（殿納得まで）

#### n（破棄）

1. 「承知。破棄いたす。memory は変更無し」と返答のみ
2. Write / Edit / git 系を一切実行しない
3. 草稿テキストも残さない（以後のログ検索用に会話ログに残るのみ）

## 禁止事項

- **承認応答（y）受領前に Write / Edit / git commit を実行すること**（F002 違反・auto-commit 禁止の根幹）
- `git add .` / `git add memory/` 等の巻き込みコミット
- `git push`（家老責務）
- 殿の発言を要約で薄めること（威勢を保て）
- 推測や類推での feedback 起票（殿が発言していないルールを書き起こすな）
- 既存 feedback と完全重複の新規ファイル作成
- `memory/feedback_{slug}.md` 以外の場所（projects/ 配下等）への誤配置

## 設計根拠

- cmd_1442 execution_plan_v3.md §3 Δ4 H11「レビュー方式」殿承認（2026-04-24 18:34）
- auto-commit 不可: F002（直接人間連絡禁止）の拡張として殿未承認の memory 書換を禁止
- レビュー方式採用の理由: 殿激怒を LLM が誤検出・誤解釈した場合の memory 汚染を防ぐため
