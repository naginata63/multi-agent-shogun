/* 釣りログ — GPS軌跡記録 PWA
 * データは全て localStorage (この端末内) に保存。サーバー送信なし。
 * 保存形式:
 *   fl_index_v1 : [{id,name,start,end,ptCount,hitCount,dist}]  … 一覧用メタ
 *   fl_sess_<id>: {id,name,start,end,points:[[t,lat,lng,acc,spd],...],hits:[{t,lat,lng,fish,size,memo}]}
 *   fl_active   : 記録中セッションid (ページ再読込からの復帰用)
 */
'use strict';

const APP_VER = '1.9';

// ---------- ネイティブ(Capacitor)検出 ----------
// APK版では @capacitor-community/background-geolocation の Foreground Service で
// 画面OFFでも記録継続。ブラウザ(PWA)では従来どおり watchPosition + WakeLock。
let IS_NATIVE = false, CapBG = null;
try {
  IS_NATIVE = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
  if (IS_NATIVE && window.Capacitor.registerPlugin) CapBG = window.Capacitor.registerPlugin('BackgroundGeolocation');
} catch (e) { if (window.__showErr) window.__showErr('plugin登録失敗: ' + e.message); }
let CapBgLog = null;
try { if (IS_NATIVE && window.Capacitor.registerPlugin) CapBgLog = window.Capacitor.registerPlugin('BgLog'); } catch (e) {}
// v1.8: registerPlugin は @capacitor/core (vendor/capacitor-core.js) が供給する。
// core 未搭載だと CapBG/CapBgLog が黙って null になり、ブラウザ測位に落ちて
// 画面OFF記録が全滅する (v1.1〜v1.7 の真因)。二度と黙らせない:
if (IS_NATIVE && (!CapBG || !CapBgLog)) {
  const msg = 'ネイティブ測位プラグイン不通 (core:' +
    (window.Capacitor && window.Capacitor.registerPlugin ? 'あり' : '無し') +
    ' BG:' + (CapBG ? 'OK' : 'NG') + ' BgLog:' + (CapBgLog ? 'OK' : 'NG') + ')';
  if (window.__showErr) window.__showErr(msg);
}
let bgWatcherId = null;
let mergeTimer = null;
let lastMergeInfo = null;   // {t, n, raw} BG診断用
// 画面OFF中にネイティブが直書きした位置ログを軌跡へ合流
async function mergeNativeLog() {
  if (!CapBgLog || !S) return;
  try {
    const res = await CapBgLog.read();
    const locs = (res && res.locations) || [];
    if (!locs.length) { lastMergeInfo = { t: Date.now(), n: 0, raw: 0 }; return; }
    locs.sort((a, b) => a.t - b.t);
    const lastT = S.points.length ? S.points[S.points.length - 1][0] : 0;
    let n = 0;
    for (const l of locs) {
      if (!l || l.t <= lastT) continue;
      maybeRecord(l.t, l.lat, l.lng, l.acc == null ? 99 : l.acc, l.spd >= 0 ? l.spd * 3.6 : null);
      n++;
    }
    await CapBgLog.clear();
    lastMergeInfo = { t: Date.now(), n, raw: locs.length };
    if (n && trackLine) trackLine.setLatLngs(S.points.map(p => [p[1], p[2]]));
    if (n) persist();
  } catch (e) {}
}

// 画面OFF記録の前提条件を検査し、欠けていれば許可を求める
async function ensureBgPrereqs(interactive) {
  if (!CapBgLog || !CapBgLog.status) return;
  try {
    let st = await CapBgLog.status();
    if (!st.notifGranted) {
      toast('⚠️ 通知が未許可ゆえ画面OFF記録が不安定になりまする。許可してくだされ', 5000);
      await CapBgLog.requestNotify();
      setTimeout(async () => {
        try {
          st = await CapBgLog.status();
          if (!st.notifGranted && interactive &&
              confirm('通知がまだ許可されておりませぬ。設定画面を開きますか？\n(画面OFF記録の安定に必要でござる)')) {
            CapBgLog.openNotifySettings();
          }
        } catch (e) {}
      }, 3000);
    }
    if (st.batteryUnrestricted === false && interactive) {
      if (confirm('このアプリは電池最適化の対象になっており申す。\n「制限なし」にすると画面OFF記録が安定しまする。設定しますか？')) {
        CapBgLog.requestBatteryUnrestricted();
      }
    }
  } catch (e) {}
}

