#!/usr/bin/env python3
"""
generate_dashboard.py — YouTube解析HTMLダッシュボード生成

Usage:
    python3 scripts/generate_dashboard.py [--skip-video-analysis]

出力:
    projects/dozle_kirinuki/analytics/dashboard/data.json
    projects/dozle_kirinuki/analytics/dashboard/index.html

閲覧:
    cd projects/dozle_kirinuki/analytics/dashboard
    python -m http.server 8080
    # → http://localhost:8080
"""

import json
import math
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build as gapi_build
    _GOOGLE_API_AVAILABLE = True
except ImportError:
    _GOOGLE_API_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
ANALYTICS_DIR = PROJECT_DIR / "analytics"
DASHBOARD_DIR = ANALYTICS_DIR / "dashboard"
ANALYSIS_HISTORY_PATH = ANALYTICS_DIR / "analysis_history.json"
VIDEO_ANALYSIS_PATH = ANALYTICS_DIR / "video_analysis.json"
TOKEN_PATH = PROJECT_DIR / "token.json"
_YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _get_youtube_client():
    """YouTube Data API クライアント取得（token.jsonが存在する場合のみ）"""
    if not _GOOGLE_API_AVAILABLE or not TOKEN_PATH.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), _YOUTUBE_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if creds and creds.valid:
            return gapi_build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"[privacy] YouTube API初期化失敗: {e}", file=sys.stderr)
    return None


def patch_privacy_status_in_raw_jsons() -> None:
    """raw.jsonにprivacy_statusがない動画をYouTube APIで取得して保存"""
    raw_files = sorted(ANALYTICS_DIR.glob("*_raw.json"))
    needs_patch: set[str] = set()
    for f in raw_files:
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            for v in data.get("videos", []):
                if "privacy_status" not in v:
                    needs_patch.add(v["id"])
        except Exception:
            pass

    if not needs_patch:
        return

    print(f"[privacy] {len(needs_patch)}本にprivacy_status未設定。YouTube APIで取得中...")
    youtube = _get_youtube_client()
    if not youtube:
        print("[privacy] YouTube API利用不可。スキップ。", file=sys.stderr)
        return

    privacy_map: dict[str, str] = {}
    ids_list = list(needs_patch)
    for i in range(0, len(ids_list), 50):
        batch = ids_list[i:i+50]
        try:
            res = youtube.videos().list(part="status", id=",".join(batch)).execute()
            for item in res.get("items", []):
                privacy_map[item["id"]] = item["status"]["privacyStatus"]
        except Exception as e:
            print(f"[warn] privacy_status取得失敗 batch{i//50+1}: {e}", file=sys.stderr)
    print(f"[privacy] 取得完了: {len(privacy_map)}本")

    for f in raw_files:
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            modified = False
            for v in data.get("videos", []):
                if "privacy_status" not in v and v["id"] in privacy_map:
                    v["privacy_status"] = privacy_map[v["id"]]
                    modified = True
            if modified:
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, ensure_ascii=False, indent=2)
                print(f"[privacy] {f.name} 更新済み")
        except Exception as e:
            print(f"[warn] {f.name} パッチ失敗: {e}", file=sys.stderr)


def load_all_raw_jsons() -> list[dict]:
    """全raw.jsonを日付順に読み込み"""
    raw_files = sorted(ANALYTICS_DIR.glob("*_raw.json"))
    result = []
    for f in raw_files:
        try:
            with open(f, encoding="utf-8") as fp:
                result.append(json.load(fp))
        except Exception as e:
            print(f"[warn] {f.name} 読み込み失敗: {e}", file=sys.stderr)
    return result


def build_daily_series(raw_list: list[dict]) -> dict:
    """日別時系列データを構築（重複日は最新raw.jsonの値を採用）"""
    all_daily: dict[str, dict] = {}
    subs_history: dict[str, int] = {}
    views_history: dict[str, int] = {}

    for raw in raw_list:
        for day in raw.get("daily_stats", []):
            all_daily[day["date"]] = day
        raw_date = raw.get("date", "")
        ch = raw.get("channel", {})
        if raw_date:
            subs_history[raw_date] = ch.get("subscribers", 0)
            views_history[raw_date] = ch.get("total_views", 0)

    sorted_dates = sorted(all_daily.keys())
    series = {
        "dates": sorted_dates,
        "views": [all_daily[d].get("views", 0) for d in sorted_dates],
        "likes": [all_daily[d].get("likes", 0) for d in sorted_dates],
        "subs_gained": [all_daily[d].get("subs_gained", 0) for d in sorted_dates],
        "watch_minutes": [all_daily[d].get("watch_minutes", 0) for d in sorted_dates],
        "subscribers_cumulative": [],
        "total_views_cumulative": [],
    }

    # 累計登録者・累計再生数（スナップショット日ベース）
    sorted_snap_dates = sorted(subs_history.keys())
    for d in sorted_dates:
        # d以前の最も近いスナップショット値を使う
        subs_val = None
        views_val = None
        for sd in sorted_snap_dates:
            if sd <= d:
                subs_val = subs_history[sd]
                views_val = views_history[sd]
        series["subscribers_cumulative"].append(subs_val)
        series["total_views_cumulative"].append(views_val)

    return series


def build_daily_extended(raw_list: list[dict]) -> dict:
    """日次拡張指標（comments, shares, subs_lost, avg_view_pct, impressions, ctr）
    欠損値は一律 null（API未取得＝null、実値0はint 0）。0埋め禁止。
    """
    all_daily: dict[str, dict] = {}
    all_impressions: dict[str, dict] = {}

    for raw in raw_list:
        for day in raw.get("daily_stats", []):
            all_daily[day["date"]] = day
        for imp in raw.get("impressions_ctr", {}).get("daily", []):
            all_impressions[imp["date"]] = imp

    def _get_or_null(mapping: dict, date: str, key: str):
        """キーが存在すればその値、なければnull。値がNoneもnullとして扱う。"""
        val = mapping.get(date, {}).get(key)
        return val if val is not None else None

    sorted_dates = sorted(all_daily.keys())
    return {
        "dates": sorted_dates,
        "comments": [_get_or_null(all_daily, d, "comments") for d in sorted_dates],
        "shares": [_get_or_null(all_daily, d, "shares") for d in sorted_dates],
        "subs_lost": [_get_or_null(all_daily, d, "subs_lost") for d in sorted_dates],
        "avg_view_pct": [_get_or_null(all_daily, d, "avg_view_pct") for d in sorted_dates],
        "impressions": [_get_or_null(all_impressions, d, "impressions") for d in sorted_dates],
        "ctr": [_get_or_null(all_impressions, d, "ctr") for d in sorted_dates],
    }


