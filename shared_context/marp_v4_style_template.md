# Marp v4 Style Template (正典)

> 抽出元: intermediate_v4_ch01_prompt_function.md
> 抽出日: 2026-05-06 (cmd_1655 Phase A)

---

## 1. Frontmatter Style (CSS)

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

## 2. Cover Slide (Opening)

```markdown
<!-- _class: cover -->

# {章タイトル}
## — {サブタイトル}

<div class="meta">
中級編 — 第{N}章 (約 {XX} min)<span class="free">FREE</span><br><br>
「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>
```

## 3. Cover Slide (Closing)

```markdown
<!-- _class: cover -->

# 第{N}章 完了
## 次は 第{N+1}章「{次章タイトル}」

<div class="meta">
✅ {達成項目1}<br>
✅ {達成項目2}<br>
...
<b>続けて第{N+1}章をお楽しみください</b>
</div>
```

## 4. Speaker Notes Format

```markdown
<!--
スピーカーノート:
{スライドの話すべき内容を自由テキストで記述}
-->
```

- スライドの `---` 区切りの直後に配置
- `<!-- ... -->` HTMLコメント形式
- 先頭行に `スピーカーノート:` プレフィックス

## 5. Key Style Elements

| 要素 | 値 | 用途 |
|------|-----|------|
| section padding | `50px 70px` | スライド余白 |
| section background | `#fafafa` | 薄グレー背景 |
| section flex | `flex-direction: column` | 上寄せレイアウト |
| cover gradient | `#1e3a8a → #312e81` | 紺グラデーション |
| cover text | `#fff` / `#fde68a` | 白+h2黄色 |
| h1 color | `#1e3a8a` | 濱紺 |
| h1 border | `3px solid #1e3a8a` | 下線 |
| blockquote accent | `#f59e0b` / `#fffbeb` | 琥珀色 |
| .free badge | `#facc15 bg / #78350f text` | FREEバッジ |
| table header | `#1e3a8a` | 紺ヘッダ |
| pre background | `#1e293b` | ダークコード |
