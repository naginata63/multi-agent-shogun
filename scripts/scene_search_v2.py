#!/usr/bin/env python3
"""
scene_search_v2.py — セマンティックシーン検索 (merged JSON + numpy cosine similarity)

使い方:
    python3 scripts/scene_search_v2.py build                   # words + chunks 両方ビルド
    python3 scripts/scene_search_v2.py build --mode words      # word-levelのみ
    python3 scripts/scene_search_v2.py build --mode chunks     # chunksのみ
    python3 scripts/scene_search_v2.py build --update          # 新規JSONのみ追加
    python3 scripts/scene_search_v2.py query "てぇてぇ" --top 10
    python3 scripts/scene_search_v2.py query "MENのボケ" --video Bxl6QhjtH7s --top 5
    python3 scripts/scene_search_v2.py query "裏切り" --speaker bon --json
    python3 scripts/scene_search_v2.py query "仕事を断る" --mode words
    python3 scripts/scene_search_v2.py find-similar a9rkN9zYwTc 13:30 --top 10
    python3 scripts/scene_search_v2.py interactions --top 20
    python3 scripts/scene_search_v2.py interactions --speaker oo_men --top 10
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

# words インデックス（既存）
EMBEDDINGS_FILE = INDEX_DIR / "embeddings.npy"
METADATA_FILE = INDEX_DIR / "metadata.json"
BUILD_INFO_FILE = INDEX_DIR / "build_info.json"

# chunks インデックス（新規）
CHUNKS_EMBEDDINGS_FILE = INDEX_DIR / "chunks_embeddings.npy"
CHUNKS_METADATA_FILE = INDEX_DIR / "chunks_metadata.json"

EMBED_MODEL = "gemini-embedding-2-preview"
EMBED_DIM = 3072
BATCH_SIZE = 100

# セグメント化パラメータ（word-level）
MAX_SEG_MS = 5000    # セグメント最大長 5秒
MAX_GAP_MS = 2000    # 無音ギャップ閾値 2秒

# チャンクパラメータ（30秒スライディングウィンドウ）
CHUNK_DURATION_MS = 30000   # チャンク長 30秒
CHUNK_OVERLAP_MS = 15000    # オーバーラップ 15秒
CHUNK_STEP_MS = CHUNK_DURATION_MS - CHUNK_OVERLAP_MS  # ステップ = 15秒

# ===== ストップワードフィルタ =====
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


# ===== セグメント化（word-level） =====
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
            "index_mode": "words",
        })

    for w in words:
        start_ms = int(w.get("start", 0))
        end_ms = int(w.get("end", start_ms))
        speaker = w.get("speaker") or None
        text = (w.get("text") or "").strip()
        if not text:
            continue

        if current["start_ms"] is None:
            current["start_ms"] = start_ms
            current["end_ms"] = end_ms
            current["speaker"] = speaker
            current["texts"] = [text]
            continue

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


# ===== チャンク化（30秒スライディングウィンドウ） =====
def create_chunks_from_words(words, video_id, source_file):
    """30秒スライディングウィンドウでチャンクを生成。

    各チャンク:
    - start_ms〜start_ms+30秒の全ワードを連結
    - 話者ラベル付きテキスト: "[speaker]: text ..."
    - 掛け合いスコアメタデータを付与

    返り値: List[dict] — チャンクメタデータリスト
    """
    chunks = []
    if not words:
        return chunks

    # ワードを時系列ソート
    sorted_words = sorted(words, key=lambda w: int(w.get("start", 0)))
    if not sorted_words:
        return chunks

    total_start = int(sorted_words[0].get("start", 0))
    total_end = int(sorted_words[-1].get("end", total_start))
    total_duration = total_end - total_start

    if total_duration < 1000:
        return chunks

    # スライディングウィンドウ
    window_start = total_start
    while window_start < total_end:
        window_end = window_start + CHUNK_DURATION_MS

        # このウィンドウ内のワードを収集
        window_words = [
            w for w in sorted_words
            if int(w.get("start", 0)) >= window_start and int(w.get("start", 0)) < window_end
        ]

        if len(window_words) < 3:
            window_start += CHUNK_STEP_MS
            continue

        # 話者ラベル付きテキスト構築
        text_parts = []
        prev_speaker = None
        for w in window_words:
            speaker = w.get("speaker") or "?"
            text = (w.get("text") or "").strip()
            if not text:
                continue
            if speaker != prev_speaker:
                text_parts.append(f"[{speaker}]:")
                prev_speaker = speaker
            text_parts.append(text)

        chunk_text = " ".join(text_parts)

        if is_stopword_segment(chunk_text):
            window_start += CHUNK_STEP_MS
            continue

        # 掛け合いスコア計算
        actual_start = int(window_words[0].get("start", window_start))
        actual_end = int(window_words[-1].get("end", window_end))
        duration_ms = max(actual_end - actual_start, 1)
        duration_sec = duration_ms / 1000.0

        # 話者交代回数
        speakers_seq = [w.get("speaker") or "?" for w in window_words]
        speaker_changes = sum(
            1 for i in range(1, len(speakers_seq))
            if speakers_seq[i] != speakers_seq[i - 1]
        )

        unique_speakers = sorted(set(s for s in speakers_seq if s != "?"))

        # 平均セリフ長（話者交代ごとのセグメント単位）
        segments_in_chunk = []
        seg_start = actual_start
        seg_speaker = speakers_seq[0] if speakers_seq else "?"
        for i, w in enumerate(window_words):
            if i > 0 and speakers_seq[i] != seg_speaker:
                seg_end = int(window_words[i - 1].get("end", seg_start))
                segments_in_chunk.append(seg_end - seg_start)
                seg_start = int(w.get("start", seg_start))
                seg_speaker = speakers_seq[i]
        if window_words:
            last_end = int(window_words[-1].get("end", seg_start))
            segments_in_chunk.append(last_end - seg_start)

        avg_line_duration_ms = int(
            sum(segments_in_chunk) / len(segments_in_chunk)
        ) if segments_in_chunk else duration_ms

        # テンポボーナス: 平均セリフが短いほど掛け合いが速い
        tempo_bonus = 1.0
        if avg_line_duration_ms < 3000:
            tempo_bonus = 1.5
        elif avg_line_duration_ms < 5000:
            tempo_bonus = 1.2

        interaction_score = (speaker_changes / duration_sec) * tempo_bonus

        chunks.append({
            "video_id": video_id,
            "start_ms": actual_start,
            "end_ms": actual_end,
            "text": chunk_text,
            "word_count": len(window_words),
            "source_file": source_file,
            "index_mode": "chunks",
            # 掛け合いメタデータ
            "speaker_changes": speaker_changes,
            "speakers": unique_speakers,
            "avg_line_duration_ms": avg_line_duration_ms,
            "interaction_score": round(interaction_score, 4),
            "duration_ms": duration_ms,
        })

        window_start += CHUNK_STEP_MS

    return chunks


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
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)
    return embeddings / norms


# ===== インデックス I/O =====
def load_index(mode="chunks"):
    """インデックスを読み込む。存在しない場合は (None, []) を返す。
    mode: "words" → word-level, "chunks" → 30秒チャンク
    """
    if mode == "words":
        emb_file, meta_file = EMBEDDINGS_FILE, METADATA_FILE
    else:
        emb_file, meta_file = CHUNKS_EMBEDDINGS_FILE, CHUNKS_METADATA_FILE

    if emb_file.exists() and meta_file.exists():
        embeddings = np.load(str(emb_file))
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return embeddings, metadata
    return None, []


def save_index(embeddings, metadata, mode="chunks"):
    """インデックスを保存。"""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if mode == "words":
        emb_file, meta_file = EMBEDDINGS_FILE, METADATA_FILE
    else:
        emb_file, meta_file = CHUNKS_EMBEDDINGS_FILE, CHUNKS_METADATA_FILE

    np.save(str(emb_file), embeddings)
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def save_build_info(n_words_segs, n_chunk_segs, n_videos):
    build_info = {
        "build_time": datetime.now().isoformat(),
        "n_word_segments": n_words_segs,
        "n_chunk_segments": n_chunk_segs,
        "n_videos": n_videos,
        "version": "v2.1",
        "model": EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "max_seg_ms": MAX_SEG_MS,
        "max_gap_ms": MAX_GAP_MS,
        "chunk_duration_ms": CHUNK_DURATION_MS,
        "chunk_overlap_ms": CHUNK_OVERLAP_MS,
    }
    with open(BUILD_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(build_info, f, ensure_ascii=False, indent=2)


# ===== 検索 =====
def search(query_embedding, embeddings, metadata, top_k=10, video_id=None, speaker=None):
    """cosine similarity検索。フィルタオプション付き。"""
    scores = embeddings @ query_embedding  # (N,) — both L2 normalized

    if video_id:
        mask = np.array([m["video_id"] == video_id for m in metadata], dtype=bool)
        scores = np.where(mask, scores, -2.0)
    if speaker:
        # words mode: speaker field / chunks mode: speakers list
        def speaker_match(m):
            if "speakers" in m:
                return speaker in m["speakers"]
            return m.get("speaker") == speaker
        mask = np.array([speaker_match(m) for m in metadata], dtype=bool)
        scores = np.where(mask, scores, -2.0)

    top_indices = np.argsort(scores)[::-1][:top_k * 10]
    results = []
    for idx in top_indices:
        if scores[idx] <= 0:
            break
        results.append({**metadata[idx], "score": float(scores[idx])})

    results = deduplicate_results(results)
    return results[:top_k]


def deduplicate_results(results, window_ms=10000):
    """同一video_id + 時間帯重複（±10秒以内）は最高スコアのみ残す。"""
    deduped = []
    for r in results:
        is_dup = False
        for d in deduped:
            if d["video_id"] != r["video_id"]:
                continue
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


def timestr_to_ms(timestr):
    """MM:SS 形式をミリ秒に変換。"""
    parts = timestr.strip().split(":")
    if len(parts) == 2:
        return (int(parts[0]) * 60 + int(parts[1])) * 1000
    elif len(parts) == 3:
        return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
    raise ValueError(f"Invalid time format: {timestr}")


# ===== サブコマンド =====
def cmd_build(args):
    """インデックス構築。--mode で words/chunks/both（デフォルト）。"""
    mode = getattr(args, "mode", "both")
    update = getattr(args, "update", False)
    print(f"=== scene_search_v2: build (mode={mode}, update={update}) ===")

    all_files = collect_merged_jsons()
    print(f"対象ファイル数: {len(all_files)}")

    # 差分ビルド（--update）: words/chunks のインデックスを独立に管理
    existing_words_emb = None
    existing_words_meta = []
    existing_chunks_emb = None
    existing_chunks_meta = []
    words_video_ids = set()
    chunks_video_ids = set()

    if update:
        if mode in ("words", "both"):
            existing_words_emb, existing_words_meta = load_index("words")
            if existing_words_emb is not None:
                words_video_ids = {m["video_id"] for m in existing_words_meta}
                print(f"  words既存: {len(existing_words_meta)} segs, {len(words_video_ids)} 動画")
        if mode in ("chunks", "both"):
            existing_chunks_emb, existing_chunks_meta = load_index("chunks")
            if existing_chunks_emb is not None:
                chunks_video_ids = {m["video_id"] for m in existing_chunks_meta}
                print(f"  chunks既存: {len(existing_chunks_meta)} chunks, {len(chunks_video_ids)} 動画")

    # 処理対象ファイルをmode別に決定
    words_files = all_files if not update else [(v, f) for v, f in all_files if v not in words_video_ids]
    chunks_files = all_files if not update else [(v, f) for v, f in all_files if v not in chunks_video_ids]

    if mode == "words":
        chunks_files = []
    elif mode == "chunks":
        words_files = []

    print(f"  words新規: {len(words_files)} 動画, chunks新規: {len(chunks_files)} 動画")
    if not words_files and not chunks_files:
        print("追加対象なし。インデックスは最新です。")
        return

    # 処理が必要な動画の統合リスト（重複なし）
    target_vids = set(v for v, _ in words_files) | set(v for v, _ in chunks_files)
    target_files = [(v, f) for v, f in all_files if v in target_vids]

    # セグメント・チャンク収集
    all_word_segments = []
    all_chunks = []

    for vid, path in target_files:
        print(f"  {vid}: {path.name}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        words = data.get("words", [])
        rel_path = str(path.relative_to(PROJECT_ROOT))

        if vid in {v for v, _ in words_files}:
            segs = segment_merged_json(words, vid, rel_path)
            print(f"    → {len(words)} words → {len(segs)} word-segments")
            all_word_segments.extend(segs)

        if vid in {v for v, _ in chunks_files}:
            chunks = create_chunks_from_words(words, vid, rel_path)
            print(f"    → {len(chunks)} 30s-chunks")
            all_chunks.extend(chunks)

    client = get_client()

    # words インデックス
    if all_word_segments:
        print(f"\n新規word-segments: {len(all_word_segments)}")
        print("Word Embedding 処理開始...")
        texts = [s["text"] for s in all_word_segments]
        new_emb = embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT")

        if existing_words_emb is not None and len(existing_words_meta) > 0:
            merged_emb = np.concatenate([existing_words_emb, new_emb], axis=0)
            merged_meta = existing_words_meta + all_word_segments
        else:
            merged_emb = new_emb
            merged_meta = all_word_segments

        print(f"Words インデックス保存: {len(merged_meta)} セグメント")
        save_index(merged_emb, merged_meta, mode="words")

    # chunks インデックス
    if all_chunks:
        print(f"\n新規chunks: {len(all_chunks)}")
        print("Chunk Embedding 処理開始...")
        texts = [c["text"] for c in all_chunks]
        new_emb = embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT")

        if existing_chunks_emb is not None and len(existing_chunks_meta) > 0:
            merged_emb = np.concatenate([existing_chunks_emb, new_emb], axis=0)
            merged_meta = existing_chunks_meta + all_chunks
        else:
            merged_emb = new_emb
            merged_meta = all_chunks

        print(f"Chunks インデックス保存: {len(merged_meta)} チャンク")
        save_index(merged_emb, merged_meta, mode="chunks")

    # build_info 更新
    w_emb, w_meta = load_index("words")
    c_emb, c_meta = load_index("chunks")
    all_vids = set()
    if w_meta:
        all_vids |= {m["video_id"] for m in w_meta}
    if c_meta:
        all_vids |= {m["video_id"] for m in c_meta}
    save_build_info(len(w_meta) if w_meta else 0, len(c_meta) if c_meta else 0, len(all_vids))
    print(f"\n完了: words={len(w_meta) if w_meta else 0}, chunks={len(c_meta) if c_meta else 0}, 動画数={len(all_vids)}")


def cmd_query(args):
    """セマンティック検索。デフォルトはchunksインデックス。--mode words で旧式。"""
    mode = getattr(args, "mode", "chunks")
    embeddings, metadata = load_index(mode)
    if embeddings is None:
        print(f"ERROR: {mode}インデックスが存在しません。先に build を実行してください。")
        sys.exit(1)

    title_map = build_title_map()
    client = get_client()
    print(f'検索中 (mode={mode}): "{args.query}"')
    query_emb = embed_texts(client, [args.query], task_type="RETRIEVAL_QUERY")[0]

    results = search(
        query_emb, embeddings, metadata,
        top_k=args.top,
        video_id=getattr(args, "video", None),
        speaker=getattr(args, "speaker", None),
    )

    if args.json:
        output = {
            "query": args.query,
            "mode": mode,
            "results": [
                {
                    "rank": i + 1,
                    "score": r["score"],
                    "video_id": r["video_id"],
                    "title": title_map.get(r["video_id"], ""),
                    "start_ms": r["start_ms"],
                    "end_ms": r["end_ms"],
                    "speaker": r.get("speaker") or r.get("speakers"),
                    "text": r["text"],
                    "word_count": r["word_count"],
                    "interaction_score": r.get("interaction_score"),
                    "speaker_changes": r.get("speaker_changes"),
                }
                for i, r in enumerate(results)
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n# {'Rank':<4} {'Score':<6} {'Video':<14} {'Time':<11} {'Speaker':<14} {'Title':<28} Text")
        print("-" * 110)
        for i, r in enumerate(results):
            time_str = f"{ms_to_timestr(r['start_ms'])}-{ms_to_timestr(r['end_ms'])}"
            if mode == "words":
                speaker = r.get("speaker") or "?"
            else:
                spk_list = r.get("speakers", [])
                speaker = ",".join(spk_list[:3]) if spk_list else "?"
                if r.get("interaction_score"):
                    speaker += f" (i={r['interaction_score']:.2f})"
            title = title_map.get(r["video_id"], "")
            title_short = title[:26] + ".." if len(title) > 28 else title
            text = r["text"]
            if len(text) > 40:
                text = text[:37] + "..."
            print(f"{i+1:<4} {r['score']:.3f}  {r['video_id']:<14} {time_str:<11} {speaker:<14} {title_short:<28} {text}")


def cmd_find_similar(args):
    """指定した動画・時刻に近いチャンクと類似するチャンクを検索。
    使い方: find-similar <video_id> <MM:SS> [--top N]
    """
    embeddings, metadata = load_index("chunks")
    if embeddings is None:
        print("ERROR: chunksインデックスが存在しません。先に build を実行してください。")
        sys.exit(1)

    try:
        target_ms = timestr_to_ms(args.time)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # 指定動画・時刻に最も近いチャンクを探す
    target_idx = None
    min_dist = float("inf")
    for i, m in enumerate(metadata):
        if m["video_id"] != args.video_id:
            continue
        # チャンクの中心との距離
        center = (m["start_ms"] + m["end_ms"]) / 2
        dist = abs(center - target_ms)
        if dist < min_dist:
            min_dist = dist
            target_idx = i

    if target_idx is None:
        print(f"ERROR: 動画 {args.video_id} がchunksインデックスに存在しません。")
        sys.exit(1)

    ref_chunk = metadata[target_idx]
    print(f"参照チャンク: {args.video_id} {ms_to_timestr(ref_chunk['start_ms'])}-{ms_to_timestr(ref_chunk['end_ms'])}")
    print(f"  話者: {ref_chunk.get('speakers', [])}")
    print(f"  掛け合いスコア: {ref_chunk.get('interaction_score', 'N/A')}")
    print(f"  テキスト: {ref_chunk['text'][:80]}...")
    print()

    # 類似検索（同一動画・同一時刻は除外）
    ref_emb = embeddings[target_idx]
    scores = embeddings @ ref_emb

    # 同一動画の近接チャンクを除外（参照動画±60秒以内）
    for i, m in enumerate(metadata):
        if m["video_id"] == args.video_id and abs(m["start_ms"] - ref_chunk["start_ms"]) <= 60000:
            scores[i] = -2.0

    top_indices = np.argsort(scores)[::-1][: args.top * 5]
    results = []
    for idx in top_indices:
        if scores[idx] <= 0:
            break
        results.append({**metadata[idx], "score": float(scores[idx])})

    results = deduplicate_results(results)
    results = results[: args.top]

    title_map = build_title_map()
    print(f"類似シーン Top {len(results)}:")
    print(f"{'Rank':<4} {'Score':<6} {'Video':<14} {'Time':<11} {'iScore':<8} {'Speakers':<20} Text")
    print("-" * 100)
    for i, r in enumerate(results):
        time_str = f"{ms_to_timestr(r['start_ms'])}-{ms_to_timestr(r['end_ms'])}"
        spk = ",".join(r.get("speakers", [])[:3])
        iscore = r.get("interaction_score", 0)
        text = r["text"][:40] + "..." if len(r["text"]) > 40 else r["text"]
        print(f"{i+1:<4} {r['score']:.3f}  {r['video_id']:<14} {time_str:<11} {iscore:<8.2f} {spk:<20} {text}")


def cmd_interactions(args):
    """掛け合いスコアが高いシーン一覧を表示。
    使い方: interactions [--top N] [--speaker SPEAKER] [--video VIDEO_ID] [--min-score SCORE]
    """
    _, metadata = load_index("chunks")
    if not metadata:
        print("ERROR: chunksインデックスが存在しません。先に build を実行してください。")
        sys.exit(1)

    # フィルタリング
    filtered = metadata
    if getattr(args, "speaker", None):
        filtered = [m for m in filtered if args.speaker in m.get("speakers", [])]
    if getattr(args, "video", None):
        filtered = [m for m in filtered if m["video_id"] == args.video]
    min_score = getattr(args, "min_score", 0.0)
    if min_score > 0:
        filtered = [m for m in filtered if m.get("interaction_score", 0) >= min_score]

    # 掛け合いスコア降順ソート
    sorted_chunks = sorted(filtered, key=lambda m: m.get("interaction_score", 0), reverse=True)

    title_map = build_title_map()
    top_n = args.top
    results = sorted_chunks[:top_n]

    print(f"掛け合いシーン Top {len(results)} (全{len(filtered)}件中):")
    if getattr(args, "speaker", None):
        print(f"  話者フィルタ: {args.speaker}")
    print()
    print(f"{'Rank':<4} {'iScore':<8} {'Chg':<5} {'Video':<14} {'Time':<11} {'Speakers':<24} Text")
    print("-" * 110)
    for i, r in enumerate(results):
        time_str = f"{ms_to_timestr(r['start_ms'])}-{ms_to_timestr(r['end_ms'])}"
        spk = ",".join(r.get("speakers", [])[:4])
        chg = r.get("speaker_changes", 0)
        iscore = r.get("interaction_score", 0)
        text = r["text"][:45] + "..." if len(r["text"]) > 45 else r["text"]
        print(f"{i+1:<4} {iscore:<8.3f} {chg:<5} {r['video_id']:<14} {time_str:<11} {spk:<24} {text}")


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

    # words インデックス
    if EMBEDDINGS_FILE.exists():
        emb = np.load(str(EMBEDDINGS_FILE))
        print(f"\n[words インデックス]")
        print(f"  shape: {emb.shape}")
        print(f"  ファイルサイズ: {EMBEDDINGS_FILE.stat().st_size / 1024 / 1024:.1f} MB")
        if METADATA_FILE.exists():
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
            videos = set(m["video_id"] for m in meta)
            print(f"  動画数: {len(videos)}")
            speakers = set(m.get("speaker") for m in meta if m.get("speaker"))
            print(f"  話者: {sorted(speakers)}")

    # chunks インデックス
    if CHUNKS_EMBEDDINGS_FILE.exists():
        emb = np.load(str(CHUNKS_EMBEDDINGS_FILE))
        print(f"\n[chunks インデックス]")
        print(f"  shape: {emb.shape}")
        print(f"  ファイルサイズ: {CHUNKS_EMBEDDINGS_FILE.stat().st_size / 1024 / 1024:.1f} MB")
        if CHUNKS_METADATA_FILE.exists():
            with open(CHUNKS_METADATA_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
            videos = set(m["video_id"] for m in meta)
            print(f"  動画数: {len(videos)}")
            speakers_flat = set()
            for m in meta:
                for s in m.get("speakers", []):
                    speakers_flat.add(s)
            print(f"  話者: {sorted(speakers_flat)}")
            scores = [m.get("interaction_score", 0) for m in meta]
            if scores:
                print(f"  掛け合いスコア: max={max(scores):.3f}, avg={sum(scores)/len(scores):.3f}")


# ===== エントリポイント =====
def main():
    parser = argparse.ArgumentParser(
        description="セマンティックシーン検索 (merged JSON + Gemini Embedding 2)"
    )
    sub = parser.add_subparsers(dest="subcommand")

    # build
    b = sub.add_parser("build", help="インデックス構築")
    b.add_argument("--mode", choices=["words", "chunks", "both"], default="both",
                   help="インデックスモード (default: both)")
    b.add_argument("--update", action="store_true", help="新規JSONのみEmbedding化して既存インデックスに追加")

    # query
    q = sub.add_parser("query", help="セマンティック検索")
    q.add_argument("query", help="検索クエリ")
    q.add_argument("--top", type=int, default=10, help="上位N件 (default: 10)")
    q.add_argument("--video", help="動画IDでフィルタ")
    q.add_argument("--speaker", help="話者名でフィルタ")
    q.add_argument("--json", action="store_true", help="JSON形式で出力")
    q.add_argument("--mode", choices=["words", "chunks"], default="chunks",
                   help="検索モード (default: chunks)")

    # find-similar
    fs = sub.add_parser("find-similar", help="指定時刻に近いシーンと類似するシーンを検索")
    fs.add_argument("video_id", help="参照動画ID")
    fs.add_argument("time", help="参照時刻 (MM:SS)")
    fs.add_argument("--top", type=int, default=10, help="上位N件 (default: 10)")

    # interactions
    ia = sub.add_parser("interactions", help="掛け合いスコアが高いシーン一覧")
    ia.add_argument("--top", type=int, default=20, help="上位N件 (default: 20)")
    ia.add_argument("--speaker", help="話者名でフィルタ")
    ia.add_argument("--video", help="動画IDでフィルタ")
    ia.add_argument("--min-score", type=float, default=0.0, dest="min_score",
                    help="最小掛け合いスコア (default: 0.0)")

    # info
    sub.add_parser("info", help="インデックス情報表示")

    args = parser.parse_args()

    if args.subcommand == "build":
        cmd_build(args)
    elif args.subcommand == "query":
        cmd_query(args)
    elif args.subcommand == "find-similar":
        cmd_find_similar(args)
    elif args.subcommand == "interactions":
        cmd_interactions(args)
    elif args.subcommand == "info":
        cmd_info(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
