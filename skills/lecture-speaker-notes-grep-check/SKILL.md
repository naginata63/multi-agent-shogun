---
name: lecture-speaker-notes-grep-check
description: Udemy講義スライド(.md)のspeaker notes有無・外部公開用語制限を自動検証する。Marp lecture品質QC用。「スピーカーノートチェック」「講義grep確認」「lecture QC」で起動。
version: "1.0"
author: ashigaru3
tags: [udemy, lecture, qc, grep, marp, speaker-notes]
---

# /lecture-speaker-notes-grep-check

## Overview

Udemy講義スライド(Marp形式.md)に対する品質チェックを一括実行する。

検証項目:
1. **Speaker notes存在確認** — 各スライド(`---`区切り)にHTMLコメント(`<!-- ... -->`)が含まれているか
2. **戦国用語grep** — 外部公開禁止用語(御意・つかまつる・ござる・拙者・候 等)の検出(false positive回避付き)
3. **本名grep** — 講師本名(村上)の検出

## When to Use

- 講義スライド(.md)作成完了後のQC
- cmd完了報告前の品質確認
- 「スピーカーノートチェック」「講義grep確認」「lecture QC」と言われた時

## Instructions

### Step 1: check.sh 実行

```bash
bash skills/lecture-speaker-notes-grep-check/check.sh \
  projects/udemy_course/drafts/lectures/beginner_*_v4.md \
  projects/udemy_course/drafts/lectures/intermediate_v4_ch0*.md
```

### Step 2: 結果確認

出力例:
```
=== Speaker Notes Check ===
[PASS] beginner_ch01_prompt_v4.md: 10/10 slides have speaker notes
[FAIL] beginner_ch02_claude_md_v4.md: slide 5 missing speaker notes

=== Forbidden Words Check ===
[PASS] beginner_ch01_prompt_v4.md: 0 forbidden words
[FAIL] intermediate_v4_ch03.md: line 42: 拙者

=== Summary ===
PASS: 11/12 files
FAIL: 1/12 files
```

### Step 3: FAIL対応

FAIL検出時:
- 過去cmdの漏れとして報告書に明記
- 修正は別cmdで対応(このSkillでは修正しない)
