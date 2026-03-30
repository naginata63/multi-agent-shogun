'use strict';

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
    if (url !== '#') window.open(url, '_blank', 'noopener');
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

function init() {
  initDarkMode();
  buildCategoryButtons();
  loadDates();
}

document.addEventListener('DOMContentLoaded', init);
