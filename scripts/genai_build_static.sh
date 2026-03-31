#!/usr/bin/env bash
# genai_build_static.sh — genai_viewerを静的HTMLとしてdist/に出力する
# 出力: dist/index.html, dist/style.css, dist/app.js
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"
REPORTS_DIR="$REPO_ROOT/reports/genai_daily"
STATIC_DIR="$REPO_ROOT/genai_viewer/static"

mkdir -p "$DIST_DIR"

echo "[genai_build_static] レポート解析中..."

python3 - <<'PYEOF'
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent if '__file__' in dir() else Path.cwd().parent
SCRIPT_DIR = Path(__file__).parent if '__file__' in dir() else Path.cwd()

import os
REPO_ROOT = Path(os.environ.get('REPO_ROOT', Path(__file__).parent.parent if '__file__' in dir() else ''))
REPORTS_DIR = REPO_ROOT / "reports" / "genai_daily"
OGP_CACHE_FILE = REPORTS_DIR / ".ogp_cache.json"
DIST_DIR = REPO_ROOT / "dist"
STATIC_DIR = REPO_ROOT / "genai_viewer" / "static"

CATEGORY_MAP = {
    "🤖": "model",
    "📄": "paper",
    "💰": "api",
    "🛠️": "oss",
    "📢": "news",
}