// BG診断: 画面表示 + 遠隔送信
async function runBgDiag() {
  let st = {};
  try { st = CapBgLog && CapBgLog.status ? await CapBgLog.status() : { err: 'BgLog橋なし(ブラウザ版か旧APK)' }; }
  catch (e) { st = { err: '' + e }; }
  const fmt = t => t ? new Date(t).toLocaleString() : '--';
  const lines = [
    'アプリ版: v' + APP_VER + (IS_NATIVE ? ' (APK)' : ' (ブラウザ)'),
    '通知許可: ' + (st.notifGranted == null ? '?' : st.notifGranted ? 'OK' : '❌ 未許可'),
    '電池最適化: ' + (st.batteryUnrestricted == null ? '?' : st.batteryUnrestricted ? '制限なし(OK)' : '⚠️ 最適化対象'),
    '未合流のBG記録: ' + (st.jsonlCount == null ? '?' : st.jsonlCount + '点'),
    'BG最終記録: ' + fmt(st.jsonlLastT),
    '最終合流: ' + (lastMergeInfo ? lastMergeInfo.n + '点採用/' + lastMergeInfo.raw + '点 @' + fmt(lastMergeInfo.t) : 'まだ'),
    '瞬間移動を除外: ' + jumpSkipped + '回',
    (st.err ? 'エラー: ' + st.err : ''),
  ].filter(Boolean);
  alert('🔧 BG診断\n' + lines.join('\n'));
  try {
    await fetch(DIAG_URL, { method: 'POST',
      body: JSON.stringify({ v: APP_VER, bgdiag: st, merge: lastMergeInfo, ua: navigator.userAgent }),
      headers: { Title: 'tsurilog-bgdiag' } });
  } catch (e) {}
}

