'use strict';

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  dates: [],
  selectedDate: null,
  topics: [],          // current report topics (full list)
  searchResults: null, // null = not in search mode
  activeCategory: 'all',
  searchQuery: '',
  debounceTimer: null,
};

// ── Category Config ────────────────────────────────────────────────────────
const CATEGORIES = [
  { key: 'all',   label: '全て',    icon: '' },
  { key: 'model', label: 'モデル',  icon: '🤖' },
  { key: 'paper', label: '論文',    icon: '📄' },
  { key: 'api',   label: 'API',     icon: '💰' },
  { key: 'oss',   label: 'OSS',     icon: '🛠️' },
  { key: 'news',  label: '動向',    icon: '📢' },
  { key: 'other', label: 'その他',  icon: '📌' },
];

// ── DOM Refs ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const dateList        = $('date-list');
const mobileDateSelect = $('mobile-date-select');
const searchInput     = $('search-input');
const searchClear     = $('search-clear');
const categoryFilters = $('category-filters');
const cardsContainer  = $('cards-container');
const loading         = $('loading');
const emptyState      = $('empty-state');
const resultCount     = $('result-count');
const darkToggle      = $('dark-toggle');

// ── Dark Mode ──────────────────────────────────────────────────────────────
function initDarkMode() {
  const saved = localStorage.getItem('genai-theme');
  // default: dark
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

// ── API Helpers ────────────────────────────────────────────────────────────
async function apiFetch(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

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
async function loadDates() {
  try {
    const data = await apiFetch('/api/dates');
    state.dates = data.dates || [];
  } catch (e) {
    state.dates = [];
    showEmpty('バックエンドに接続できません。<br>app.py を起動してからリロードしてください。', '🔌');
    return;
  }

  // Populate desktop sidebar
  dateList.innerHTML = '';
  state.dates.forEach(d => {
    const li = document.createElement('li');
    li.textContent = d;
    li.dataset.date = d;
    li.addEventListener('click', () => selectDate(d));
    dateList.appendChild(li);
  });

  // Populate mobile dropdown
  mobileDateSelect.innerHTML = '';
  state.dates.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    mobileDateSelect.appendChild(opt);
  });

  // Select most recent date
  if (state.dates.length > 0) {
    selectDate(state.dates[0]);
  }
}

function selectDate(date) {
  state.selectedDate = date;
  state.searchQuery = '';
  searchInput.value = '';
  searchClear.classList.remove('visible');
  state.searchResults = null;

  // Highlight sidebar item
  document.querySelectorAll('#date-list li').forEach(li => {
    li.classList.toggle('active', li.dataset.date === date);
  });
  mobileDateSelect.value = date;

  loadReport(date);
}

mobileDateSelect.addEventListener('change', e => selectDate(e.target.value));

// ── Report Loading ─────────────────────────────────────────────────────────
async function loadReport(date) {
  showLoading();
  try {
    const data = await apiFetch(`/api/report/${date}`);
    state.topics = data.topics || [];
    state.searchResults = null;
    renderTopics();
  } catch (e) {
    hideLoading();
    showEmpty(`レポートを読み込めませんでした（${date}）`, '📭');
  }
}

// ── Search ─────────────────────────────────────────────────────────────────
searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim();
  searchClear.classList.toggle('visible', q.length > 0);
  clearTimeout(state.debounceTimer);
  if (q.length === 0) {
    state.searchResults = null;
    state.searchQuery = '';
    renderTopics();
    return;
  }
  state.debounceTimer = setTimeout(() => runSearch(q), 300);
});

searchClear.addEventListener('click', () => {
  searchInput.value = '';
  searchClear.classList.remove('visible');
  state.searchResults = null;
  state.searchQuery = '';
  renderTopics();
  searchInput.focus();
});

async function runSearch(q) {
  state.searchQuery = q;
  showLoading();
  try {
    const cat = state.activeCategory !== 'all' ? `&category=${state.activeCategory}` : '';
    const data = await apiFetch(`/api/search?q=${encodeURIComponent(q)}${cat}`);
    state.searchResults = data.results || [];
    renderSearchResults();
  } catch (e) {
    hideLoading();
    showEmpty('検索に失敗しました。', '🔍');
  }
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

function renderSearchResults() {
  hideLoading();
  if (!state.searchResults) return;
  // searchResults: [{date, topic}, ...]
  // flatten to topic objects with optional date badge
  const cards = state.searchResults.map(r => ({ ...r.topic, _date: r.date }));
  renderCards(cards, true);
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
  emptyState.innerHTML = `
    <div class="empty-icon">${icon}</div>
    <p>${message}</p>
  `;
  emptyState.classList.add('visible');
  resultCount.textContent = '';
}

// ── Security Helpers ────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeAttr(str) {
  // Allow only http/https URLs
  const s = String(str).trim();
  if (/^https?:\/\//i.test(s)) return s;
  if (s === '#') return '#';
  return '#';
}

// ── Init ───────────────────────────────────────────────────────────────────
function init() {
  initDarkMode();
  buildCategoryButtons();
  loadDates();
}

document.addEventListener('DOMContentLoaded', init);
