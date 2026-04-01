#!/usr/bin/env python3
"""
字幕セマンティック検索 BigQuery移行スクリプト（一回限り実行）

概要:
  - FAISSインデックス + レジストリ + merged JSON からデータを再構築
  - BigQuery データセット/テーブルを作成
  - 全チャンク（メタデータ + ベクトル）を BigQuery にアップロード

使い方:
  cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
  source ../config/vertex_api_key.env
  python3 ../../scripts/bq_subtitle_migrate.py [--dry-run] [--skip-upload]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import faiss
import numpy as np
import yaml

# ===== 設定 =====
BASE_DIR = Path(__file__).parent.parent
DOZLE_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
INDEX_DIR = DOZLE_DIR / "work" / "subtitle_index"
FAISS_FILE = INDEX_DIR / "subtitle_index.faiss"
REGISTRY_FILE = DOZLE_DIR / "reports" / "semantic_index_registry.yaml"
WORK_DIR = BASE_DIR / "work" / "cmd_1071"
JSONL_FILE = WORK_DIR / "subtitle_chunks.jsonl"
SCHEMA_FILE = WORK_DIR / "bq_schema.json"

GCP_PROJECT = "dozlesha-mainichi-kirinuki"
BQ_DATASET = "dozle_subtitle_semantic"
BQ_TABLE = "subtitle_chunks"
FULL_TABLE = f"{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

CHUNK_SECONDS = 30


def load_registry():
    if not REGISTRY_FILE.exists():
        print(f"ERROR: registry not found: {REGISTRY_FILE}")
        sys.exit(1)
    with open(REGISTRY_FILE, encoding="utf-8") as f:
        reg = yaml.safe_load(f)
    return reg.get("videos", [])


def find_merged_json(video_id: str) -> Path | None:
    """video_idからmerged_*.jsonファイルを検索"""
    work_dir = DOZLE_DIR / "work"
    candidates = list(work_dir.rglob(f"merged_{video_id}.json"))
    if candidates:
        return candidates[0]
    # video_idが完全一致しない場合のフォールバック
    candidates2 = [p for p in work_dir.rglob("merged_*.json") if video_id in p.stem]
    if candidates2:
        return candidates2[0]
    return None


def chunk_merged_json(merged_path: Path, chunk_sec=CHUNK_SECONDS):
    """merged JSONから30秒チャンクのリストを返す（subtitle_semantic_index.pyと同一ロジック）"""
    chunks = []
    try:
        with open(merged_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return chunks

    if not isinstance(data, dict):
        return chunks
    words = data.get("words", [])
    meta = data.get("metadata", {})
    video_id = meta.get("video_id", merged_path.stem.replace("merged_", ""))

    if not words:
        return chunks

    chunk_ms = chunk_sec * 1000
    window_start_ms = words[0].get("start", 0)
    window_texts = []

    def flush(ws_ms, we_ms, texts):
        if texts:
            chunks.append({
                "video_id": video_id,
                "start_ms": int(ws_ms),
                "end_ms": int(we_ms),
                "text": "".join(texts),
            })

    for w in words:
        start_ms = w.get("start", 0)
        text = w.get("text", "")
        if start_ms - window_start_ms >= chunk_ms:
            flush(window_start_ms, start_ms, window_texts)
            window_start_ms = start_ms
            window_texts = [text]
        else:
            window_texts.append(text)

    flush(window_start_ms, window_start_ms + chunk_ms, window_texts)
    return chunks


def extract_faiss_vectors():
    """FAISSインデックスから全ベクトルを抽出"""
    if not FAISS_FILE.exists():
        print(f"ERROR: FAISS file not found: {FAISS_FILE}")
        sys.exit(1)
    print(f"FAISSインデックス読み込み: {FAISS_FILE}")
    index = faiss.read_index(str(FAISS_FILE))
    print(f"  ベクトル数: {index.ntotal}, 次元数: {index.d}")
    print("  全ベクトルを抽出中...")
    vectors = index.reconstruct_n(0, index.ntotal)
    print(f"  抽出完了: {vectors.shape}")
    return vectors


def rebuild_metadata(videos: list, max_vectors: int):
    """
    レジストリ順序でメタデータを再構築し、FAISS位置を対応付ける。
    戻り値: [(video_id, start_ms, end_ms, text, faiss_position)]
    """
    entries = []
    faiss_pos = 0
    missing_videos = []

    print(f"\nメタデータ再構築: {len(videos)}動画...")
    for i, v in enumerate(videos):
        video_id = v["video_id"]
        expected_chunks = v.get("chunk_count", 0)

        if faiss_pos >= max_vectors:
            print(f"  STOP: FAISS境界到達 (pos={faiss_pos})")
            break

        # merged JSON検索
        merged_path = find_merged_json(video_id)
        if not merged_path:
            # ファイルなし: スキップしてFAISS位置を進める
            faiss_pos += expected_chunks
            missing_videos.append(video_id)
            continue

        # チャンク化
        chunks = chunk_merged_json(merged_path)
        actual_chunks = len(chunks)

        # FAISS位置との照合
        if actual_chunks != expected_chunks:
            # チャンク数が一致しない: レジストリのchunk_countを信頼
            # 実際のチャンクのみ追加し、残りはスキップ
            use_count = min(actual_chunks, expected_chunks, max_vectors - faiss_pos)
        else:
            use_count = min(actual_chunks, max_vectors - faiss_pos)

        for j in range(use_count):
            if j < actual_chunks:
                c = chunks[j]
                entries.append({
                    "chunk_id": faiss_pos + j,
                    "video_id": c["video_id"],
                    "start_ms": c["start_ms"],
                    "end_ms": c["end_ms"],
                    "text": c["text"],
                    "faiss_pos": faiss_pos + j,
                })

        faiss_pos += expected_chunks

        if (i + 1) % 100 == 0:
            print(f"  進捗: {i+1}/{len(videos)} 動画, {len(entries)} チャンク")

    print(f"\nメタデータ再構築完了:")
    print(f"  チャンク数: {len(entries)}")
    print(f"  ファイル不明動画: {len(missing_videos)}件")
    return entries


def write_schema():
    """BigQueryスキーマJSONを書き出す"""
    schema = [
        {"name": "chunk_id", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "video_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "start_ms", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "end_ms", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "text", "type": "STRING", "mode": "NULLABLE"},
        {"name": "embedding", "type": "FLOAT64", "mode": "REPEATED"},
    ]
    SCHEMA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_FILE, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"スキーマ書き込み: {SCHEMA_FILE}")


def write_jsonl(entries, vectors):
    """JSONL形式でデータを書き出す"""
    JSONL_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nJSONL書き込み: {JSONL_FILE}")
    print(f"  チャンク数: {len(entries)}")

    written = 0
    errors = 0
    with open(JSONL_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            pos = entry["faiss_pos"]
            if pos >= len(vectors):
                errors += 1
                continue
            vec = vectors[pos].tolist()
            row = {
                "chunk_id": entry["chunk_id"],
                "video_id": entry["video_id"],
                "start_ms": entry["start_ms"],
                "end_ms": entry["end_ms"],
                "text": entry["text"],
                "embedding": vec,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    file_size_mb = JSONL_FILE.stat().st_size / (1024 * 1024)
    print(f"  書き込み完了: {written} 行, {file_size_mb:.1f} MB, {errors} エラー")
    return written


def run_bq(cmd: list, check=True) -> subprocess.CompletedProcess:
    """bq CLIを実行する"""
    full_cmd = ["bq"] + cmd
    print(f"  [bq] {' '.join(str(c) for c in full_cmd)}")
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.stdout:
        print(f"  stdout: {result.stdout.strip()[:200]}")
    if result.stderr:
        print(f"  stderr: {result.stderr.strip()[:200]}")
    if check and result.returncode != 0:
        print(f"  ERROR: exit code {result.returncode}")
        sys.exit(1)
    return result


def setup_bigquery():
    """BigQueryデータセット・テーブルを作成"""
    print(f"\n=== BigQuery セットアップ ===")

    # データセット作成（既存はOK）
    result = run_bq([
        "mk", "--dataset", "--location=asia-northeast1",
        f"{GCP_PROJECT}:{BQ_DATASET}"
    ], check=False)
    if result.returncode != 0 and "Already Exists" not in result.stderr:
        print("ERROR: データセット作成失敗")
        sys.exit(1)
    print(f"  データセット: {BQ_DATASET} (OK)")

    # テーブル削除（既存時）
    run_bq(["rm", "-f", "-t", f"{GCP_PROJECT}:{BQ_DATASET}.{BQ_TABLE}"], check=False)

    # テーブル作成
    run_bq([
        "mk", "--table",
        f"{GCP_PROJECT}:{BQ_DATASET}.{BQ_TABLE}",
        str(SCHEMA_FILE)
    ])
    print(f"  テーブル: {BQ_TABLE} (OK)")


def upload_to_bigquery():
    """JSONLをBigQueryにロード"""
    print(f"\n=== BigQuery アップロード ===")
    print(f"  ソース: {JSONL_FILE}")

    run_bq([
        "load",
        "--source_format=NEWLINE_DELIMITED_JSON",
        f"{GCP_PROJECT}:{BQ_DATASET}.{BQ_TABLE}",
        str(JSONL_FILE),
        str(SCHEMA_FILE)
    ])
    print("  アップロード完了")


def verify_upload():
    """アップロードされた行数を確認"""
    print(f"\n=== 検証 ===")
    result = run_bq([
        "query", "--use_legacy_sql=false",
        f"SELECT COUNT(*) as cnt FROM `{FULL_TABLE}`"
    ])
    print(f"  BigQuery行数確認完了")


def main():
    parser = argparse.ArgumentParser(description="字幕セマンティック検索 BigQuery移行")
    parser.add_argument("--dry-run", action="store_true", help="BQ操作をスキップ（データ準備のみ）")
    parser.add_argument("--skip-upload", action="store_true", help="アップロードをスキップ（JSONL生成のみ）")
    parser.add_argument("--skip-jsonl", action="store_true", help="JSONL生成をスキップ（既存JSONL使用）")
    args = parser.parse_args()

    print("=== BigQuery移行スクリプト ===")
    print(f"プロジェクト: {GCP_PROJECT}")
    print(f"テーブル: {FULL_TABLE}")

    # スキーマ書き出し
    write_schema()

    if not args.skip_jsonl:
        # FAISSからベクトル抽出
        vectors = extract_faiss_vectors()

        # レジストリ読み込み
        videos = load_registry()
        print(f"レジストリ: {len(videos)} 動画")

        # メタデータ再構築
        entries = rebuild_metadata(videos, max_vectors=len(vectors))

        # JSONL書き出し
        written = write_jsonl(entries, vectors)
        if written == 0:
            print("ERROR: 書き込み0件")
            sys.exit(1)
    else:
        if not JSONL_FILE.exists():
            print(f"ERROR: JSONL not found: {JSONL_FILE}")
            sys.exit(1)
        print(f"既存JSONLを使用: {JSONL_FILE}")

    if args.dry_run or args.skip_upload:
        print("\n--dry-run/--skip-upload: BQ操作をスキップ")
        print(f"JSONL: {JSONL_FILE}")
        print("完了（BQアップロードなし）")
        return

    # BigQueryセットアップ
    setup_bigquery()

    # アップロード
    upload_to_bigquery()

    # 検証
    verify_upload()

    print("\n=== 移行完了 ===")
    print(f"  BigQueryテーブル: {FULL_TABLE}")
    print(f"  次のステップ: subtitle_semantic_index.py search コマンドで検索テスト")


if __name__ == "__main__":
    main()