// ---------- ユーティリティ ----------
const $ = id => document.getElementById(id);
const toast = (msg, ms = 2200) => {
  const t = $('toast'); t.textContent = msg; t.style.display = 'block';
  clearTimeout(toast._h); toast._h = setTimeout(() => t.style.display = 'none', ms);
};
const fmtT = s => {
  s = Math.floor(s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
  return h ? `${h}:${String(m).padStart(2,'0')}:${String(s%60).padStart(2,'0')}` : `${m}:${String(s%60).padStart(2,'0')}`;
};
const fmtDate = t => new Date(t).toLocaleString('ja-JP', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
const iso = t => new Date(t).toISOString();
// 2点間距離(m) haversine
function distM(la1, lo1, la2, lo2) {
  const R = 6371000, d = Math.PI / 180;
  const a = Math.sin((la2-la1)*d/2)**2 + Math.cos(la1*d)*Math.cos(la2*d)*Math.sin((lo2-lo1)*d/2)**2;
  return 2 * R * Math.asin(Math.sqrt(a));
}
const esc = s => String(s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// ---------- ストレージ ----------
const store = {
  index() { try { return JSON.parse(localStorage.getItem('fl_index_v1')) || []; } catch { return []; } },
  saveIndex(ix) { localStorage.setItem('fl_index_v1', JSON.stringify(ix)); },
  sess(id) { try { return JSON.parse(localStorage.getItem('fl_sess_' + id)); } catch { return null; } },
  saveSess(s) {
    try { localStorage.setItem('fl_sess_' + s.id, JSON.stringify(s)); }
    catch (e) { toast('⚠️ 保存容量が一杯。古い記録を書き出して削除してくだされ', 4000); }
  },
  delSess(id) {
    localStorage.removeItem('fl_sess_' + id);
    store.saveIndex(store.index().filter(x => x.id !== id));
  },
  usage() {
    let n = 0; for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i); if (k.startsWith('fl_')) n += (localStorage.getItem(k) || '').length;
    }
    return n;
  }
};

// ---------- 地図 ----------
const map = L.map('map', { zoomControl: false, attributionControl: true }).setView([35.30, 139.48], 11);
L.control.attribution({ prefix: false }).addAttribution('© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors');
const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const tileLayer = L.tileLayer(TILE_URL, { maxZoom: 18 }).addTo(map);
let tileErrN = 0;
tileLayer.on('tileerror', () => {
  tileErrN++;
  if (tileErrN === 3) toast('⚠️ 地図タイルの読込に失敗しております(通信環境を確認)', 4000);
});

let posMarker = null, accCircle = null, trackLine = null;
const hitLayer = L.layerGroup().addTo(map);

function drawPos(lat, lng, acc) {
  if (!posMarker) {
    posMarker = L.circleMarker([lat, lng], { radius: 8, color: '#fff', weight: 2, fillColor: '#2fa8ff', fillOpacity: 1 }).addTo(map);
    accCircle = L.circle([lat, lng], { radius: acc, color: '#2fa8ff', weight: 1, opacity: .4, fillOpacity: .08 }).addTo(map);
  } else {
    posMarker.setLatLng([lat, lng]);
    accCircle.setLatLng([lat, lng]).setRadius(acc);
  }
}
function drawHit(h, n) {
  const m = L.circleMarker([h.lat, h.lng], { radius: 9, color: '#fff', weight: 2, fillColor: '#ff5a5a', fillOpacity: 1 }).addTo(hitLayer);
  const label = [h.fish, h.size].filter(Boolean).join(' ') || ('ヒット#' + n);
  m.bindPopup(`🎣 <b>${esc(label)}</b><br>${fmtDate(h.t)}<br>${esc(h.memo || '')}`);
}

// ---------- 記録状態 ----------
let S = null;              // 現行セッション
let watching = null;       // watchPosition id
let lastPos = null;        // 直近の生位置 [t,lat,lng,acc,spdKmh]
let lastSaved = 0;         // 最終保存時刻
let follow = true;
let tickTimer = null;

function newSession() {
  const id = Date.now().toString(36);
  return { id, name: '釣行 ' + new Date().toLocaleDateString('ja-JP'), start: Date.now(), end: null, points: [], hits: [] };
}
function sessDist(points) {
  let d = 0;
  for (let i = 1; i < points.length; i++) d += distM(points[i-1][1], points[i-1][2], points[i][1], points[i][2]);
  return d;
}

// 点の採用判定: 前回採用点から 4m 以上 or 5秒以上、精度75m以内
// 瞬間移動ガード: 釣り(船・徒歩)で出る速度をはるかに超える飛びは測位エラーとみなす。
// 地下→地上復帰時に古い座標が混じると軌跡が数km巻き戻る (2026-08-06 殿報告)。
// 海上の実速度(最大60km/h程度)では決して発動せぬ余裕をとる。
const JUMP_KMH = 150;
let jumpSkipped = 0;

function maybeRecord(t, lat, lng, acc, spd) {
  if (acc > 75) return;
  const P = S.points;
  if (P.length) {
    const last = P[P.length - 1];
    if (t - last[0] < 5000 && distM(last[1], last[2], lat, lng) < 4) return;
    const dt = (t - last[0]) / 1000;
    if (dt > 0) {
      const kmh = distM(last[1], last[2], lat, lng) / dt * 3.6;
      // 200m超の飛びかつ異常速度のみ弾く(短距離のGPS揺れは通す)
      if (kmh > JUMP_KMH && distM(last[1], last[2], lat, lng) > 200) {
        jumpSkipped++;
        return;
      }
    }
  }
  P.push([t, +lat.toFixed(6), +lng.toFixed(6), Math.round(acc), spd == null ? null : +spd.toFixed(1)]);
  if (trackLine) trackLine.addLatLng([lat, lng]);
  if (t - lastSaved > 5000) { persist(); lastSaved = t; }
}

function persist() {
  if (!S) return;
  store.saveSess(S);
  const ix = store.index().filter(x => x.id !== S.id);
  ix.unshift({ id: S.id, name: S.name, start: S.start, end: S.end,
    ptCount: S.points.length, hitCount: S.hits.length, dist: sessDist(S.points) });
  store.saveIndex(ix);
}

function onPos(p) {
  const { latitude: lat, longitude: lng, accuracy: acc } = p.coords;
  let spdKmh = p.coords.speed != null && !isNaN(p.coords.speed) ? p.coords.speed * 3.6 : null;
  const t = Date.now();
  if (spdKmh == null && lastPos) {
    const dt = (t - lastPos[0]) / 1000;
    if (dt > 0.5) spdKmh = distM(lastPos[1], lastPos[2], lat, lng) / dt * 3.6;
  }
  lastPos = [t, lat, lng, acc, spdKmh];
  drawPos(lat, lng, acc);
  if (follow) map.panTo([lat, lng], { animate: true, duration: .4 });
  const av = $('accv'); av.textContent = Math.round(acc);
  av.className = acc <= 15 ? 'v good' : acc <= 40 ? 'v mid' : 'v bad';
  $('sv').textContent = spdKmh == null ? '--' : spdKmh.toFixed(1);
  if (S) maybeRecord(t, lat, lng, acc, spdKmh);
}
function onPosErr(e) {
  if (e.code === 1) toast('位置情報が許可されておりませぬ。ブラウザ設定で許可してくだされ', 4000);
  else toast('GPS取得エラー: ' + e.message, 3000);
}
function startWatch() {
  if (watching != null) return;
  watching = navigator.geolocation.watchPosition(onPos, onPosErr,
    { enableHighAccuracy: true, maximumAge: 1000, timeout: 20000 });
}
function stopBrowserWatch() {
  if (watching != null) { navigator.geolocation.clearWatch(watching); watching = null; }
}
// ネイティブ: Foreground Service 測位(画面OFFでも継続)
function startNativeWatch() {
  return CapBG.addWatcher({
    backgroundTitle: '🎣 釣りログ',
    backgroundMessage: 'GPS軌跡を記録中(タップで戻る)',
    requestPermissions: true,
    stale: false,
    distanceFilter: 3
  }, (loc, err) => {
    if (err) {
      if (err.code === 'NOT_AUTHORIZED' &&
          confirm('位置情報の権限がありませぬ。設定を開きますか？')) CapBG.openSettings();
      return;
    }
    onPos({ coords: { latitude: loc.latitude, longitude: loc.longitude,
                      accuracy: loc.accuracy || 99, speed: loc.speed } });
  }).then(id => { bgWatcherId = id; });
}
function stopNativeWatch() {
  if (bgWatcherId) { CapBG.removeWatcher({ id: bgWatcherId }); bgWatcherId = null; }
}

// ---------- Wake Lock ----------
let wakeLock = null, wakeWanted = false;
async function acquireWake() {
  if (!('wakeLock' in navigator)) { $('wakeState').textContent = '非対応'; return; }
  try {
    wakeLock = await navigator.wakeLock.request('screen');
    $('wakeState').textContent = 'ON';
    wakeLock.addEventListener('release', () => { $('wakeState').textContent = 'OFF'; });
  } catch (e) { $('wakeState').textContent = 'OFF'; }
}
function releaseWake() { if (wakeLock) { wakeLock.release(); wakeLock = null; } $('wakeState').textContent = 'OFF'; }
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    if (wakeWanted) acquireWake();
    if (S && !IS_NATIVE) toast('復帰いたした。バックグラウンド中は記録が止まりまする', 3000);
    if (S && IS_NATIVE) mergeNativeLog();
  }
});

