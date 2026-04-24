# claude-mem クイックスタート

殿がターミナルから直接 claude-mem を叩いて過去知見を呼び出すためのコピペ集。
worker URL: `http://localhost:37777`

---

## パターン1: キーワード検索（/api/search）

**用途**: 「過去に yt-dlp の n-challenge をどう解決したか」等、キーワードで関連観察/セッション/プロンプトを横断検索する。

```bash
curl -s -G 'http://localhost:37777/api/search' \
  --data-urlencode 'query=yt-dlp n-challenge' \
  --data-urlencode 'limit=5'
```

**出力形式**: `{"content":[{"type":"text","text":"...markdown..."}]}`
テキスト本文は Markdown（ID/時刻/タイトル/参照数の表）。

**そのまま読む**:
```bash
curl -s -G 'http://localhost:37777/api/search' \
  --data-urlencode 'query=yt-dlp' --data-urlencode 'limit=5' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['content'][0]['text'])"
```

**出力サンプル**:
```
Found 6 result(s) matching "yt-dlp" (3 obs, 3 sessions, 0 prompts)

### Apr 24, 2026

**dist/index.html**
| ID | Time | T | Title | Read |
| #12137 | 12:44 PM | 🔵 | yt-dlp-js-runtimes-fix スキル化前の使用箇所調査 | ~129 |
```

---

## パターン2: セッション履歴（/api/summaries）

**用途**: 時系列で「何を依頼されて何を調べて何を学んだか」を俯瞰する。キーワード不問。

```bash
curl -s 'http://localhost:37777/api/summaries?limit=5'
```

**出力形式**: `{"items":[{id, session_id, request, investigated, learned, completed, next_steps, project, created_at, ...}]}`

**見やすく整形**:
```bash
curl -s 'http://localhost:37777/api/summaries?limit=5' \
  | python3 -c "
import sys, json
for s in json.load(sys.stdin)['items']:
    print(f\"[{s['id']}] {s['created_at']}\")
    print(f\"  req: {s['request'][:80]}\")
    print(f\"  learn: {(s.get('learned') or '')[:120]}\")
    print()
"
```

---

## パターン3: 観察（Observation）詳細（/api/observations）

**用途**: 特定観察IDの本文（narrative/facts/files_modified 等）を丸ごと取得する。cmd_xxxx完了後の振り返り等。

```bash
curl -s 'http://localhost:37777/api/observations?limit=3'
```

**出力形式**: `{"items":[{id, project, type, title, subtitle, narrative, text, facts, concepts, files_read, files_modified, created_at, ...}]}`

**タイトル+narrative抜粋**:
```bash
curl -s 'http://localhost:37777/api/observations?limit=10' \
  | python3 -c "
import sys, json
for o in json.load(sys.stdin)['items']:
    print(f\"#{o['id']} [{o['type']}] {o['title']}\")
    print(f\"  {(o.get('narrative') or '')[:150]}\")
    print()
"
```

**特定IDを取りに行きたい時**（limitを大きくして絞る）:
```bash
curl -s 'http://localhost:37777/api/observations?limit=200' \
  | python3 -c "
import sys, json
TARGET = 12137
for o in json.load(sys.stdin)['items']:
    if o['id'] == TARGET:
        print(json.dumps(o, ensure_ascii=False, indent=2))
        break
"
```

---

## 使い分けチートシート

| やりたいこと | 使うパターン |
|------|------|
| キーワードで横断検索 | (1) `/api/search` |
| 最近の作業履歴をざっと見る | (2) `/api/summaries` |
| 特定観察の本文を読む | (3) `/api/observations` |
| QC/実装前の知見確認 | `bash scripts/cmem_search.sh "<キーワード>"` |

scripts/cmem_search.sh はパターン1のラッパー。引数のURLエンコードを自動で行う。
