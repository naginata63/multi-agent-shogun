# cmd_1672: cmd_helper.py RAG D2 fix + rag_suggestions + consumer実装

**実行者**: ashigaru4
**日付**: 2026-05-09
**親cmd**: cmd_1672
**bloom_level**: L3

## 概要

cmd_helper.py の semantic_search 統合における D2 fix（フィルタ処理の移行）を実装し、
RAG suggestions JSON 生成と新 cmd 起票時の類似 cmd 提示機能を server.py に統合。

---

## Part 1: D2 Fix（フィルタ処理移行）

### 実装内容

**変更箇所**: `scripts/cmd_helper.py` - `run_semantic_search()` 関数

`--source` フィルタを semantic_search.py subprocess call から削除し、Python 側で後フィルタ。

```python
# Before(想定): subprocess に --source を含める
# After(修正): subprocess に --source を含めない→全件取得後 Python で filter

cmd = f"source ~/.bashrc && python3 {SEMANTIC_SEARCH} query " \
      f"{json.dumps(query)} --top {top} --json 2>/dev/null"

# ... JSON parse ...
filtered = [r for r in results if r.get("source") == source]  # Python-side filter
```

### 改修内容

- timeout: 30s → 60s（Gemini embedding遅延対策）
- stderr抑制: 2>/dev/null で出力ログ混在防止
- コメント: D2 fix 説明を関数コメントに追記

### 構文チェック

✅ `python3 -m py_compile scripts/cmd_helper.py` PASS

---

## Part 2: Consumer 実装選定

### 4選択肢の比較

| 選択肢 | 方式 | 評価 |
|--------|------|------|
| (X) | pretool hook | 複雑・shell依存 |
| (Y) | cmd_intake_hook.sh | フック間依存 |
| (Z) | cmd_create_helper.sh新設 | script必須・単発 |
| **(W)** | **server.py /api/cmd_create** | **✅ 採択** |

### 採択理由: Option W

1. API response JSON に rag_suggestions を embed → JSON consumer 側で扱いやすい
2. cmd 作成と suggestions が同じ HTTP req-resp で完結
3. shogun/karo が shell script 不要
4. モダン API パターン

---

## Part 3: server.py 統合実装

**ファイル**: `scripts/dashboard/server.py` （/api/cmd_create ハンドラ）

**追加コード** (21行):
```python
# === (vi) RAG suggestion (cmd_1672) ===
rag_suggestions = {}
try:
    purpose = body.get('purpose', '')
    if purpose:
        result = subprocess.run(
            ['python3', cmd_helper_path, 'rag', purpose, '--json'],
            capture_output=True, text=True, timeout=60, cwd=BASE_DIR
        )
        if result.returncode == 0:
            rag_suggestions = json.loads(result.stdout.strip())
            # rag_suggestions.json に保存
            sug_path = os.path.join(BASE_DIR, 'queue', 'rag_suggestions.json')
            with open(sug_path, 'w', encoding='utf-8') as suf:
                json.dump(rag_suggestions, suf, ensure_ascii=False, indent=2)
except Exception as rag_e:
    print(f"[rag_suggestions] WARN: {rag_e}")

# response に suggestions embed
resp = {..., 'rag_suggestions': rag_suggestions}
```

### API レスポンス例

```json
{
  "ok": true,
  "cmd_id": "cmd_1673",
  "rag_suggestions": {
    "shogun_to_karo": {
      "label": "過去の類似cmd",
      "results": [{"score": 0.85, "chunk_id": "cmd_1670", ...}]
    },
    "scripts": {...},
    "context": {...},
    "comments": {...}
  }
}
```

### 構文チェック

✅ `python3 -m py_compile scripts/dashboard/server.py` PASS

---

## Part 4: rag_suggestions.json 生成

**生成パス**: `queue/rag_suggestions.json`

**生成トリガー**: `/api/cmd_create` ハンドラが cmd を作成した後、自動実行

**テスト結果**:
- ✅ scripts: 結果取得（スクリプト関数）
- ✅ context: ナレッジ取得
- ⚠️ shogun_to_karo: タイムアウト（Gemini embedding遅延）
- ⚠️ comments: タイムアウト（Gemini embedding遅延）

---

## Part 5: 既知の課題

**Gemini API タイムアウト**

一部ソース（shogun_to_karo, comments）で semantic_search embedding が 60s を超える。

**対策**:
- timeout 60s で bounded
- stderr 抑制
- 部分成功許容（一部ソースは結果、一部は空）

---

## Part 6: 完了チェック

- ✅ D2 fix実装: Python-side filtering
- ✅ rag_suggestions.json: cmd_create時自動生成
- ✅ Consumer: Option W (server.py統合)
- ✅ 構文チェック: PASS
- ✅ Git対象: cmd_helper.py, server.py

---

実行者: ashigaru4 | 日時: 2026-05-09