// ---------- 記録開始/停止 ----------
function beginTracking(resume) {
  if (!resume) {
    S = newSession();
    localStorage.setItem('fl_active', S.id);
    if (trackLine) map.removeLayer(trackLine);
    hitLayer.clearLayers();
    trackLine = L.polyline([], { color: '#2fa8ff', weight: 4, opacity: .9 }).addTo(map);
  } else {
    trackLine = L.polyline(S.points.map(p => [p[1], p[2]]), { color: '#2fa8ff', weight: 4, opacity: .9 }).addTo(map);
    S.hits.forEach((h, i) => drawHit(h, i + 1));
  }
  if (IS_NATIVE && CapBG) {
    if (!resume && CapBgLog) CapBgLog.clear().catch(() => {});
    if (resume) mergeNativeLog();
    ensureBgPrereqs(!resume);
    clearInterval(mergeTimer);
    mergeTimer = setInterval(mergeNativeLog, 15000);
    stopBrowserWatch();
    startNativeWatch().catch(e => {
      if (window.__showErr) window.__showErr('BG測位失敗: ' + e.message);
      startWatch(); wakeWanted = true; acquireWake();
    });
  } else { wakeWanted = true; acquireWake(); }
  $('btnStart').textContent = '■ 停止'; $('btnStart').classList.add('stop');
  $('btnHit').style.display = 'block';
  $('recdot').style.display = 'flex';
  tickTimer = setInterval(() => {
    $('tv').textContent = fmtT((Date.now() - S.start) / 1000);
    $('dv').textContent = (sessDist(S.points) / 1000).toFixed(2);
  }, 1000);
  toast(resume ? '記録を再開いたした' : '記録開始。良い釣りを！');
}
async function stopTracking() {
  clearInterval(mergeTimer); mergeTimer = null;
  if (IS_NATIVE) { try { await mergeNativeLog(); } catch (e) {} }
  S.end = Date.now(); persist();
  localStorage.removeItem('fl_active');
  clearInterval(tickTimer);
  if (IS_NATIVE) { stopNativeWatch(); startWatch(); }
  wakeWanted = false; releaseWake();
  $('btnStart').textContent = '▶ 記録開始'; $('btnStart').classList.remove('stop');
  $('btnHit').style.display = 'none';
  $('recdot').style.display = 'none';
  const d = (sessDist(S.points) / 1000).toFixed(2);
  toast(`記録終了: ${d}km・ヒット${S.hits.length}回。メニュー→GPX書き出しで保存できまする`, 4500);
  S = null;
}
$('btnStart').onclick = () => {
  if (S) { if (confirm('記録を停止しますか？')) stopTracking(); }
  else beginTracking(false);
};

