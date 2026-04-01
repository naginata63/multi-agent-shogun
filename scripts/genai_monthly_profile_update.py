#!/usr/bin/env python3
"""
genai_monthly_profile_update.py — Discordリアクション集計 → genai_user_profile.yaml 更新
使用方法: python3 scripts/genai_monthly_profile_update.py [--month YYYY-MM] [--dry-run]

処理概要:
1. queue/genai_feedback.yaml からリアクション履歴を読み込む
2. 指定月（デフォルト: 先月）の ⭐/👎 リアクションを集計
3. カテゴリ・キーワードごとの好評/不評スコアを算出
4. config/genai_user_profile.yaml の interests.high/medium/low を更新
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FEEDBACK_FILE = PROJECT_ROOT / "queue" / "genai_feedback.yaml"
PROFILE_FILE = PROJECT_ROOT / "config" / "genai_user_profile.yaml"
MESSAGE_MAP_FILE = PROJECT_ROOT / "queue" / "discord_message_map.json"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [monthly_update] {msg}", flush=True)


def parse_feedback_yaml(text: str) -> list:
    """genai_feedback.yaml からエントリリストを返す（YAML依存なしの簡易パーサ）。"""
    entries = []
    current = {}
    for line in text.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("- "):
            if current:
                entries.append(current)
            current = {}
            rest = line_stripped[2:]
        else:
            rest = line_stripped

        if ":" in rest:
            key, _, value = rest.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value:
                current[key] = value

    if current:
        entries.append(current)
    return entries


def parse_profile_yaml(text: str) -> dict:
    """genai_user_profile.yaml を dict に変換（最低限のパーサ）。"""
    profile = {"interests": {"high": [], "medium": [], "low": []}, "other": []}
    current_section = None
    current_list_key = None

    for line in text.splitlines():
        if line.startswith("interests:"):
            current_section = "interests"
        elif current_section == "interests":
            m = re.match(r'\s+(high|medium|low):', line)
            if m:
                current_list_key = m.group(1)
            elif current_list_key and re.match(r'\s+-\s+', line):
                item = re.sub(r'^\s+-\s+', '', line).strip()
                if item:
                    profile["interests"][current_list_key].append(item)
            elif line and not line.startswith(" "):
                current_section = None
                current_list_key = None

    return profile


def serialize_profile(original_text: str, profile: dict) -> str:
    """更新済みの interests セクションを元のYAMLテキストに反映して返す。"""
    lines = original_text.splitlines(keepends=True)
    result = []
    in_interests = False
    in_list = False
    skip = False

    for line in lines:
        if line.startswith("interests:"):
            in_interests = True
            result.append(line)
            continue

        if in_interests:
            m = re.match(r'\s+(high|medium|low):', line)
            if m:
                level = m.group(1)
                in_list = True
                skip = True
                result.append(line)
                for item in profile["interests"][level]:
                    result.append(f"    - {item}\n")
                continue

            if in_list and re.match(r'\s+-\s+', line):
                continue  # 古いリスト行は削除

            if line and not line.startswith(" "):
                in_interests = False
                in_list = False

        result.append(line)

    return "".join(result)


def get_target_month(month_str: str | None) -> str:
    """集計対象月 YYYY-MM を返す。Noneなら先月。"""
    if month_str:
        return month_str
    now = datetime.now(timezone.utc)
    if now.month == 1:
        return f"{now.year - 1}-12"
    return f"{now.year}-{now.month - 1:02d}"


def extract_keywords_from_title(title: str) -> list:
    """タイトルから関連キーワードを抽出（プロファイルのinterestsと照合用）。"""
    # 日本語・英語の重要ワードをスペースや記号で分割
    words = re.split(r'[\s/・、。,]+', title)
    return [w.strip() for w in words if len(w.strip()) >= 2]


def calculate_score_delta(star_count: int, thumbs_down_count: int) -> float:
    """⭐と👎の数から興味スコア変化量を計算。正=興味増、負=興味減。"""
    return float(star_count - thumbs_down_count * 1.5)


def update_interests(profile: dict, keyword_scores: dict) -> dict:
    """keyword_scores に基づいて interests を更新。"""
    HIGH_THRESHOLD = 1.5
    LOW_THRESHOLD = -1.0

    all_high = set(profile["interests"]["high"])
    all_medium = set(profile["interests"]["medium"])
    all_low = set(profile["interests"]["low"])

    for keyword, score in keyword_scores.items():
        # 既存カテゴリから除外してから再分類
        all_high.discard(keyword)
        all_medium.discard(keyword)
        all_low.discard(keyword)

        if score >= HIGH_THRESHOLD:
            all_high.add(keyword)
            log(f"  → {keyword}: high (score={score:.1f})")
        elif score <= LOW_THRESHOLD:
            all_low.add(keyword)
            log(f"  → {keyword}: low (score={score:.1f})")
        else:
            all_medium.add(keyword)
            log(f"  → {keyword}: medium (score={score:.1f})")

    profile["interests"]["high"] = sorted(all_high)
    profile["interests"]["medium"] = sorted(all_medium)
    profile["interests"]["low"] = sorted(all_low)
    return profile


def main():
    parser = argparse.ArgumentParser(description="月次Discordリアクション集計 → genai_user_profile.yaml更新")
    parser.add_argument("--month", help="集計月 (YYYY-MM)。デフォルト: 先月")
    parser.add_argument("--dry-run", action="store_true", help="更新内容を表示するだけで書き込まない")
    args = parser.parse_args()

    target_month = get_target_month(args.month)
    log(f"集計対象月: {target_month}")

    # フィードバックYAML読み込み
    if not FEEDBACK_FILE.exists():
        log("フィードバックファイルが存在しません。集計スキップ。")
        sys.exit(0)

    feedback_text = FEEDBACK_FILE.read_text(encoding="utf-8")
    entries = parse_feedback_yaml(feedback_text)
    log(f"フィードバック総件数: {len(entries)}")

    # 対象月のエントリを絞り込み
    target_entries = [
        e for e in entries
        if e.get("timestamp", "").startswith(target_month)
        and e.get("action") == "add"
        and e.get("emoji") in ("⭐", "👎")
    ]
    log(f"対象月エントリ数: {len(target_entries)} (⭐+👎のみ、addのみ)")

    if not target_entries:
        log("対象月のリアクションデータなし。genai_user_profile.yaml は更新しません。")
        sys.exit(0)

    # タイトル別集計
    title_reactions: dict[str, dict] = defaultdict(lambda: {"star": 0, "down": 0})
    for entry in target_entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        emoji = entry.get("emoji", "")
        if emoji == "⭐":
            title_reactions[title]["star"] += 1
        elif emoji == "👎":
            title_reactions[title]["down"] += 1

    log(f"リアクション付き記事数: {len(title_reactions)}")

    # キーワードスコア計算
    keyword_scores: dict[str, float] = defaultdict(float)
    keyword_counts: dict[str, int] = defaultdict(int)
    for title, counts in title_reactions.items():
        delta = calculate_score_delta(counts["star"], counts["down"])
        keywords = extract_keywords_from_title(title)
        for kw in keywords:
            keyword_scores[kw] += delta
            keyword_counts[kw] += 1

    # 2件以上に出現したキーワードのみ対象（ノイズ除去）
    significant_keywords = {
        kw: score for kw, score in keyword_scores.items()
        if keyword_counts[kw] >= 2
    }
    log(f"有意キーワード数 (2件以上): {len(significant_keywords)}")

    if not significant_keywords:
        log("有意なキーワードなし。genai_user_profile.yaml は更新しません。")
        sys.exit(0)

    # プロファイル読み込み
    if not PROFILE_FILE.exists():
        log(f"プロファイルファイルが見つかりません: {PROFILE_FILE}")
        sys.exit(1)

    profile_text = PROFILE_FILE.read_text(encoding="utf-8")
    profile = parse_profile_yaml(profile_text)

    log("現在のinterests:")
    for level in ("high", "medium", "low"):
        log(f"  {level}: {profile['interests'][level]}")

    log("\nキーワードスコア（有意のみ）:")
    for kw, score in sorted(significant_keywords.items(), key=lambda x: -x[1]):
        log(f"  {kw}: {score:+.1f} ({keyword_counts[kw]}件)")

    # interests更新
    updated_profile = update_interests(profile, significant_keywords)

    log("\n更新後のinterests:")
    for level in ("high", "medium", "low"):
        log(f"  {level}: {updated_profile['interests'][level]}")

    if args.dry_run:
        log("[dry-run] ファイル書き込みをスキップ")
        sys.exit(0)

    # YAMLファイル更新
    updated_text = serialize_profile(profile_text, updated_profile)
    PROFILE_FILE.write_text(updated_text, encoding="utf-8")
    log(f"genai_user_profile.yaml 更新完了: {PROFILE_FILE}")

    # 集計サマリーをwork/に保存
    summary_dir = PROJECT_ROOT / "work" / "genai_monthly_summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / f"{target_month}_summary.json"
    summary = {
        "month": target_month,
        "total_reactions": len(target_entries),
        "articles_reacted": len(title_reactions),
        "significant_keywords": dict(sorted(significant_keywords.items(), key=lambda x: -x[1])),
        "updated_interests": updated_profile["interests"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"集計サマリー保存: {summary_file}")


if __name__ == "__main__":
    main()