def build_content_type(raw_list: list[dict]) -> dict:
    """コンテンツタイプ別（short/longForm）統計"""
    ct = latest_from_raw(raw_list, "content_type_stats", {})
    key_map = {"shorts": "short", "videoOnDemand": "longForm", "liveStream": "live"}
    result = {}
    for api_key, out_key in key_map.items():
        if api_key in ct:
            result[out_key] = {
                "views": ct[api_key].get("views", 0),
                "watch_minutes": ct[api_key].get("watch_minutes", 0),
                "subs_gained": ct[api_key].get("subs_gained", 0),
            }
    # Ensure both keys exist
    for key in ("short", "longForm"):
        if key not in result:
            result[key] = {"views": 0, "watch_minutes": 0, "subs_gained": 0}
    return result


def build_demographics(raw_list: list[dict]) -> dict:
    """視聴者層データ"""
    demo = latest_from_raw(raw_list, "demographics", {})
    return {
        "age": demo.get("age", []),
        "gender": demo.get("gender", {}),
        "country": demo.get("country", []),
        "device": latest_from_raw(raw_list, "device_stats", {}),
    }


def build_retention_top5(raw_list: list[dict]) -> dict:
    """再生数TOP5動画のオーディエンスリテンション"""
    return latest_from_raw(raw_list, "retention_top5", {})


def build_monetization(raw_list: list[dict]) -> dict:
    """YPP収益化条件の達成状況"""
    ct = latest_from_raw(raw_list, "content_type_stats", {})

    shorts_views = ct.get("shorts", {}).get("views", 0)
    longform_watch_min = ct.get("videoOnDemand", {}).get("watch_minutes", 0)
    longform_watch_hours = longform_watch_min / 60

    total_views_90d = sum(
        sum(d.get("views", 0) for d in r.get("daily_stats", []))
        for r in raw_list[-90:] if raw_list
    )
    shorts_pct = round(shorts_views / total_views_90d * 100, 1) if total_views_90d > 0 else 0.0
    longform_pct = round(longform_watch_hours / 4000 * 100, 1) if longform_watch_hours > 0 else 0.0

    return {
        "shorts_path_views_90d": shorts_views,
        "shorts_path_pct": shorts_pct,
        "longform_watch_hours_365d": round(longform_watch_hours, 1),
        "longform_path_pct": longform_pct,
    }


def build_predictions(raw_list: list[dict]) -> dict:
    """将来予測（3ヶ月/6ヶ月後の登録者・再生数）"""
    if len(raw_list) < 7:
        return {"subs_3mo": 0, "views_3mo": 0, "subs_6mo": 0}

    recent = raw_list[-7:]
    ch = recent[-1].get("channel", {})
    current_subs = ch.get("subscribers", 0)
    current_views = ch.get("total_views", 0)

    first_ch = recent[0].get("channel", {})
    first_subs = first_ch.get("subscribers", current_subs)
    first_views = first_ch.get("total_views", current_views)

    daily_sub_rate = max(0, (current_subs - first_subs) / len(recent))
    daily_view_rate = max(0, (current_views - first_views) / len(recent))

    return {
        "subs_3mo": round(current_subs + daily_sub_rate * 90),
        "views_3mo": round(current_views + daily_view_rate * 90),
        "subs_6mo": round(current_subs + daily_sub_rate * 180),
    }


def _strip_handle(title: str) -> str:
    """タイトルから@ハンドル・ハッシュタグ・【】見出しを除去（キャラ検出前処理）"""
    import re as _re
    return _re.sub(r'@\w+|#\w+|【[^】]+】', '', title)


def build_content_analysis(raw_list: list[dict]) -> dict:
    """動画の尺別・キャラ別分析"""
    if not raw_list:
        return {"by_duration": [], "by_character": []}

    latest = raw_list[-1]
    videos = [v for v in latest.get("videos", [])
              if v.get("privacy_status", "public") == "public"]

    # 尺別分析
    duration_buckets = {"short": [], "medium": [], "long": []}
    for v in videos:
        sec = v.get("duration_sec", 0)
        views = v.get("views", 0)
        if sec <= 60:
            duration_buckets["short"].append(views)
        elif sec <= 180:
            duration_buckets["medium"].append(views)
        else:
            duration_buckets["long"].append(views)

    by_duration = []
    for label, view_list in duration_buckets.items():
        if view_list:
            by_duration.append({
                "category": label,
                "count": len(view_list),
                "avg_views": round(sum(view_list) / len(view_list)),
                "total_views": sum(view_list),
            })

    # キャラ別分析（strip_handle + substring match）
    character_patterns = {
        "dozle": ["ドズル", "dozle"],
        "bon": ["ぼんじゅうる", "ぼん"],
        "oo_men": ["おおはらMEN", "おおはら", "MEN"],
        "qnly": ["おんりー", "ONLY"],
        "orafu": ["おらふ", "オラフ"],
        "nekooji": ["ネコおじ", "ねこおじ"],
    }

    by_character = []
    for name, keywords in character_patterns.items():
        char_views = []
        for v in videos:
            clean = _strip_handle(v.get("title", ""))
            # 長いキーワードを先にチェック（部分一致優先度制御）
            if any(kw in clean for kw in keywords):
                char_views.append(v.get("views", 0))
        if char_views:
            by_character.append({
                "character": name,
                "count": len(char_views),
                "avg_views": round(sum(char_views) / len(char_views)),
                "total_views": sum(char_views),
            })

    return {"by_duration": by_duration, "by_character": by_character}


def latest_from_raw(raw_list: list[dict], key: str, default=None):
    """raw_listの末尾から指定キーの値を取得"""
    for raw in reversed(raw_list):
        val = raw.get(key)
        if val:
            return val
    return default if default is not None else {}