// ---------- ヒット ----------
let pendingHit = null;
$('btnHit').onclick = () => {
  if (!lastPos) { toast('まだGPSを取得できておりませぬ'); return; }
  pendingHit = { t: Date.now(), lat: lastPos[1], lng: lastPos[2], fish: '', size: '', memo: '' };
  S.hits.push(pendingHit); persist();
  drawHit(pendingHit, S.hits.length);
  $('hitTitle').textContent = '#' + S.hits.length;
  $('hFish').value = ''; $('hSize').value = ''; $('hMemo').value = '';
  openSheet('hitsheet');
  toast('位置を記録いたした！詳細は任意で');
};
$('hSave').onclick = () => {
  if (pendingHit) {
    pendingHit.fish = $('hFish').value.trim();
    pendingHit.size = $('hSize').value.trim();
    pendingHit.memo = $('hMemo').value.trim();
    persist();
    hitLayer.clearLayers(); S.hits.forEach((h, i) => drawHit(h, i + 1));
  }
  closeSheet('hitsheet'); pendingHit = null;
};

// ---------- 追尾 ----------
$('btnFollow').onclick = () => {
  follow = !follow;
  $('btnFollow').classList.toggle('on', follow);
  if (follow && lastPos) map.panTo([lastPos[1], lastPos[2]]);
  toast(follow ? '現在地を追尾' : '追尾OFF(地図を自由に動かせまする)');
};
map.on('dragstart', () => { if (follow) { follow = false; $('btnFollow').classList.remove('on'); } });

