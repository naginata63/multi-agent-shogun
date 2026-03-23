#!/usr/bin/env python3
"""
scene_search_v2.py — セマンティックシーン検索 (merged JSON + numpy cosine similarity)

使い方:
    python3 scripts/scene_search_v2.py build
    python3 scripts/scene_search_v2.py build --update   # 新規JSONのみ追加
    python3 scripts/scene_search_v2.py query "てぇてぇ" --top 10
    python3 scripts/scene_search_v2.py query "MENのボケ" --video Bxl6QhjtH7s --top 5
    python3 scripts/scene_search_v2.py query "裏切り" --speaker bon --json
    python3 scripts/scene_search_v2.py info
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# ===== 定数 =====
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
KIRINUKI_DIR = PROJECT_ROOT / "projects" / "dozle_kirinuki"
SRT_CANDIDATES_DIR = KIRINUKI_DIR / "work" / "srt_and_candidates"
WORK_DIR = KIRINUKI_DIR / "work"
INDEX_DIR = PROJECT_ROOT / "data" / "scene_index_v2"
EMBEDDINGS_FILE = INDEX_DIR / "embeddings.npy"
METADATA_FILE = INDEX_DIR / "metadata.json"
BUILD_INFO_FILE = INDEX_DIR / "build_info.json"

EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072
BATCH_SIZE = 100

# セグメント化パラメータ
MAX_SEG_MS = 5000    # セグメント最大長 5秒
MAX_GAP_MS = 2000    # 無音ギャップ閾値 2秒

# ===== 修正1: ストップワードフィルタ =====
STOP_WORDS = [
    "ご視聴ありがとう",
    "チャンネル登録",
    "高評価",
    "バイバーイ",
    "お願いします",
    "毎日18時",
    "動画投稿中",
    "おすすめ動画",
    "コメント欄",
]

def is_stopword_segment(text: str) -> bool:
    """定型句（エンディング・CTA等）を含むセグメントを判定。"""
    return any(sw in text for sw in STOP_WORDS)


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# google-genai インポート
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("WARNING: google-genai not installed. build subcommand unavailable.")


# ===== 動画タイトルマップ =====
def build_title_map() -> dict:
    """work/配下の*.info.jsonから video_id → title のマップを構築。"""
    title_map = {}
    if not WORK_DIR.exists():
        return title_map
    for info_file in WORK_DIR.rglob("*.info.json"):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            vid = data.get("id") or info_file.stem.replace(".info", "")
            title = data.get("title", "")
            if vid and title and vid not in title_map:
                title_map[vid] = title
        except Exception:
            pass
    return title_map


# ===== merged JSON 集約 =====
def collect_merged_jsons():
    """重複排除してmerged JSONファイルのリストを返す。
    vocals_版は非vocals版が存在する場合は除外。
    """
    seen_video_ids = set()
    result = []

    if not SRT_CANDIDATES_DIR.exists():
        print(f"ERROR: srt_and_candidates dir not found: {SRT_CANDIDATES_DIR}")
        sys.exit(1)

    for f in sorted(SRT_CANDIDATES_DIR.glob("merged_*.json")):
        stem = f.stem  # e.g. "merged_sQQ1t9OQl2c" or "merged_vocals_iuAP6rAoGFk"
        is_vocals = "vocals_" in stem
        if is_vocals:
            vid = stem.replace("merged_vocals_", "")
            # 非vocals版が存在するなら除外
            if (SRT_CANDIDATES_DIR / f"merged_{vid}.json").exists():
                continue
        else:
            vid = stem.replace("merged_", "")

        if vid in seen_video_ids:
            continue
        seen_video_ids.add(vid)
        result.append((vid, f))

    return result


# ===== セグメント化 =====
def segment_merged_json(words, video_id, source_file):
    """merged JSONのwordsをセグメントに分割。

    分割条件（いずれか）:
    1. 話者が変わった
    2. 前のワードから MAX_GAP_MS 以上の無音ギャップ
    3. セグメント長が MAX_SEG_MS を超えた

    ストップワードを含むセグメントは除外する。
    """
    segments = []
    if not words:
        return segments

    current = {
        "start_ms": None,
        "end_ms": None,
        "speaker": None,
        "texts": [],
    }

    def flush(c):
        if not c["texts"]:
            return
        text = " ".join(c["texts"])
        # 修正1: ストップワードフィルタ
        if is_stopword_segment(text):
            return
        segments.append({
            "video_id": video_id,
            "start_ms": c["start_ms"],
            "end_ms": c["end_ms"],
            "speaker": c["speaker"],
            "text": text,
            "word_count": len(c["texts"]),
            "source_file": source_file,
        })

    for w in words:
        start_ms = int(w.get("start", 0))
        end_ms = int(w.get("end", start_ms))
        speaker = w.get("speaker") or None
        text = (w.get("text") or "").strip()
        if not text:
            continue

        if current["start_ms"] is None:
            # 最初のワード
            current["start_ms"] = start_ms
            current["end_ms"] = end_ms
            current["speaker"] = speaker
            current["texts"] = [text]
            continue

        # 分割判定
        gap_ms = start_ms - current["end_ms"]
        seg_len_ms = start_ms - current["start_ms"]
        speaker_changed = speaker != current["speaker"]
        gap_too_large = gap_ms > MAX_GAP_MS
        seg_too_long = seg_len_ms > MAX_SEG_MS

        if speaker_changed or gap_too_large or seg_too_long:
            flush(current)
            current = {
                "start_ms": start_ms,
                "end_ms": end_ms,
                "speaker": speaker,
                "texts": [text],
            }
        else:
            current["end_ms"] = end_ms
            current["texts"].append(text)

    flush(current)
    return segments


# ===== Embedding =====
def get_client():
    if not HAS_GENAI:
        print("ERROR: google-genai not installed. Run: pip install google-genai")
        sys.exit(1)
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Run: source ~/.bashrc")
        sys.exit(1)
    return genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT"):
    """テキストリストのembedding取得（バッチ処理）。L2正規化済みnp.array返す。"""
    all_embeds = []
    n_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Embedding batch {batch_num}/{n_batches} ({len(batch)} items)...")
        success = False
        for attempt in range(2):
            try:
                response = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=batch,
                    config=genai_types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=EMBED_DIM,
                    ),
                )
                for emb in response.embeddings:
                    all_embeds.append(emb.values)
                time.sleep(0.5)
                success = True
                break
            except Exception as e:
                print(f"  WARNING: Embedding error (attempt {attempt+1}): {e}")
                if attempt == 0:
                    time.sleep(5)
        if not success:
            print("  ERROR: Embedding failed. Using zero vectors.")
            for _ in batch:
                all_embeds.append([0.0] * EMBED_DIM)

    embeddings = np.array(all_embeds, dtype=np.float32)
    # L2正規化（cosine = dot product）
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)
    return embeddings / norms


# ===== インデックス I/O =====
def load_index():
    """インデックスを読み込む。存在しない場合は (None, []) を返す。"""
    if EMBEDDINGS_FILE.exists() and METADATA_FILE.exists():
        embeddings = np.load(str(EMBEDDINGS_FILE))
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return embeddings, metadata
    return None, []


def save_index(embeddings, metadata):
    """インデックスを保存。"""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(str(EMBEDDINGS_FILE), embeddings)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def save_build_info(n_segments, n_videos):
    build_info = {
        "build_time": datetime.now().isoformat(),
        "n_segments": n_segments,
        "n_videos": n_videos,
        "version": "v2",
        "model": EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "max_seg_ms": MAX_SEG_MS,
        "max_gap_ms": MAX_GAP_MS,
    }
    with open(BUILD_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(build_info, f, ensure_ascii=False, indent=2)


# ===== 検索 =====
def search(query_embedding, embeddings, metadata, top_k=10, video_id=None, speaker=None):
    """cosine similarity検索。フィルタオプション付き。"""
    scores = embeddings @ query_embedding  # (N,) — both L2 normalized

    # フィルタリング
    if video_id:
        mask = np.array([m["video_id"] == video_id for m in metadata], dtype=bool)
        scores = np.where(mask, scores, -2.0)
    if speaker:
        mask = np.array([m.get("speaker") == speaker for m in metadata], dtype=bool)
        scores = np.where(mask, scores, -2.0)

    top_indices = np.argsort(scores)[::-1][:top_k * 5]  # 余分に取得してdedup後top_k
    results = []
    for idx in top_indices:
        if scores[idx] <= 0:
            break
        results.append({**metadata[idx], "score": float(scores[idx])})

    # 修正2: 重複排除（同一video_id + ±10秒以内 → 最高スコアのみ）
    results = deduplicate_results(results)

    return results[:top_k]


def deduplicate_results(results, window_ms=10000):
    """同一video_id + 時間帯重複（±10秒以内）は最高スコアのみ残す。
    resultsはスコア降順前提。
    """
    deduped = []
    for r in results:
        is_dup = False
        for d in deduped:
            if d["video_id"] != r["video_id"]:
                continue
            # 開始時刻が±10秒以内なら重複とみなす
            if abs(r["start_ms"] - d["start_ms"]) <= window_ms:
                is_dup = True
                break
        if not is_dup:
            deduped.append(r)
    return deduped


def ms_to_timestr(ms):
    """ミリ秒を MM:SS 形式に変換。"""
    total_s = ms // 1000
    m = total_s // 60
    s = total_s % 60
    return f"{m:02d}:{s:02d}"


# ===== サブコマンド =====
def cmd_build(args):
    """インデックス構築。--update で新規JSONのみ追加。"""
    print("=== scene_search_v2: build ===")
    files = collect_merged_jsons()
    print(f"対象ファイル数: {len(files)}")

    # 修正3: 差分ビルド（--update）
    existing_embeddings = None
    existing_metadata = []
    existing_video_ids = set()

    if getattr(args, "update", False):
        existing_embeddings, existing_metadata = load_index()
        if existing_embeddings is not None:
            existing_video_ids = {m["video_id"] for m in existing_metadata}
            print(f"既存インデックス: {len(existing_metadata)} セグメント, {len(existing_video_ids)} 動画")
            # 新規ファイルのみに絞る
            files = [(vid, f) for vid, f in files if vid not in existing_video_ids]
            print(f"新規ファイル数: {len(files)}")
            if not files:
                print("追加対象なし。インデックスは最新です。")
                return
        else:
            print("既存インデックスなし。フルビルドで実行。")

    all_segments = []
    skipped_stopword = 0
    for vid, path in files:
        print(f"  {vid}: {path.name}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        words = data.get("words", [])
        segs_before = len(words)
        segs = segment_merged_json(words, vid, str(path.relative_to(PROJECT_ROOT)))
        print(f"    → {len(words)} words → {len(segs)} segments")
        all_segments.extend(segs)

    print(f"\n新規セグメント数: {len(all_segments)}")
    if not all_segments:
        print("セグメントなし。終了。")
        return

    print("Embedding 処理開始...")
    client = get_client()
    texts = [s["text"] for s in all_segments]
    new_embeddings = embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT")

    # 差分ビルド: 既存に追記
    if existing_embeddings is not None and len(existing_metadata) > 0:
        merged_embeddings = np.concatenate([existing_embeddings, new_embeddings], axis=0)
        merged_metadata = existing_metadata + all_segments
    else:
        merged_embeddings = new_embeddings
        merged_metadata = all_segments

    print(f"\nインデックス保存: {INDEX_DIR}")
    save_index(merged_embeddings, merged_metadata)
    all_vids = set(m["video_id"] for m in merged_metadata)
    save_build_info(len(merged_metadata), len(all_vids))

    print(f"完了: {len(merged_metadata)} セグメント, {len(all_vids)} 動画")
    print(f"  embeddings.npy: {merged_embeddings.shape}")
    print(f"  metadata.json: {len(merged_metadata)} エントリ")


def cmd_query(args):
    """セマンティック検索。"""
    embeddings, metadata = load_index()
    if embeddings is None:
        print("ERROR: インデックスが存在しません。先に build を実行してください。")
        sys.exit(1)

    # 修正4: タイトルマップ構築
    title_map = build_title_map()

    client = get_client()
    print(f'検索中: "{args.query}"')
    query_emb = embed_texts(client, [args.query], task_type="RETRIEVAL_QUERY")[0]

    results = search(
        query_emb, embeddings, metadata,
        top_k=args.top,
        video_id=args.video,
        speaker=args.speaker,
    )

    if args.json:
        output = {
            "query": args.query,
            "results": [
                {
                    "rank": i + 1,
                    "score": r["score"],
                    "video_id": r["video_id"],
                    "title": title_map.get(r["video_id"], ""),
                    "start_ms": r["start_ms"],
                    "end_ms": r["end_ms"],
                    "speaker": r.get("speaker"),
                    "text": r["text"],
                    "word_count": r["word_count"],
                }
                for i, r in enumerate(results)
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n# {'Rank':<4} {'Score':<6} {'Video':<14} {'Time':<11} {'Speaker':<10} {'Title':<30} Text")
        print("-" * 100)
        for i, r in enumerate(results):
            time_str = f"{ms_to_timestr(r['start_ms'])}-{ms_to_timestr(r['end_ms'])}"
            speaker = r.get("speaker") or "?"
            title = title_map.get(r["video_id"], "")
            title_short = title[:28] + ".." if len(title) > 30 else title
            text = r["text"]
            if len(text) > 40:
                text = text[:37] + "..."
            print(f"{i+1:<4} {r['score']:.3f}  {r['video_id']:<14} {time_str:<11} {speaker:<10} {title_short:<30} {text}")


def cmd_info(args):
    """インデックス情報表示。"""
    if not INDEX_DIR.exists():
        print("インデックスが存在しません。build を実行してください。")
        return

    if BUILD_INFO_FILE.exists():
        with open(BUILD_INFO_FILE, "r", encoding="utf-8") as f:
            info = json.load(f)
        print("=== scene_index_v2 情報 ===")
        for k, v in info.items():
            print(f"  {k}: {v}")
    else:
        print("build_info.json が見つかりません。")

    if EMBEDDINGS_FILE.exists():
        emb = np.load(str(EMBEDDINGS_FILE))
        print(f"  embeddings shape: {emb.shape}")
        print(f"  ファイルサイズ: {EMBEDDINGS_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        videos = set(m["video_id"] for m in meta)
        print(f"  動画数: {len(videos)}")
        speakers = set(m.get("speaker") for m in meta if m.get("speaker"))
        print(f"  話者: {sorted(speakers)}")


# ===== エントリポイント =====
def main():
    parser = argparse.ArgumentParser(
        description="セマンティックシーン検索 (merged JSON + Gemini Embedding 2)"
    )
    sub = parser.add_subparsers(dest="subcommand")

    # build
    b = sub.add_parser("build", help="インデックス構築")
    b.add_argument("--update", action="store_true", help="新規JSONのみEmbedding化して既存インデックスに追加")

    # query
    q = sub.add_parser("query", help="セマンティック検索")
    q.add_argument("query", help="検索クエリ")
    q.add_argument("--top", type=int, default=10, help="上位N件 (default: 10)")
    q.add_argument("--video", help="動画IDでフィルタ")
    q.add_argument("--speaker", help="話者名でフィルタ")
    q.add_argument("--json", action="store_true", help="JSON形式で出力")

    # info
    sub.add_parser("info", help="インデックス情報表示")

    args = parser.parse_args()

    if args.subcommand == "build":
        cmd_build(args)
    elif args.subcommand == "query":
        cmd_query(args)
    elif args.subcommand == "info":
        cmd_info(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