def build_video_table(latest_raw: dict, prev_raw: dict | None) -> list[dict]:
    """動画テーブルデータ構築（前日比・like_rate・loop_rate・avg_view_pct付き）"""
    videos = latest_raw.get("videos", [])

    pva_map = {v["id"]: v for v in latest_raw.get("per_video_analytics", [])}
    prev_map = {}
    if prev_raw:
        prev_map = {v["id"]: v.get("views", 0) for v in prev_raw.get("videos", [])}

    result = []
    for v in videos:
        pva = pva_map.get(v["id"], {})
        views = v.get("views", 0)
        likes = v.get("likes", 0)
        duration_sec = v.get("duration_sec", 0)
        pub = v.get("published_at", "")
        if pub and len(pub) >= 10:
            pub = pub[:10]  # YYYY-MM-DD

        prev_views = prev_map.get(v["id"], views) if prev_raw else None
        view_diff_1d = views - prev_views if prev_raw else None
        view_growth_rate = (
            round(view_diff_1d / prev_views * 100, 2)
            if prev_raw and prev_views and prev_views > 0 and view_diff_1d is not None
            else None
        )
        entry = {
            "id": v["id"],
            "title": v.get("title", ""),
            "views": views,
            "likes": likes,
            "comments": v.get("comments", 0),
            "like_rate": round(likes / views * 100, 2) if views > 0 else 0,
            "duration_sec": duration_sec,
            "duration_str": v.get("duration_str", ""),
            "is_short": duration_sec <= 180,
            "published_at": pub,
            "loop_rate": pva.get("loop_rate"),
            "avg_view_pct": pva.get("avg_view_pct"),
            "view_diff_1d": view_diff_1d,
            "view_growth_rate": view_growth_rate,
        }
        result.append(entry)

    return result


def build_video_history(raw_list: list[dict]) -> dict:
    """全raw.jsonから動画別時系列データを構築"""
    history: dict[str, dict] = {}

    for raw in raw_list:
        raw_date = raw.get("date", "")
        if not raw_date:
            continue

        video_map = {v["id"]: v for v in raw.get("videos", [])}
        pva_map = {v["id"]: v for v in raw.get("per_video_analytics", [])}

        for vid, v in video_map.items():
            if vid not in history:
                history[vid] = {
                    "dates": [], "views": [], "likes": [],
                    "view_diffs": [], "like_rates": [],
                    "loop_rates": [], "avg_view_pcts": [],
                }
            h = history[vid]
            views = v.get("views", 0)
            likes = v.get("likes", 0)

            prev_views = h["views"][-1] if h["views"] else None
            view_diff = views - prev_views if prev_views is not None else None

            pva = pva_map.get(vid, {})

            h["dates"].append(raw_date)
            h["views"].append(views)
            h["likes"].append(likes)
            h["view_diffs"].append(view_diff)
            h["like_rates"].append(round(likes / views * 100, 2) if views > 0 else 0)
            h["loop_rates"].append(pva.get("loop_rate"))
            h["avg_view_pcts"].append(pva.get("avg_view_pct"))

    return history


def build_similar_videos(videos: list[dict]) -> dict:
    """動画別類似動画マッピングを事前計算（上位5本）"""
    result = {}
    for target in videos:
        candidates = [v for v in videos if v["id"] != target["id"]]
        scores = []
        for c in candidates:
            score = 0.0
            if target["views"] > 0 and c["views"] > 0:
                log_ratio = abs(math.log10(c["views"]) - math.log10(target["views"]))
                score += max(0.0, 1.0 - log_ratio)
            tr = target.get("like_rate", 0) or 0
            cr = c.get("like_rate", 0) or 0
            score += max(0.0, 1.0 - abs(tr - cr) / 5)
            td = target.get("duration_sec", 30) or 30
            cd = c.get("duration_sec", 30) or 30
            score += max(0.0, 1.0 - abs(td - cd) / 60)
            if target.get("is_short") == c.get("is_short"):
                score += 0.5
            scores.append((score, c["id"]))
        scores.sort(reverse=True)
        result[target["id"]] = [vid for _, vid in scores[:5]]
    return result


def build_rankings(videos: list[dict]) -> dict:
    """6ランキングをTOP10で構築"""
    def top10(key: str) -> list[dict]:
        valid = [v for v in videos if v.get(key) is not None]
        sorted_v = sorted(valid, key=lambda v: v[key] or 0, reverse=True)[:10]
        return [{"id": v["id"], "title": v["title"], "value": v[key]} for v in sorted_v]

    return {
        "views": top10("views"),
        "like_rate": top10("like_rate"),
        "avg_view_pct": top10("avg_view_pct"),
        "loop_rate": top10("loop_rate"),
        "comments": top10("comments"),
        "view_growth_rate": top10("view_growth_rate"),
    }


def load_video_analysis() -> dict:
    """動画別LLM分析読み込み"""
    if not VIDEO_ANALYSIS_PATH.exists():
        return {}
    try:
        with open(VIDEO_ANALYSIS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[warn] video_analysis.json 読み込み失敗: {e}", file=sys.stderr)
        return {}


def save_video_analysis(analysis: dict) -> None:
    """動画別LLM分析保存"""
    try:
        with open(VIDEO_ANALYSIS_PATH, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[warn] video_analysis.json 保存失敗: {e}", file=sys.stderr)


def analyze_top_videos(videos: list[dict], n: int = 5) -> None:
    """再生数上位N本 + 前日比上位3本をClaude CLIで個別分析し保存"""
    targets: set[str] = set()
    by_views = sorted(videos, key=lambda v: v["views"], reverse=True)
    for v in by_views[:n]:
        targets.add(v["id"])
    by_growth = sorted(videos, key=lambda v: v.get("view_diff_1d") or 0, reverse=True)
    for v in by_growth[:3]:
        if v.get("view_diff_1d", 0) and v["view_diff_1d"] > 0:
            targets.add(v["id"])

    existing = load_video_analysis()
    today = datetime.now().strftime("%Y-%m-%d")
    for vid in list(targets):
        if vid in existing:
            if any(a["date"] == today for a in existing[vid].get("analyses", [])):
                targets.discard(vid)

    video_map = {v["id"]: v for v in videos}
    for vid in targets:
        v = video_map.get(vid)
        if not v:
            continue
        prompt = (
            f"以下のYouTubeショート動画のパフォーマンスを分析してください。\n\n"
            f"タイトル: {v['title']}\n"
            f"再生数: {v['views']:,}\n"
            f"いいね: {v['likes']}\n"
            f"Like率: {v.get('like_rate', 0):.1f}%\n"
            f"周回率: {v.get('loop_rate', 'N/A')}\n"
            f"視聴率: {v.get('avg_view_pct', 'N/A')}%\n"
            f"公開日: {v['published_at']}\n"
            f"尺: {v['duration_str']}\n\n"
            f"分析観点:\n"
            f"1. なぜこの動画は伸びた/伸びなかったか\n"
            f"2. タイトル・サムネイル（タイトルから推測）の効果\n"
            f"3. 改善すべき点\n"
        )
        print(f"[analyze] {vid}: {v['title'][:30]}...", file=sys.stderr)
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "claude-opus-4-6"],
                capture_output=True, text=True, timeout=60
            )
            content = result.stdout.strip()
            if not content:
                print(f"[warn] {vid}: 分析結果なし", file=sys.stderr)
                continue
        except Exception as e:
            print(f"[warn] {vid}: 分析失敗: {e}", file=sys.stderr)
            continue

        if vid not in existing:
            existing[vid] = {"title": v["title"], "analyses": []}
        existing[vid]["analyses"].append({
            "date": today,
            "model": "claude-opus-4-6",
            "content": content,
        })

    if targets:
        save_video_analysis(existing)


