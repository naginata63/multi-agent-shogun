#!/usr/bin/env python3
"""
generate_dashboard.py — YouTube解析HTMLダッシュボード生成

Usage:
    python3 scripts/generate_dashboard.py

出力:
    projects/dozle_kirinuki/analytics/dashboard/data.json
    projects/dozle_kirinuki/analytics/dashboard/index.html

閲覧:
    cd projects/dozle_kirinuki/analytics/dashboard
    python -m http.server 8080
    # → http://localhost:8080
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR / "projects" / "dozle_kirinuki"
ANALYTICS_DIR = PROJECT_DIR / "analytics"
DASHBOARD_DIR = ANALYTICS_DIR / "dashboard"
ANALYSIS_HISTORY_PATH = ANALYTICS_DIR / "analysis_history.json"


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

        entry = {
            "id": v["id"],
            "title": v.get("title", ""),
            "views": views,
            "likes": likes,
            "like_rate": round(likes / views * 100, 2) if views > 0 else 0,
            "duration_sec": duration_sec,
            "duration_str": v.get("duration_str", ""),
            "is_short": duration_sec <= 180,
            "published_at": pub,
            "loop_rate": pva.get("loop_rate"),
            "avg_view_pct": pva.get("avg_view_pct"),
            "view_diff_1d": views - prev_map.get(v["id"], views) if prev_raw else None,
        }
        result.append(entry)

    return result


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

    ch = latest_raw.get("channel", {})
    daily_series = build_daily_series(raw_list)
    videos = build_video_table(latest_raw, prev_raw)
    traffic = latest_raw.get("traffic_sources", [])

    jst = timezone(timedelta(hours=9))
    generated_at = datetime.now(jst).strftime("%Y-%m-%dT%H:%M:%S")

    return {
        "generated_at": generated_at,
        "channel": {
            "name": ch.get("name", ""),
            "subscribers": ch.get("subscribers", 0),
            "total_views": ch.get("total_views", 0),
            "video_count": ch.get("video_count", 0),
        },
        "daily_series": daily_series,
        "traffic_sources": traffic,
        "videos": videos,
        "analysis_history": analysis,
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
  </style>
</head>
<body>
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
    <h2>AI分析コメント</h2>
    <div id="analysis-list"><p id="no-data" style="display:none">分析コメントなし</p></div>
  </div>

<script>
let data = null;
let currentSort = { key: \'views\', dir: -1 };
let dailyChartInstance = null;

const fmt = n => n == null ? \'-\' : n.toLocaleString();
const fmtPct = n => n == null ? \'-\' : n.toFixed(1) + \'%\';
const fmtRate = n => n == null ? \'-\' : n.toFixed(3);

const metricConfig = {
  views:  { label: \'日別再生数\', key: \'views\',       type: \'bar\' },
  subs:   { label: \'累計登録者\', key: \'subscribers_cumulative\', type: \'line\' },
  likes:  { label: \'日別いいね\', key: \'likes\',       type: \'bar\' },
  growth: { label: \'日別登録増\', key: \'subs_gained\', type: \'bar\' },
};

function showChart(metric, btn) {
  document.querySelectorAll(\'.tab-btn\').forEach(b => b.classList.remove(\'active\'));
  if (btn) btn.classList.add(\'active\');
  if (!data) return;

  const cfg = metricConfig[metric];
  const labels = data.daily_series.dates.map(d => d.slice(5));
  const values = data.daily_series[cfg.key];

  if (dailyChartInstance) dailyChartInstance.destroy();

  const datasets = [{
    label: cfg.label,
    data: values,
    backgroundColor: \'rgba(233,69,96,0.6)\',
    borderColor: \'#e94560\',
    borderWidth: 1,
    fill: cfg.type === \'line\',
    tension: 0.3,
  }];

  // 再生数タブは7日移動平均を追加
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
      <td><a href="${ytUrl}" target="_blank" style="color:#aaa;text-decoration:none">${shortTitle}</a>${badge}</td>
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

  // 前日再生増: daily_seriesの最終2日の差
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
    raw_list = load_all_raw_jsons()
    if not raw_list:
        print("[error] analytics/*.raw.json が見つかりません", file=sys.stderr)
        sys.exit(1)

    analysis = load_analysis_history()
    data = generate_data_json(raw_list, analysis)

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
