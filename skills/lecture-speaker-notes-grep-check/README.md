# lecture-speaker-notes-grep-check

Udemy講義スライド(Marp形式.md)の品質を自動検証するClaude Code Skill。

## 検証項目

| 項目 | 説明 |
|------|------|
| Speaker Notes | 各スライドにHTMLコメント(`<!-- ... -->`)が存在するか |
| 戦国用語 | 外部公開禁止用語(御意・つかまつる・ござる・拙者・候)の検出 |
| 本名 | 講師本名(村上)の検出 |

## 使い方

```bash
# 全講義チェック
bash skills/lecture-speaker-notes-grep-check/check.sh \
  projects/udemy_course/drafts/lectures/beginner_*_v4.md \
  projects/udemy_course/drafts/lectures/intermediate_v4_ch0*.md

# 個別ファイル
bash skills/lecture-speaker-notes-grep-check/check.sh \
  projects/udemy_course/drafts/lectures/beginner_ch01_prompt_v4.md
```

## 出力例

```
[PASS] beginner_ch01_prompt_v4.md
  [PASS] Speaker notes: 10/10 slides OK
  (no forbidden words)

[FAIL] example_fail.md
  [FAIL] Speaker notes: 3/5 slides missing (slide_2,slide_4,slide_5)
  [FAIL] 戦国用語(拙者): 1 hit(s)

=== Summary ===
PASS: 1/2 files
FAIL: 1/2 files
```

## grep戦国用語パターン

false positive回避のため `候` は `候[^補選手者]` で検出:
- 検出: 「〜と候」「候補外」以外の候
- 除外: 候補、候選、候手

## FAIL対応

FAIL検出時は「過去cmdの漏れ」として報告書に明記。修正は別cmdで対応。