def load_ogp_cache():
    if OGP_CACHE_FILE.exists():
        try:
            return json.loads(OGP_CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_category(emoji):
    for icon, category in CATEGORY_MAP.items():
        if emoji.startswith(icon):
            return category, icon
    return "other", emoji[:2] if emoji else ""


def parse_report(md_text):
    topics = []
    lines = md_text.splitlines()
    current_title = None
    current_icon = ""
    current_category = ""
    current_score = 0
    summary_lines = []
    in_topic = False
    source_pattern = re.compile(r'\*\*ソース\*\*:\s*\[([^\]]+)\]\(([^)]+)\)')

    def flush_topic():
        nonlocal summary_lines, current_score
        if current_title is None:
            return
        source_name = ""
        source_url = ""
        cleaned = []
        for line in summary_lines:
            m = source_pattern.search(line)
            if m:
                source_name = m.group(1)
                source_url = m.group(2)
            else:
                cleaned.append(line)
        summary = "\n".join(cleaned).strip()
        topics.append({
            "title": current_title,
            "category": current_category,
            "category_icon": current_icon,
            "score": current_score,
            "summary": summary,
            "source_name": source_name,
            "source_url": source_url,
        })

    for line in lines:
        if line.startswith("## "):
            if in_topic:
                flush_topic()
            heading = line[3:].strip()
            category, icon = get_category(heading)
            score = 0
            star_m = re.search(r'(★[★☆]{4})\s*', heading)
            if star_m:
                stars = star_m.group(1)
                score = stars.count('★') * 20
                heading = heading[:star_m.start()] + heading[star_m.end():]
            title = re.sub(r'^[^\w\d\u3000-\u9FFF\uF900-\uFAFF]+', '', heading)
            current_title = title.strip()
            current_icon = icon
            current_category = category
            current_score = score
            summary_lines = []
            in_topic = True
        elif line.strip() == "---":
            if in_topic:
                flush_topic()
                in_topic = False
                current_title = None
                summary_lines = []
        elif in_topic:
            summary_lines.append(line)

    if in_topic and current_title:
        flush_topic()

    return topics


def list_dates():
    if not REPORTS_DIR.exists():
        return []
    dates = []
    for f in REPORTS_DIR.glob("*.md"):
        stem = f.stem
        if "test" in stem or stem.count("-") != 2:
            continue
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', stem):
            dates.append(stem)
    return sorted(dates, reverse=True)


def enrich_topics_with_ogp(topics, cache):
    for topic in topics:
        url = topic.get("source_url", "")
        topic["ogp_image"] = cache.get(url) if url and url != "#" else None
    return topics


def build_static_data():
    cache = load_ogp_cache()
    dates = list_dates()
    reports = {}
    for date in dates:
        md_path = REPORTS_DIR / f"{date}.md"
        try:
            md_text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        topics = parse_report(md_text)
        if any(t["score"] > 0 for t in topics):
            topics = sorted(topics, key=lambda t: t["score"], reverse=True)
        topics = enrich_topics_with_ogp(topics, cache)
        reports[date] = topics
    return {"dates": dates, "reports": reports}


static_data = build_static_data()
data_json = json.dumps(static_data, ensure_ascii=False)
print(f"[genai_build_static] {len(static_data['dates'])}日分のデータを解析完了")

# ── style.css コピー ──────────────────────────────────────────────────────
import shutil
shutil.copy(STATIC_DIR / "style.css", DIST_DIR / "style.css")
print("[genai_build_static] style.css コピー完了")

# ── 静的版 app.js 生成 ────────────────────────────────────────────────────
static_app_js = r"""'use strict';

// ── Static Data (injected at build time) ──────────────────────────────────
// window.STATIC_DATA = { dates: [...], reports: { "YYYY-MM-DD": [topics] } }

const CATEGORIES = [
  { key: 'all',   label: '全て',    icon: '' },
  { key: 'model', label: 'モデル',  icon: '🤖' },
  { key: 'paper', label: '論文',    icon: '📄' },
  { key: 'api',   label: 'API',     icon: '💰' },
  { key: 'oss',   label: 'OSS',     icon: '🛠️' },
  { key: 'news',  label: '動向',    icon: '📢' },
  { key: 'other', label: 'その他',  icon: '📌' },
];

const state = {
  dates: [],
  selectedDate: null,
  topics: [],
  activeCategory: 'all',
  searchQuery: '',
  debounceTimer: null,
};

const $ = id => document.getElementById(id);
const dateList         = $('date-list');
const mobileDateSelect = $('mobile-date-select');
const searchInput      = $('search-input');
const searchClear      = $('search-clear');
const categoryFilters  = $('category-filters');
const cardsContainer   = $('cards-container');
const loading          = $('loading');
const emptyState       = $('empty-state');
const resultCount      = $('result-count');
const darkToggle       = $('dark-toggle');

// ── Dark Mode ──────────────────────────────────────────────────────────────
function initDarkMode() {
  const saved = localStorage.getItem('genai-theme');
  if (saved === 'light') {
    document.body.classList.add('light-mode');
    darkToggle.textContent = '☀️';
  } else {
    darkToggle.textContent = '🌙';
  }
}

darkToggle.addEventListener('click', () => {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  darkToggle.textContent = isLight ? '☀️' : '🌙';
  localStorage.setItem('genai-theme', isLight ? 'light' : 'dark');
});

// ── Loading helpers ────────────────────────────────────────────────────────
function showLoading() {
  loading.classList.add('visible');
  cardsContainer.innerHTML = '';
  emptyState.classList.remove('visible');
  resultCount.textContent = '';
}

function hideLoading() {
  loading.classList.remove('visible');
}

// ── Date Sidebar ───────────────────────────────────────────────────────────
function loadDates() {
  const data = window.STATIC_DATA || { dates: [], reports: {} };
  state.dates = data.dates || [];

  if (state.dates.length === 0) {
    showEmpty('レポートデータがありません。', '📭');
    return;
  }

  dateList.innerHTML = '';
  state.dates.forEach(d => {
    const li = document.createElement('li');
    li.textContent = d;
    li.dataset.date = d;
    li.addEventListener('click', () => selectDate(d));
    dateList.appendChild(li);
  });

  mobileDateSelect.innerHTML = '';
  state.dates.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    mobileDateSelect.appendChild(opt);
  });

  if (state.dates.length > 0) {
    selectDate(state.dates[0]);
  }
}

function selectDate(date) {
  state.selectedDate = date;
  state.searchQuery = '';
  searchInput.value = '';
  searchClear.classList.remove('visible');

  document.querySelectorAll('#date-list li').forEach(li => {
    li.classList.toggle('active', li.dataset.date === date);
  });
  mobileDateSelect.value = date;

  loadReport(date);
}

mobileDateSelect.addEventListener('change', e => selectDate(e.target.value));

// ── Report Loading (from static data) ─────────────────────────────────────
function loadReport(date) {
  showLoading();
  const data = window.STATIC_DATA || { dates: [], reports: {} };
  const topics = (data.reports && data.reports[date]) || [];
  state.topics = topics;
  renderTopics();
}

// ── Search (client-side) ───────────────────────────────────────────────────
searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim();
  searchClear.classList.toggle('visible', q.length > 0);
  clearTimeout(state.debounceTimer);
  state.searchQuery = q;
  if (q.length === 0) {
    renderTopics();
    return;
  }
  state.debounceTimer = setTimeout(() => runSearch(q), 200);
});

searchClear.addEventListener('click', () => {
  searchInput.value = '';
  searchClear.classList.remove('visible');
  state.searchQuery = '';
  renderTopics();
  searchInput.focus();
});

function runSearch(q) {
  const data = window.STATIC_DATA || { dates: [], reports: {} };
  const ql = q.toLowerCase();
  const cat = state.activeCategory;
  const results = [];
  for (const date of (data.dates || [])) {
    const topics = (data.reports && data.reports[date]) || [];
    for (const topic of topics) {
      if (cat !== 'all' && topic.category !== cat) continue;
      if (ql && !topic.title.toLowerCase().includes(ql) && !topic.summary.toLowerCase().includes(ql)) continue;
      results.push({ date, topic: { ...topic, _date: date } });
      if (results.length >= 50) break;
    }
    if (results.length >= 50) break;
  }
  hideLoading();
  renderCards(results.map(r => r.topic), true);
}

// ── Category Filters ───────────────────────────────────────────────────────
function buildCategoryButtons() {
  categoryFilters.innerHTML = '';
  CATEGORIES.forEach(({ key, label, icon }) => {
    const btn = document.createElement('button');
    btn.className = 'cat-btn' + (key === 'all' ? ' active' : '');
    btn.dataset.cat = key;
    btn.textContent = icon ? `${icon} ${label}` : label;
    btn.addEventListener('click', () => setCategory(key));
    categoryFilters.appendChild(btn);
  });
}

function setCategory(cat) {
  state.activeCategory = cat;
  document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.cat === cat);
  });
  if (state.searchQuery) {
    runSearch(state.searchQuery);
  } else {
    renderTopics();
  }
}

// ── Render ─────────────────────────────────────────────────────────────────
function renderTopics() {
  hideLoading();
  let topics = state.topics;
  if (state.activeCategory !== 'all') {
    topics = topics.filter(t => t.category === state.activeCategory);
  }
  renderCards(topics);
}

function renderCards(topics, showDateBadge = false) {
  cardsContainer.innerHTML = '';
  if (topics.length === 0) {
    resultCount.textContent = '';
    showEmpty(
      state.searchQuery
        ? `「${state.searchQuery}」の検索結果はありません。`
        : 'このカテゴリのトピックはありません。',
      '🔎'
    );
    return;
  }
  emptyState.classList.remove('visible');
  resultCount.textContent = `${topics.length} 件`;
  topics.forEach(topic => {
    const card = buildCard(topic, showDateBadge);
    cardsContainer.appendChild(card);
  });
}

function buildCard(topic, showDateBadge) {
  const card = document.createElement('article');
  card.className = 'topic-card';
  card.dataset.category = topic.category || 'other';
  card.style.cursor = 'pointer';
  card.addEventListener('click', (e) => {
    if (e.target.tagName === 'A') return;
    const url = topic.source_url || '#';
    if (url !== '#') {
      trackClick(topic.title || '', url);
      window.open(url, '_blank', 'noopener');
    }
  });

  const icon = topic.category_icon || getCategoryIcon(topic.category);
  const title = escapeHtml(topic.title || '(タイトルなし)');
  const summary = escapeHtml(topic.summary || '');
  const sourceName = escapeHtml(topic.source_name || 'ソースを見る');
  const sourceUrl = topic.source_url || '#';
  const dateBadge = showDateBadge && topic._date
    ? `<span class="card-date-badge">${escapeHtml(topic._date)}</span>`
    : '';
  const score = topic.score || 0;
  const starCount = Math.round(score / 20);
  const stars = '★'.repeat(starCount) + '☆'.repeat(5 - starCount);
  const starHtml = score > 0
    ? `<span class="card-stars" title="重要度: ${score}/100">${stars}</span>`
    : '';
  const ogpUrl = topic.ogp_image ? escapeAttr(topic.ogp_image) : '';
  const thumbnailHtml = ogpUrl
    ? `<div class="card-thumbnail"><img src="${ogpUrl}" alt="" loading="lazy" onerror="this.parentElement.style.display='none'"></div>`
    : '';

  card.innerHTML = `
    ${thumbnailHtml}
    <div class="card-header">
      <span class="card-icon">${icon}</span>
      <h2 class="card-title">${title}</h2>
      ${starHtml}
    </div>
    <p class="card-summary">${summary}</p>
    <div class="card-footer">
      <a class="card-source-link"
         href="${escapeAttr(sourceUrl)}"
         target="_blank"
         rel="noopener noreferrer">
        ${sourceName} →
      </a>
      ${dateBadge}
    </div>
  `;
  if (sourceUrl !== '#') {
    const link = card.querySelector('.card-source-link');
    if (link) link.addEventListener('click', () => trackClick(topic.title || '', sourceUrl));
  }
  return card;
}

function getCategoryIcon(cat) {
  const map = { model: '🤖', paper: '📄', api: '💰', oss: '🛠️', news: '📢', other: '📌' };
  return map[cat] || '📌';
}

function showEmpty(message, icon = '📭') {
  emptyState.innerHTML = `<div class="empty-icon">${icon}</div><p>${message}</p>`;
  emptyState.classList.add('visible');
  resultCount.textContent = '';
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeAttr(str) {
  const s = String(str).trim();
  if (/^https?:\/\//i.test(s)) return s;
  if (s === '#') return '#';
  return '#';
}

// ── Click Tracking ─────────────────────────────────────────────────────────
function trackClick(title, url) {
  try {
    const clicks = JSON.parse(localStorage.getItem('genai-clicks') || '[]');
    clicks.push({ title, url, clicked_at: new Date().toISOString() });
    if (clicks.length > 500) clicks.splice(0, clicks.length - 500);
    localStorage.setItem('genai-clicks', JSON.stringify(clicks));
    const counts = JSON.parse(localStorage.getItem('genai-click-counts') || '{}');
    counts[url] = (counts[url] || 0) + 1;
    localStorage.setItem('genai-click-counts', JSON.stringify(counts));
  } catch (e) { /* localStorage unavailable */ }
}

function init() {
  initDarkMode();
  buildCategoryButtons();
  loadDates();
}

document.addEventListener('DOMContentLoaded', init);
"""

(DIST_DIR / "app.js").write_text(static_app_js, encoding="utf-8")
print("[genai_build_static] app.js 生成完了")

# ── index.html 生成（データ埋め込み）─────────────────────────────────────
build_date = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')
topic_count = sum(len(v) for v in static_data['reports'].values())

html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🤖 GenAI Daily</title>
  <meta name="description" content="生成AI最新情報まとめ (静的版)">
  <link rel="stylesheet" href="style.css">
</head>
<body>

  <!-- ── Header ── -->
  <header id="header">
    <h1>🤖 GenAI Daily</h1>
    <button id="dark-toggle" aria-label="ダークモード切替">🌙</button>
  </header>

  <!-- ── Mobile: date dropdown (shown < 768px) ── -->
  <div id="mobile-date-row">
    <label for="mobile-date-select">📅 日付:</label>
    <select id="mobile-date-select" aria-label="日付選択"></select>
  </div>

  <!-- ── Main Layout ── -->
  <div id="layout">

    <!-- Sidebar: date list (desktop) -->
    <nav id="sidebar" aria-label="日付一覧">
      <div id="sidebar-title">📅 日付</div>
      <ul id="date-list" role="listbox" aria-label="レポート日付"></ul>
    </nav>

    <!-- Main Content -->
    <div id="main">
      <div id="toolbar">
        <div id="search-row">
          <input
            id="search-input"
            type="search"
            placeholder="🔍 キーワードで検索..."
            aria-label="キーワード検索"
          >
          <button id="search-clear" aria-label="検索クリア">✕</button>
        </div>
        <div id="category-filters" role="group" aria-label="カテゴリフィルタ"></div>
      </div>

      <div id="content-area" role="main">
        <div id="result-count" aria-live="polite"></div>
        <div id="loading" aria-live="polite" aria-label="読み込み中">
          <div class="spinner"></div>
        </div>
        <div id="empty-state" aria-live="polite"></div>
        <div id="cards-container" aria-label="トピック一覧"></div>
      </div>
    </div>
  </div>

  <!-- ビルド情報 -->
  <footer style="text-align:center;padding:8px;font-size:11px;color:var(--text-muted)">
    静的版 | {len(static_data['dates'])}日分 {topic_count}件 | ビルド: {build_date}
  </footer>

  <!-- 埋め込みデータ -->
  <script>
window.STATIC_DATA = {data_json};
  </script>
  <script src="app.js"></script>
</body>
</html>"""

(DIST_DIR / "index.html").write_text(html, encoding="utf-8")
print(f"[genai_build_static] index.html 生成完了 ({len(static_data['dates'])}日分, {topic_count}件)")

# ── stats.html 生成（クリック統計ページ）──────────────────────────────────
stats_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📊 GenAI Daily - クリック統計</title>
  <style>
    body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 16px; background: #1a1a2e; color: #e0e0e0; }
    h1 { font-size: 1.4rem; margin-bottom: 8px; }
    .back { color: #88aaff; text-decoration: none; font-size: 0.9rem; }
    .back:hover { text-decoration: underline; }
    .summary { font-size: 0.85rem; color: #aaa; margin: 8px 0 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th { text-align: left; padding: 8px; border-bottom: 2px solid #333; color: #aaa; }
    td { padding: 8px; border-bottom: 1px solid #2a2a3e; vertical-align: top; }
    td a { color: #88aaff; text-decoration: none; word-break: break-all; }
    td a:hover { text-decoration: underline; }
    .count { font-weight: bold; color: #ffd700; text-align: center; }
    .empty { text-align: center; padding: 40px; color: #666; }
    .clear-btn { margin-top: 24px; padding: 8px 16px; background: #3a1a1a; color: #ff8888; border: 1px solid #cc4444; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
    .clear-btn:hover { background: #5a2a2a; }
  </style>
</head>
<body>
  <h1>📊 クリック統計</h1>
  <a class="back" href="/">← GenAI Daily に戻る</a>
  <div class="summary" id="summary"></div>
  <div id="content"></div>
  <button class="clear-btn" onclick="clearStats()">統計をリセット</button>
  <script>
    function loadStats() {
      const clicks = JSON.parse(localStorage.getItem('genai-clicks') || '[]');
      const counts = JSON.parse(localStorage.getItem('genai-click-counts') || '{}');
      const summary = document.getElementById('summary');
      const content = document.getElementById('content');

      if (clicks.length === 0) {
        summary.textContent = 'クリック履歴なし';
        content.innerHTML = '<div class="empty">まだクリックデータがありません。<br><a href="/" style="color:#88aaff">記事を読んでみましょう →</a></div>';
        return;
      }

      summary.textContent = `総クリック数: ${clicks.length}件 | ユニークURL: ${Object.keys(counts).length}件`;

      // Sort by count desc
      const sorted = Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 50);

      // Build title map from click history
      const titleMap = {};
      for (const c of clicks) {
        if (c.url && c.title && !titleMap[c.url]) titleMap[c.url] = c.title;
      }

      let rows = sorted.map(([url, count]) => {
        const title = titleMap[url] || url;
        const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        return `<tr>
          <td class="count">${count}</td>
          <td><a href="${esc(url)}" target="_blank" rel="noopener">${esc(title)}</a></td>
        </tr>`;
      }).join('');

      content.innerHTML = `<table>
        <thead><tr><th style="width:60px">回数</th><th>記事</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    }

    function clearStats() {
      if (confirm('クリック統計をリセットしますか？')) {
        localStorage.removeItem('genai-clicks');
        localStorage.removeItem('genai-click-counts');
        loadStats();
      }
    }

    loadStats();
  </script>
</body>
</html>"""

(DIST_DIR / "stats.html").write_text(stats_html, encoding="utf-8")
print("[genai_build_static] stats.html 生成完了")
print(f"[genai_build_static] 出力先: {DIST_DIR}")
PYEOF

echo "[genai_build_static] 完了"