def load_analysis_history() -> list[dict]:
    """LLM分析履歴読み込み"""
    if not ANALYSIS_HISTORY_PATH.exists():
        return []
    try:
        with open(ANALYSIS_HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[warn] analysis_history.json 読み込み失敗: {e}", file=sys.stderr)
        return []


def generate_data_json(raw_list: list[dict], analysis: list[dict]) -> dict:
    """data.json用データ構築"""
    if not raw_list:
        print("[error] raw.jsonが見つかりません", file=sys.stderr)
        return {}

    latest_raw = raw_list[-1]
    prev_raw = raw_list[-2] if len(raw_list) >= 2 else None

    # 非公開・限定公開動画を除外（privacy_status=private or unlisted）
    _EXCLUDED_STATUSES = {"private", "unlisted"}

    def _filter_private(raw: dict) -> dict:
        """raw.jsonのvideos/per_video_analyticsから非公開/限定公開動画を除外したコピーを返す"""
        import copy
        r = copy.copy(raw)
        r["videos"] = [v for v in raw.get("videos", []) if v.get("privacy_status", "public") not in _EXCLUDED_STATUSES]
        excluded_ids = {v["id"] for v in raw.get("videos", []) if v.get("privacy_status", "public") in _EXCLUDED_STATUSES}
        r["per_video_analytics"] = [p for p in raw.get("per_video_analytics", []) if p.get("id") not in excluded_ids]
        return r

    latest_raw_filtered = _filter_private(latest_raw)
    prev_raw_filtered = _filter_private(prev_raw) if prev_raw else None
    raw_list_filtered = [_filter_private(r) for r in raw_list]

    private_count = len(latest_raw.get("videos", [])) - len(latest_raw_filtered["videos"])
    if private_count > 0:
        print(f"[info] 非公開動画を除外: {private_count}本", file=sys.stderr)

    ch = latest_raw.get("channel", {})
    daily_series = build_daily_series(raw_list_filtered)
    videos = build_video_table(latest_raw_filtered, prev_raw_filtered)
    traffic = latest_raw_filtered.get("traffic_sources", [])

    # 動画個別分析ページ用データ
    video_history = build_video_history(raw_list_filtered)
    similar_videos = build_similar_videos(videos)
    video_analysis = load_video_analysis()
    rankings = build_rankings(videos)

    jst = timezone(timedelta(hours=9))
    generated_at = datetime.now(jst).strftime("%Y-%m-%dT%H:%M:%S")

    # Phase2 拡張データ
    daily_extended = build_daily_extended(raw_list_filtered)
    content_type = build_content_type(raw_list_filtered)
    demographics = build_demographics(raw_list_filtered)
    retention_top5 = build_retention_top5(raw_list_filtered)
    monetization = build_monetization(raw_list_filtered)
    predictions = build_predictions(raw_list_filtered)
    content_analysis = build_content_analysis(raw_list_filtered)

    return {
        "generated_at": generated_at,
        "channel": {
            "name": ch.get("name", ""),
            "subscribers": ch.get("subscribers", 0),
            "total_views": ch.get("total_views", 0),
            "video_count": ch.get("video_count", 0),
        },
        "daily_series": daily_series,
        "daily_extended": daily_extended,
        "content_type": content_type,
        "demographics": demographics,
        "retention_top5": retention_top5,
        "monetization": monetization,
        "predictions": predictions,
        "content_analysis": content_analysis,
        "traffic_sources": traffic,
        "videos": videos,
        "analysis_history": analysis,
        "video_history": video_history,
        "similar_videos": similar_videos,
        "video_analysis": video_analysis,
        "rankings": rankings,
    }


def generate_html() -> str:
    """index.html生成（Chart.js CDN + インラインCSS/JS）"""
    return '''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>毎日ドズル社切り抜き Analytics</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <style>
    :root { --bg: #1a1a2e; --card: #16213e; --text: #e0e0e0; --accent: #e94560; --accent2: #0f3460; }
    * { box-sizing: border-box; }
    body { background: var(--bg); color: var(--text); font-family: \'Hiragino Kaku Gothic Pro\', \'Yu Gothic\', sans-serif; margin: 0; padding: 20px; }
    h1 { color: var(--accent); margin: 0 0 4px; }
    h2 { color: #aaa; font-size: 1.1em; margin: 0 0 12px; }
    #last-updated { color: #888; font-size: 0.85em; margin-bottom: 20px; }
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
    @media (max-width: 800px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
    .kpi-card { background: var(--card); padding: 20px; border-radius: 8px; text-align: center; }
    .kpi-label { font-size: 0.85em; color: #888; margin-bottom: 8px; }
    .kpi-value { font-size: 2em; font-weight: bold; color: var(--accent); }
    .kpi-sub { font-size: 0.8em; color: #666; margin-top: 4px; }
    .card { background: var(--card); border-radius: 8px; padding: 20px; margin-bottom: 20px; }
    .tab-btns { margin-bottom: 12px; }
    .tab-btn { background: #333; color: var(--text); border: none; padding: 6px 14px; border-radius: 4px; cursor: pointer; margin-right: 6px; font-size: 0.9em; }
    .tab-btn.active { background: var(--accent); }
    canvas { max-height: 300px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88em; }
    th, td { padding: 7px 10px; text-align: left; border-bottom: 1px solid #2a2a4a; white-space: nowrap; }
    th { cursor: pointer; color: #aaa; background: #0f1a2e; position: sticky; top: 0; }
    th:hover { color: var(--accent); }
    tr:hover td { background: #1f2f4f; }
    .badge-short { background: #e94560; color: white; border-radius: 3px; padding: 1px 5px; font-size: 0.75em; margin-left: 4px; }
    .badge-hl { background: #0f3460; color: white; border-radius: 3px; padding: 1px 5px; font-size: 0.75em; margin-left: 4px; }
    .analysis-entry { background: #0f1a2e; margin: 8px 0; border-radius: 6px; border: 1px solid #2a2a4a; }
    .analysis-header { padding: 12px 16px; cursor: pointer; display: flex; justify-content: space-between; }
    .analysis-header:hover { background: #1a2a4a; border-radius: 6px 6px 0 0; }
    .analysis-body { padding: 0 16px 12px; display: none; white-space: pre-wrap; font-size: 0.88em; line-height: 1.6; color: #ccc; }
    .analysis-body.open { display: block; }
    .sort-arrow { font-size: 0.7em; color: #888; }
    .table-wrap { overflow-x: auto; }
    .pos { color: #4caf50; }
    .neg { color: #e94560; }
    .loop-badge { color: #f9a825; font-size: 0.85em; }
    #no-data { color: #888; padding: 20px; text-align: center; }
    /* 個別ページ */
    #detail-view { display: none; }
    .back-btn { background: #333; color: var(--text); border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 0.95em; margin-bottom: 16px; }
    .back-btn:hover { background: #444; }
    .detail-meta { color: #888; font-size: 0.9em; margin-bottom: 16px; }
    .detail-meta a { color: #aaa; }
    .detail-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
    @media (max-width: 800px) { .detail-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
    .detail-title { font-size: 1.3em; font-weight: bold; color: var(--text); margin-bottom: 6px; word-break: break-all; white-space: normal; }
    .similar-row { cursor: pointer; }
    .similar-row:hover td { background: #1f2f4f; }
    /* ランキング */
    .ranking-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    @media (max-width: 900px) { .ranking-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 600px) { .ranking-grid { grid-template-columns: 1fr; } }
    .ranking-card { background: #0f1a2e; border-radius: 6px; padding: 12px; }
    .ranking-title { font-weight: bold; color: var(--accent); margin-bottom: 8px; font-size: 0.9em; }
    .ranking-item { display: flex; align-items: center; padding: 4px 0; border-bottom: 1px solid #2a2a4a; font-size: 0.82em; cursor: pointer; }
    .ranking-item:hover { background: #1a2a4a; border-radius: 3px; }
    .ranking-num { color: #888; width: 22px; flex-shrink: 0; text-align: right; margin-right: 6px; }
    .ranking-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #ccc; margin-right: 6px; }
    .ranking-val { color: var(--accent); font-weight: bold; flex-shrink: 0; }
  </style>
</head>
<body>

  <!-- ダッシュボード一覧ビュー -->
  <div id="dashboard-view">
    <h1>毎日ドズル社切り抜き Analytics</h1>
    <p id="last-updated">読み込み中...</p>

    <div class="kpi-grid" id="kpi-cards">
      <div class="kpi-card"><div class="kpi-label">登録者</div><div class="kpi-value" id="kpi-subs">-</div></div>
      <div class="kpi-card"><div class="kpi-label">総再生数</div><div class="kpi-value" id="kpi-views">-</div></div>
      <div class="kpi-card"><div class="kpi-label">動画数</div><div class="kpi-value" id="kpi-vcount">-</div></div>
      <div class="kpi-card"><div class="kpi-label">前日再生増</div><div class="kpi-value" id="kpi-growth">-</div><div class="kpi-sub" id="kpi-growth-date"></div></div>
    </div>

    <div class="card">
      <h2>日次推移</h2>
      <div class="tab-btns">
        <button class="tab-btn active" onclick="showChart(\'views\', this)">再生数</button>
        <button class="tab-btn" onclick="showChart(\'subs\', this)">登録者</button>
        <button class="tab-btn" onclick="showChart(\'likes\', this)">いいね</button>
        <button class="tab-btn" onclick="showChart(\'growth\', this)">登録増</button>
      </div>
      <canvas id="dailyChart"></canvas>
    </div>

    <div class="card">
      <h2>トラフィックソース（直近14日）</h2>
      <canvas id="trafficChart" style="max-height:280px; max-width:500px;"></canvas>
    </div>

    <div class="card">
      <h2>動画別パフォーマンス</h2>
      <div class="table-wrap">
        <table id="video-table">
          <thead>
            <tr>
              <th onclick="sortTable(\'title\')">タイトル</th>
              <th onclick="sortTable(\'views\')">再生数 <span class="sort-arrow" id="sort-arrow-views">↓</span></th>
              <th onclick="sortTable(\'likes\')">いいね</th>
              <th onclick="sortTable(\'like_rate\')">Like率%</th>
              <th onclick="sortTable(\'loop_rate\')">周回率</th>
              <th onclick="sortTable(\'avg_view_pct\')">視聴率%</th>
              <th onclick="sortTable(\'view_diff_1d\')">前日比</th>
              <th>尺</th>
              <th onclick="sortTable(\'published_at\')">公開日</th>
            </tr>
          </thead>
          <tbody id="video-tbody"></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h2>ランキング TOP10</h2>
      <div class="ranking-grid">
        <div class="ranking-card">
          <div class="ranking-title">&#x1F441; 再生数</div>
          <div id="rank-views"></div>
        </div>
        <div class="ranking-card">
          <div class="ranking-title">&#x1F44D; Like率%</div>
          <div id="rank-like-rate"></div>
        </div>
        <div class="ranking-card">
          <div class="ranking-title">&#x1F4FA; 視聴率%</div>
          <div id="rank-avg-view-pct"></div>
        </div>
        <div class="ranking-card">
          <div class="ranking-title">&#x1F501; 周回率</div>
          <div id="rank-loop-rate"></div>
        </div>
        <div class="ranking-card">
          <div class="ranking-title">&#x1F4AC; コメント数</div>
          <div id="rank-comments"></div>
        </div>
        <div class="ranking-card">
          <div class="ranking-title">&#x1F4C8; 伸び率%</div>
          <div id="rank-growth-rate"></div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>AI分析コメント</h2>
      <div id="analysis-list"><p id="no-data" style="display:none">分析コメントなし</p></div>
    </div>
  </div>

  <!-- 動画個別詳細ビュー -->
  <div id="detail-view">
    <button class="back-btn" onclick="location.hash=\'\'">← 一覧に戻る</button>
    <div id="detail-content"></div>
  </div>

<script>
let data = null;
let currentSort = { key: \'views\', dir: -1 };
let dailyChartInstance = null;
let detailChartInstances = [];

const fmt = n => n == null ? \'-\' : n.toLocaleString();
const fmtPct = n => n == null ? \'-\' : n.toFixed(1) + \'%\';
const fmtRate = n => n == null ? \'-\' : n.toFixed(3);

// ── ルーティング ──────────────────────────────────────
window.addEventListener(\'hashchange\', route);
window.addEventListener(\'load\', route);

function route() {
  const hash = location.hash;
  const match = hash.match(/^#video=(.+)$/);
  if (match) {
    showVideoDetail(decodeURIComponent(match[1]));
  } else {
    showDashboard();
  }
}

function showDashboard() {
  document.getElementById(\'dashboard-view\').style.display = \'block\';
  document.getElementById(\'detail-view\').style.display = \'none\';
  // チャートを再描画（非表示中に破棄される場合がある）
  if (data && !dailyChartInstance) {
    showChart(\'views\', document.querySelector(\'.tab-btn.active\'));
  }
}

function showVideoDetail(videoId) {
  document.getElementById(\'dashboard-view\').style.display = \'none\';
  document.getElementById(\'detail-view\').style.display = \'block\';
  if (data) renderVideoDetail(videoId);
}

// ── 個別ページレンダリング ────────────────────────────
function renderVideoDetail(videoId) {
  // 既存チャート破棄
  detailChartInstances.forEach(c => c.destroy());
  detailChartInstances = [];

  const v = data.videos.find(x => x.id === videoId);
  if (!v) {
    document.getElementById(\'detail-content\').innerHTML = \'<p style="color:#888">動画が見つかりません: \' + videoId + \'</p>\';
    return;
  }

  const badge = v.is_short ? \'<span class="badge-short">SHORT</span>\' : \'<span class="badge-hl">HL</span>\';
  const loopBadge = (v.loop_rate != null && v.loop_rate >= 1.0) ? \' <span class="loop-badge">🔁</span>\' : \'\';
  const ytUrl = \'https://youtube.com/watch?v=\' + videoId;

  const html = `
    <div class="detail-title">${escHtml(v.title)}${badge}</div>
    <div class="detail-meta">
      公開日: ${v.published_at || \'-\'} &nbsp;|&nbsp; 尺: ${v.duration_str || \'-\'}
      &nbsp;|&nbsp; <a href="${ytUrl}" target="_blank">YouTubeで見る ↗</a>
    </div>

    <div class="detail-kpi-grid">
      <div class="kpi-card"><div class="kpi-label">再生数</div><div class="kpi-value">${fmt(v.views)}</div></div>
      <div class="kpi-card"><div class="kpi-label">いいね</div><div class="kpi-value">${fmt(v.likes)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Like率</div><div class="kpi-value">${fmtPct(v.like_rate)}</div></div>
      <div class="kpi-card"><div class="kpi-label">周回率${loopBadge}</div><div class="kpi-value">${fmtRate(v.loop_rate)}</div></div>
    </div>

    <div class="card">
      <h2>日次再生数推移</h2>
      <canvas id="detail-views-chart"></canvas>
    </div>

    <div class="card">
      <h2>メトリクス推移（Like率 / 視聴率% / 周回率）</h2>
      <canvas id="detail-metrics-chart"></canvas>
    </div>

    <div class="card">
      <h2>類似動画</h2>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>タイトル</th>
            <th>再生数</th>
            <th>Like率%</th>
            <th>周回率</th>
            <th>尺</th>
            <th>公開日</th>
          </tr></thead>
          <tbody id="similar-tbody"></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h2>AI動画分析</h2>
      <div id="video-analysis-list"></div>
    </div>
  `;
  document.getElementById(\'detail-content\').innerHTML = html;

  // 日次再生数グラフ
  const hist = (data.video_history || {})[videoId];
  if (hist && hist.dates.length > 0) {
    const labels = hist.dates.map(d => d.slice(5));
    const ctx1 = document.getElementById(\'detail-views-chart\');
    detailChartInstances.push(new Chart(ctx1, {
      type: \'bar\',
      data: {
        labels,
        datasets: [{
          label: \'累計再生数\',
          data: hist.views,
          backgroundColor: \'rgba(233,69,96,0.6)\',
          borderColor: \'#e94560\',
          borderWidth: 1,
        }, {
          label: \'日次増加\',
          data: hist.view_diffs,
          type: \'line\',
          borderColor: \'#f9a825\',
          backgroundColor: \'transparent\',
          yAxisID: \'y2\',
          tension: 0.3,
          pointRadius: 3,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: \'#ccc\' } } },
        scales: {
          x: { ticks: { color: \'#888\' }, grid: { color: \'#2a2a4a\' } },
          y: { ticks: { color: \'#888\' }, grid: { color: \'#2a2a4a\' }, title: { display: true, text: \'累計\', color: \'#888\' } },
          y2: { position: \'right\', ticks: { color: \'#888\' }, grid: { drawOnChartArea: false }, title: { display: true, text: \'日次増加\', color: \'#888\' } }
        }
      }
    }));

    // メトリクス推移グラフ
    const ctx2 = document.getElementById(\'detail-metrics-chart\');
    detailChartInstances.push(new Chart(ctx2, {
      type: \'line\',
      data: {
        labels,
        datasets: [{
          label: \'Like率%\',
          data: hist.like_rates,
          borderColor: \'#e94560\',
          backgroundColor: \'transparent\',
          tension: 0.3,
          yAxisID: \'yL\',
        }, {
          label: \'視聴率%\',
          data: hist.avg_view_pcts,
          borderColor: \'#2196f3\',
          backgroundColor: \'transparent\',
          tension: 0.3,
          yAxisID: \'yL\',
        }, {
          label: \'周回率\',
          data: hist.loop_rates,
          borderColor: \'#f9a825\',
          backgroundColor: \'transparent\',
          tension: 0.3,
          yAxisID: \'yR\',
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: \'#ccc\' } } },
        scales: {
          x: { ticks: { color: \'#888\' }, grid: { color: \'#2a2a4a\' } },
          yL: { ticks: { color: \'#888\' }, grid: { color: \'#2a2a4a\' }, title: { display: true, text: \'%\', color: \'#888\' } },
          yR: { position: \'right\', ticks: { color: \'#888\' }, grid: { drawOnChartArea: false }, title: { display: true, text: \'周回率\', color: \'#888\' } }
        }
      }
    }));
  } else {
    document.getElementById(\'detail-views-chart\').parentElement.innerHTML += \'<p style="color:#888;font-size:0.85em">時系列データなし（raw.json蓄積待ち）</p>\';
  }

  // 類似動画テーブル
  const similarIds = (data.similar_videos || {})[videoId] || [];
  const videoMap = {};
  data.videos.forEach(x => { videoMap[x.id] = x; });
  const similarTbody = document.getElementById(\'similar-tbody\');
  if (similarIds.length) {
    similarTbody.innerHTML = similarIds.map(sid => {
      const sv = videoMap[sid];
      if (!sv) return \'\';
      const sb = sv.is_short ? \'<span class="badge-short">SHORT</span>\' : \'<span class="badge-hl">HL</span>\';
      const st = sv.title.replace(/【.*?】/g, \'\').replace(/@.*$/,\'\').trim();
      return `<tr class="similar-row" onclick="location.hash=\'#video=${sv.id}\'">
        <td><span style="color:#aaa">${escHtml(st)}</span>${sb}</td>
        <td>${fmt(sv.views)}</td>
        <td>${fmtPct(sv.like_rate)}</td>
        <td>${fmtRate(sv.loop_rate)}</td>
        <td>${sv.duration_str || \'-\'}</td>
        <td>${sv.published_at || \'-\'}</td>
      </tr>`;
    }).join(\'\');
  } else {
    similarTbody.innerHTML = \'<tr><td colspan="6" style="color:#888">類似動画なし</td></tr>\';
  }

  // AI動画個別分析
  const analysisList = document.getElementById(\'video-analysis-list\');
  const vaEntry = (data.video_analysis || {})[videoId];
  if (vaEntry && vaEntry.analyses && vaEntry.analyses.length) {
    analysisList.innerHTML = vaEntry.analyses.slice().reverse().map((a, i) => {
      const isFirst = i === 0;
      return `<div class="analysis-entry">
        <div class="analysis-header" onclick="toggleVA(\'va_\'+${i})">
          <span>${a.date} ${a.model ? \'(\' + a.model + \')\' : \'\'}</span>
          <span id="va_arrow_${i}">${isFirst ? \'▼\' : \'▶\'}</span>
        </div>
        <div class="analysis-body ${isFirst ? \'open\' : \'\'}" id="va_${i}">${escHtml(a.content)}</div>
      </div>`;
    }).join(\'\');
  } else {
    analysisList.innerHTML = \'<p style="color:#888">この動画のAI分析なし（--skip-video-analysisを外して再実行すると上位動画が分析されます）</p>\';
  }
}

function toggleVA(id) {
  const body = document.getElementById(id);
  const i = id.replace(\'va_\', \'\');
  const arrow = document.getElementById(\'va_arrow_\' + i);
  if (!body || !arrow) return;
  body.classList.toggle(\'open\');
  arrow.textContent = body.classList.contains(\'open\') ? \'▼\' : \'▶\';
}

function escHtml(str) {
  return str.replace(/&/g,\'&amp;\').replace(/</g,\'&lt;\').replace(/>/g,\'&gt;\').replace(/"/g,\'&quot;\');
}

function renderRankings() {
  if (!data || !data.rankings) return;
  const r = data.rankings;
  const fmtRankVal = (key, val) => {
    if (val == null) return \'-\';
    if (key === \'views\' || key === \'comments\') return val.toLocaleString();
    if (key === \'like_rate\' || key === \'avg_view_pct\' || key === \'view_growth_rate\') return val.toFixed(1) + \'%\';
    return val.toFixed(3);
  };
  const renderRank = (id, key, items) => {
    const el = document.getElementById(id);
    if (!el || !items) return;
    el.innerHTML = items.map((item, i) => {
      const medal = i === 0 ? \'&#x1F947;\' : i === 1 ? \'&#x1F948;\' : i === 2 ? \'&#x1F949;\' : (i + 1) + \'\';
      const short = escHtml(item.title.replace(/\\u300a.*?\\u300b/g, \'\').replace(/【.*?】/g, \'\').replace(/@.*$/, \'\').trim().slice(0, 18));
      return \'<div class="ranking-item" onclick="location.hash=\\\'#video=\' + item.id + \'\\\'">\' +
        \'<span class="ranking-num">\' + medal + \'</span>\' +
        \'<span class="ranking-name">\' + short + \'</span>\' +
        \'<span class="ranking-val">\' + fmtRankVal(key, item.value) + \'</span>\' +
        \'</div>\';
    }).join(\'\');
  };
  renderRank(\'rank-views\', \'views\', r.views);
  renderRank(\'rank-like-rate\', \'like_rate\', r.like_rate);
  renderRank(\'rank-avg-view-pct\', \'avg_view_pct\', r.avg_view_pct);
  renderRank(\'rank-loop-rate\', \'loop_rate\', r.loop_rate);
  renderRank(\'rank-comments\', \'comments\', r.comments);
  renderRank(\'rank-growth-rate\', \'view_growth_rate\', r.view_growth_rate);
}

// ── ダッシュボード（既存機能） ─────────────────────────
const metricConfig = {
  views:  { label: \'日別再生数\', key: \'views\',       type: \'bar\' },
  subs:   { label: \'累計登録者\', key: \'subscribers_cumulative\', type: \'line\' },
  likes:  { label: \'日別いいね\', key: \'likes\',       type: \'bar\' },
  growth: { label: \'日別登録増\', key: \'subs_gained\', type: \'bar\' },
};

function showChart(metric, btn) {
  document.querySelectorAll(\'#dashboard-view .tab-btn\').forEach(b => b.classList.remove(\'active\'));
  if (btn) btn.classList.add(\'active\');
  if (!data) return;

  const cfg = metricConfig[metric];
  const labels = data.daily_series.dates.map(d => d.slice(5));
  const values = data.daily_series[cfg.key];

  if (dailyChartInstance) { dailyChartInstance.destroy(); dailyChartInstance = null; }

  const datasets = [{
    label: cfg.label,
    data: values,
    backgroundColor: \'rgba(233,69,96,0.6)\',
    borderColor: \'#e94560\',
    borderWidth: 1,
    fill: cfg.type === \'line\',
    tension: 0.3,
  }];

  if (metric === \'views\') {
    const ma7 = values.map((_, i) => {
      const slice = values.slice(Math.max(0, i-6), i+1);
      return Math.round(slice.reduce((a,b) => a+(b||0), 0) / slice.length);
    });
    datasets.push({
      label: \'7日移動平均\',
      data: ma7,
      type: \'line\',
      borderColor: \'#f9a825\',
      backgroundColor: \'transparent\',
      pointRadius: 0,
      borderWidth: 2,
      tension: 0.3,
    });
  }

  dailyChartInstance = new Chart(document.getElementById(\'dailyChart\'), {
    type: cfg.type,
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: \'#ccc\' } } },
      scales: {
        x: { ticks: { color: \'#888\' }, grid: { color: \'#2a2a4a\' } },
        y: { beginAtZero: metric !== \'subs\', ticks: { color: \'#888\' }, grid: { color: \'#2a2a4a\' } }
      }
    }
  });
}

function renderTraffic() {
  if (!data || !data.traffic_sources.length) return;
  const labels = data.traffic_sources.map(s => s.source + \' (\' + s.pct + \'%)\');
  const values = data.traffic_sources.map(s => s.views);
  const colors = [\'#e94560\',\'#0f3460\',\'#533483\',\'#16aa6e\',\'#f9a825\',\'#2196f3\',\'#ff5722\',\'#9c27b0\',\'#00bcd4\',\'#607d8b\'];
  new Chart(document.getElementById(\'trafficChart\'), {
    type: \'doughnut\',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors.slice(0, values.length) }]
    },
    options: {
      plugins: { legend: { position: \'right\', labels: { color: \'#ccc\', font: { size: 11 } } } }
    }
  });
}

function renderTable(videos) {
  const tbody = document.getElementById(\'video-tbody\');
  tbody.innerHTML = videos.map(v => {
    const badge = v.is_short ? \'<span class="badge-short">SHORT</span>\' : \'<span class="badge-hl">HL</span>\';
    const loopBadge = (v.loop_rate != null && v.loop_rate >= 1.0) ? \' <span class="loop-badge">🔁</span>\' : \'\';
    const diff = v.view_diff_1d;
    const diffStr = diff == null ? \'-\' : (diff >= 0 ? \'<span class="pos">+\' + fmt(diff) + \'</span>\' : \'<span class="neg">\' + fmt(diff) + \'</span>\');
    const shortTitle = v.title.replace(/【.*?】/g, \'\').replace(/@.*$/,\'\').trim();
    const ytUrl = \'https://youtube.com/watch?v=\' + v.id;
    return `<tr>
      <td>
        <a href="#video=${v.id}" style="color:#aaa;text-decoration:none">${escHtml(shortTitle)}</a>${badge}
        <a href="${ytUrl}" target="_blank" style="color:#555;font-size:0.8em;margin-left:4px">↗YT</a>
      </td>
      <td>${fmt(v.views)}</td>
      <td>${fmt(v.likes)}</td>
      <td>${fmtPct(v.like_rate)}</td>
      <td>${fmtRate(v.loop_rate)}${loopBadge}</td>
      <td>${fmtPct(v.avg_view_pct)}</td>
      <td>${diffStr}</td>
      <td>${v.duration_str || \'-\'}</td>
      <td>${v.published_at || \'-\'}</td>
    </tr>`;
  }).join(\'\');
}

function sortTable(key) {
  if (!data) return;
  if (currentSort.key === key) currentSort.dir *= -1;
  else { currentSort.key = key; currentSort.dir = -1; }
  document.querySelectorAll(\'.sort-arrow\').forEach(el => el.textContent = \'\');
  const arrow = document.getElementById(\'sort-arrow-\' + key);
  if (arrow) arrow.textContent = currentSort.dir === -1 ? \'↓\' : \'↑\';
  const sorted = [...data.videos].sort((a, b) => {
    const av = a[key] ?? -Infinity;
    const bv = b[key] ?? -Infinity;
    if (typeof av === \'string\') return av.localeCompare(bv) * currentSort.dir;
    return (av - bv) * currentSort.dir;
  });
  renderTable(sorted);
}

function renderAnalysis() {
  const list = document.getElementById(\'analysis-list\');
  const history = data.analysis_history || [];
  if (!history.length) {
    document.getElementById(\'no-data\').style.display = \'block\';
    return;
  }
  list.innerHTML = history.map((entry, i) => {
    const isFirst = i === 0;
    return `<div class="analysis-entry">
      <div class="analysis-header" onclick="toggleAnalysis(${i})">
        <span>${entry.date} ${entry.model ? \'(\' + entry.model + \')\' : \'\'}</span>
        <span id="arrow-${i}">${isFirst ? \'▼\' : \'▶\'}</span>
      </div>
      <div class="analysis-body ${isFirst ? \'open\' : \'\'}" id="body-${i}">${entry.content}</div>
    </div>`;
  }).join(\'\');
}

function toggleAnalysis(i) {
  const body = document.getElementById(\'body-\' + i);
  const arrow = document.getElementById(\'arrow-\' + i);
  body.classList.toggle(\'open\');
  arrow.textContent = body.classList.contains(\'open\') ? \'▼\' : \'▶\';
}

function renderKPI() {
  const ch = data.channel;
  document.getElementById(\'kpi-subs\').textContent = fmt(ch.subscribers);
  document.getElementById(\'kpi-views\').textContent = fmt(ch.total_views);
  document.getElementById(\'kpi-vcount\').textContent = fmt(ch.video_count);

  const ds = data.daily_series;
  if (ds.views.length >= 2) {
    const last = ds.views[ds.views.length - 1] || 0;
    const prev = ds.views[ds.views.length - 2] || 0;
    const diff = last - prev;
    const el = document.getElementById(\'kpi-growth\');
    el.textContent = (diff >= 0 ? \'+\' : \'\') + fmt(diff);
    el.className = \'kpi-value \' + (diff >= 0 ? \'pos\' : \'neg\');
    const date = ds.dates[ds.dates.length - 1] || \'\';
    document.getElementById(\'kpi-growth-date\').textContent = date ? date.slice(5) : \'\';
  }
}

fetch(\'data.json\')
  .then(r => r.json())
  .then(d => {
    data = d;
    document.getElementById(\'last-updated\').textContent = \'最終更新: \' + (d.generated_at || \'\') + \' JST\';
    renderKPI();
    showChart(\'views\', document.querySelector(\'.tab-btn.active\'));
    renderTraffic();
    renderTable([...d.videos].sort((a, b) => (b.views || 0) - (a.views || 0)));
    renderAnalysis();
    renderRankings();
    // ロード後にハッシュが既にあればルーティング
    route();
  })
  .catch(e => {
    document.getElementById(\'last-updated\').textContent = \'data.json 読み込み失敗。http.serverで起動してください。\';
    console.error(e);
  });
</script>
</body>
</html>
'''


def main():
    skip_video_analysis = "--skip-video-analysis" in sys.argv

    patch_privacy_status_in_raw_jsons()
    raw_list = load_all_raw_jsons()
    if not raw_list:
        print("[error] analytics/*.raw.json が見つかりません", file=sys.stderr)
        sys.exit(1)

    analysis = load_analysis_history()
    data = generate_data_json(raw_list, analysis)

    # 動画個別LLM分析（上位5本 + 前日比上位3本）
    if not skip_video_analysis and data.get("videos"):
        analyze_top_videos(data["videos"])
        # 分析後に再読み込みしてdata.jsonに反映
        data["video_analysis"] = load_video_analysis()

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    data_path = DASHBOARD_DIR / "data.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[dashboard] data.json: {data_path}")

    html_path = DASHBOARD_DIR / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_html())
    print(f"[dashboard] index.html: {html_path}")

    print(f"[dashboard] 動画数: {len(data['videos'])}, 日別: {len(data['daily_series']['dates'])}日")
    print("[dashboard] 閲覧: python -m http.server 8080 -d projects/dozle_kirinuki/analytics/dashboard/")


if __name__ == "__main__":
    main()