// ---------- シート開閉 ----------
function openSheet(id) { $(id).style.display = 'block'; }
function closeSheet(id) { $(id).style.display = 'none'; }
document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => closeSheet(b.dataset.close));
document.querySelectorAll('.sheet').forEach(sh => sh.addEventListener('click', e => { if (e.target === sh) sh.style.display = 'none'; }));
$('btnMenu').onclick = () => {
  const kb = store.usage() / 1024;
  $('storInfo').textContent = `保存容量: ${kb < 1024 ? kb.toFixed(0) + 'KB' : (kb/1024).toFixed(2) + 'MB'} / 約5MB(端末内)`;
  const vi = $('verInfo');
  if (vi) vi.textContent = `釣りログ v${APP_VER}` + (IS_NATIVE ? ' (APK)' : ' (Web)');
  openSheet('menu');
};
{ const b = $('mBgDiag'); if (b) b.onclick = () => runBgDiag(); }

// ---------- 書き出し ----------
function latestSession() {
  if (S) return S;
  const ix = store.index();
  return ix.length ? store.sess(ix[0].id) : null;
}
function download(name, text, mime) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: mime }));
  a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
function toGpx(s) {
  const w = s.hits.map((h, i) => {
    const nm = [h.fish, h.size].filter(Boolean).join(' ') || ('ヒット' + (i + 1));
    return `  <wpt lat="${h.lat}" lon="${h.lng}"><time>${iso(h.t)}</time><name>${esc(nm)}</name><desc>${esc(h.memo||'')}</desc></wpt>`;
  }).join('\n');
  const pts = s.points.map(p => `      <trkpt lat="${p[1]}" lon="${p[2]}"><time>${iso(p[0])}</time></trkpt>`).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="tsurilog" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>${esc(s.name)}</name><time>${iso(s.start)}</time></metadata>
${w}
  <trk><name>${esc(s.name)}</name><trkseg>
${pts}
    </trkseg></trk>
</gpx>`;
}
function toCsv(s) {
  const rows = [['type','time','lat','lng','accuracy_m','speed_kmh','fish','size','memo']];
  s.points.forEach(p => rows.push(['track', iso(p[0]), p[1], p[2], p[3], p[4] ?? '', '', '', '']));
  s.hits.forEach(h => rows.push(['hit', iso(h.t), h.lat, h.lng, '', '', h.fish, h.size, h.memo]));
  return rows.map(r => r.map(v => `"${String(v??'').replace(/"/g,'""')}"`).join(',')).join('\r\n');
}
const fname = s => s.name.replace(/[\\/:*?"<>|\s]/g, '_') + '_' + new Date(s.start).toISOString().slice(0,10);
$('mExportGpx').onclick = () => {
  const s = latestSession(); if (!s || !s.points.length) { toast('書き出せる記録がありませぬ'); return; }
  download(fname(s) + '.gpx', toGpx(s), 'application/gpx+xml'); toast('GPXを書き出した(ダウンロード)');
};
$('mExportCsv').onclick = () => {
  const s = latestSession(); if (!s || !s.points.length) { toast('書き出せる記録がありませぬ'); return; }
  download(fname(s) + '.csv', toCsv(s), 'text/csv'); toast('CSVを書き出した(ダウンロード)');
};

// ---------- 一覧 ----------
$('mSessions').onclick = () => {
  const ix = store.index();
  $('listTitle').textContent = `記録一覧 (${ix.length}件)`;
  $('listBody').innerHTML = ix.length ? '' : '<div class="card">まだ記録がありませぬ</div>';
  ix.forEach(m => {
    const el = document.createElement('div'); el.className = 'card';
    el.innerHTML = `<b>${esc(m.name)}</b>
      <div class="sub">${fmtDate(m.start)}${m.end ? ' 〜 ' + fmtDate(m.end) : ' (記録中)'} ・ ${(m.dist/1000).toFixed(2)}km ・ 位置${m.ptCount}点 ・ 🎣${m.hitCount}</div>
      <div class="ops"><button data-op="show">地図に表示</button><button data-op="gpx">GPX</button><button data-op="del" class="warn">削除</button></div>`;
    el.querySelector('[data-op=show]').onclick = () => {
      const s = store.sess(m.id); if (!s) return;
      if (trackLine) map.removeLayer(trackLine);
      hitLayer.clearLayers();
      trackLine = L.polyline(s.points.map(p => [p[1], p[2]]), { color: '#27c46a', weight: 4 }).addTo(map);
      s.hits.forEach((h, i) => drawHit(h, i + 1));
      if (s.points.length) map.fitBounds(trackLine.getBounds(), { padding: [40, 40] });
      follow = false; $('btnFollow').classList.remove('on');
      closeSheet('listsheet'); closeSheet('menu');
    };
    el.querySelector('[data-op=gpx]').onclick = () => {
      const s = store.sess(m.id); if (s) download(fname(s) + '.gpx', toGpx(s), 'application/gpx+xml');
    };
    el.querySelector('[data-op=del]').onclick = () => {
      if (confirm(`「${m.name}」を削除しますか？(書き出し済みか確認を)`)) { store.delSess(m.id); $('mSessions').onclick(); }
    };
    $('listBody').appendChild(el);
  });
  closeSheet('menu'); openSheet('listsheet');
};
$('mHits').onclick = () => {
  const s = latestSession();
  const hits = s ? s.hits : [];
  $('listTitle').textContent = `ヒット一覧 (${hits.length}件)`;
  $('listBody').innerHTML = hits.length ? '' : '<div class="card">ヒット記録がありませぬ</div>';
  hits.forEach((h, i) => {
    const el = document.createElement('div'); el.className = 'card';
    el.innerHTML = `<b>🎣 #${i+1} ${esc([h.fish,h.size].filter(Boolean).join(' ') || '(未記入)')}</b>
      <div class="sub">${fmtDate(h.t)} ・ ${h.lat.toFixed(5)}, ${h.lng.toFixed(5)}</div>
      <div class="sub">${esc(h.memo || '')}</div>
      <div class="ops"><button data-op="go">地図で見る</button></div>`;
    el.querySelector('[data-op=go]').onclick = () => {
      map.setView([h.lat, h.lng], Math.max(map.getZoom(), 15));
      follow = false; $('btnFollow').classList.remove('on');
      closeSheet('listsheet'); closeSheet('menu');
    };
    $('listBody').appendChild(el);
  });
  closeSheet('menu'); openSheet('listsheet');
};

// ---------- 圏外用タイル保存 ----------
$('mTiles').onclick = async () => {
  if (IS_NATIVE) { toast('アプリ版では不要でござる(一度表示した地図は端末が自動保持)', 3500); return; }
  if (!('caches' in window)) { toast('この環境ではタイル保存に非対応'); return; }
  const zooms = [];
  const zNow = Math.round(map.getZoom());
  for (let z = Math.max(zNow - 1, 8); z <= Math.min(zNow + 3, 16); z++) zooms.push(z);
  const b = map.getBounds();
  const tiles = [];
  const t2 = (lat, lng, z) => {
    const n = 2 ** z;
    return [Math.floor((lng + 180) / 360 * n),
      Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n)];
  };
  for (const z of zooms) {
    const [x0, y0] = t2(b.getNorth(), b.getWest(), z), [x1, y1] = t2(b.getSouth(), b.getEast(), z);
    for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) tiles.push([z, x, y]);
  }
  if (tiles.length > 900) { toast(`タイル${tiles.length}枚は多すぎまする。地図を少し拡大してから再度どうぞ`, 4000); return; }
  toast(`海域地図を保存中… (${tiles.length}枚)`);
  const cache = await caches.open('fl-tiles-v1');
  let ok = 0;
  for (let i = 0; i < tiles.length; i += 6) {
    await Promise.all(tiles.slice(i, i + 6).map(async ([z, x, y]) => {
      const url = TILE_URL.replace('{z}', z).replace('{x}', x).replace('{y}', y);
      try {
        if (await cache.match(url)) { ok++; return; }
        const r = await fetch(url, { mode: 'cors' });
        if (r.ok) { await cache.put(url, r); ok++; }
      } catch (e) {}
    }));
  }
  toast(`海域地図を保存いたした (${ok}/${tiles.length}枚)。圏外でも表示できまする`, 4000);
};

// ---------- Wake Lock 手動トグル ----------
$('mWake').onclick = () => { if (wakeLock) { wakeWanted = false; releaseWake(); } else { wakeWanted = true; acquireWake(); } };

// ---------- 自己診断 (地図が出ない問題の切り分け用・位置情報は含めない) ----------
const DIAG_URL = 'https://ntfy.sh/tsurilog-diag-7c31';
async function runDiag(auto) {
  const r = { v: APP_VER, native: IS_NATIVE, ua: navigator.userAgent, online: navigator.onLine,
              errs: window.__diagErrs || [], leaflet: typeof L !== 'undefined',
              mapInit: typeof map !== 'undefined' && !!map, tileErrN, tests: {} };
  const tile = 'https://tile.openstreetmap.org/11/1817/806.png';
  // test1: <img> 読込 (Leafletと同じ経路)
  r.tests.img = await new Promise(res => {
    const im = new Image(); const t0 = Date.now();
    const done = ok => res(ok + ' ' + (Date.now() - t0) + 'ms');
    im.onload = () => done('OK'); im.onerror = () => done('FAIL');
    setTimeout(() => done('TIMEOUT'), 8000);
    im.src = tile + '?d=' + Date.now();
  });
  // test2: fetch 直
  try { const f = await fetch(tile + '?f=' + Date.now(), { cache: 'no-store' });
        r.tests.fetch = f.status + ' ' + f.type; }
  catch (e) { r.tests.fetch = 'ERR: ' + e.message; }
  // test3: 自サイト接続
  try { const f = await fetch('https://genai-daily.pages.dev/fishing/manifest.webmanifest?d=' + Date.now(), { cache: 'no-store' });
        r.tests.site = String(f.status); }
  catch (e) { r.tests.site = 'ERR: ' + e.message; }
  // test4: SW 状態
  try { r.tests.sw = 'serviceWorker' in navigator ? (await navigator.serviceWorker.getRegistrations()).length : 'none'; }
  catch (e) { r.tests.sw = 'ERR: ' + e.message; }
  const body = JSON.stringify(r);
  try { await fetch(DIAG_URL, { method: 'POST', body, headers: { Title: 'tsurilog-diag' } }); } catch (e) {}
  const short = `img:${r.tests.img} / fetch:${r.tests.fetch} / site:${r.tests.site} / sw:${r.tests.sw} / err:${r.errs.length}`;
  if (!auto) alert('診断結果(送信済)\n' + short + '\n' + r.errs.slice(0,3).join('\n'));
  else toast('🔧 診断送信済: ' + short, 6000);
}
if (IS_NATIVE) setTimeout(() => runDiag(true), 6000);

// ---------- 起動 ----------
if (IS_NATIVE) $('wakeState').textContent = '不要(アプリ版は画面OFF可)';
startWatch();
// 中断からの復帰
(() => {
  const act = localStorage.getItem('fl_active');
  if (!act) return;
  const s = store.sess(act);
  if (s && !s.end) {
    if (confirm('前回の記録が途中で終わっておりまする。再開しますか？\n(いいえ → そこで終了として保存)')) {
      S = s; beginTracking(true);
    } else { S = s; stopTracking(); }
  } else localStorage.removeItem('fl_active');
})();
// Service Worker
// SWはブラウザ版のみ(APK版は資産が端末内蔵ゆえ不要・残留キャッシュ事故防止)
if (!IS_NATIVE && 'serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');

window.__appLoaded = true;
