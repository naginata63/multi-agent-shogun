# 非エンジニア向けDifyナレッジ Googleスプレッドシートの自動連携

**URL**: https://note.com/sasuu/n/n4f8d39694fb0

---

【非エンジニア向け】Difyナレッジ⇔ Google

スプレッドシートの自動連携

はじめに

DeFiナレッジとGoogleスプレッドシートを自動連携する方法について解説します。 この記事では、Google Apps Script（GAS）を使って、スプレッドシートの編集内容をDeFiに自動反映 させる方法を紹介します。

少しコードも含まれますが、手順通りに進めれば誰でも設定可能です。わからない箇所はChatGPTな どで補完しながら進めてください。

はじめに

第1章：やりたいことの全体像

1-1. 目的とゴール

1-2. 手順の概要

第2章：Dify側の準備

2-1. APIキーの取得

2-2. Difyナレッジのデータセットを作成

2-3. Difyナレッジのドキュメントを作成

sasuu｜非エンジニアのAI活用術 2025年6月1日 11:26

目次 

第3章：Google Drive・スプレッドシートの準備

3-1. フォルダとシートを作る

第1章：やりたいことの全体像

1-1. 目的とゴール

Difyでナレッジを管理したい

Googleスプレッドシートで管理している内容を自動でDifyナレッジへ登録

編集のたびにDifyナレッジへ反映される仕組みを作りたい

1-2. 手順の概要

1. DifyでAPIキー・データセット・ドキュメントを作成

2. Google Driveでスプレッドシートを用意

3. GAS（Google Apps Script）でコードを記述

4. トリガー設定でスプレッドシートの変更を検知

5. Difyに自動で同期

第2章：Dify側の準備

2-1. APIキーの取得

1. Difyのダッシュボードにログイン

2. 「APIキー」を発行してコピー

3. 後ほど使うため、メモしておく

DifyナレッジAPIキーを取得

すべて表示

2-2. Difyナレッジのデータセットを作成

1. Difyで新しいデータセットを作成

2. データセットIDをメモ

2-3. Difyナレッジのドキュメントを作成

1. 空のエクセルファイルを登録してドキュメントを作成

2. そのドキュメントIDをメモ

第3章：Google Drive・スプレッドシートの準備

3-1. フォルダとシートを作る

Google Driveで任意のフォルダを作成

フォルダ内に「空のGoogleスプレッドシート」を1つ作る

以下の画像のように1行目に・・・

1列目：No（番号）

2列目：item（商品名）

3列目：spec（商品仕様）

という形で表を作成してください。 （コードの仕様上1行目はヘッダーとして認識するようになっています）

スプレッドシートの表を作る

3-2. スプレッドシートIDをメモしておく

スプレッドシートを作成し終えたら、URLからスプレッドシートIDをメモしておく。

例： https://docs.google.com/spreadsheets/d/ここの部分がスプレッドシートのID/edit?gid=0#gid=0

3-3. スプレッドシートのシート名をメモしておく

スプレッドシートの画面下にあるシート名（「シート1」と書かれていることが多い）をメモしてお く。

第4章：スクリプトのプロパティを設定

4-1. スクリプトプロパティの入力

1. 左メニューの「歯車（プロジェクトの設定）」をクリック

2. 下にある「スクリプトプロパティ」から `＋追加` を選び、以下を設定：

4-2. スクリプトエディタを開く

1. スプレッドシートを開いた状態で、メニューから`拡張機能 > Apps Script` をクリック

1. エディタ画面が開いたら、以下のコードを貼り付けます

/** * Dify ✕ スプレッドシート同期スクリプト（コンテナバウンド＋デバウンス） * ------------------------------------------------------------------ * - 同じブックにバウンドしている前提。 * - onEdit で “30 秒後に一度だけ” sync() を実行するデバウンス方式。 * - 連続入力中は何度セルを確定しても sync は走らない。 * * ------------------------------ * 必須スクリプトプロパティ * ------------------------------ * API_KEY Dify の API キー * DATASET_ID Dify データセット ID * DOCUMENT_ID Dify ドキュメント ID * SHEET_NAME 対象シート名 * REQUEST_INTERVAL_MS (任意) Dify API 連続呼び出し間隔 ms 既定 800 * DEBOUNCE_MS (任意) onEdit から同期までの待機 ms 既定 30000 */

/* ---------------------------- * Utility * -------------------------- */ function trace(...msg) { const ts = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM- Logger.log(`[${ts}] ${msg.join(' ')}`); } function getProp(key, required = true) { const val = PropertiesService.getScriptProperties().getProperty(key); if (required && !val) throw new Error(`${key} is not set in script properties`); return val || ''; } function request(path, method, payload = null) { const API_ENDPOINT = 'http://dev-dify.myuuu.net/v1'; const API_KEY = getProp('API_KEY'); const res = UrlFetchApp.fetch(`${API_ENDPOINT}${path}`, { method, headers: { Authorization: `Bearer ${API_KEY}`, 'Content-Type': 'application/json muteHttpExceptions: true, ...(payload && { payload: JSON.stringify(payload) }) }); if (res.getResponseCode() !== 200) throw new Error(`${method} ${path} -> ${res.get return JSON.parse(res.getContentText()); }

/* ---------------------------- * Spreadsheet Helpers * -------------------------- */ function getTargetSheet() { const name = getProp('SHEET_NAME'); const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name); if (!sheet) throw new Error(`Sheet '${name}' not found`); return sheet; } function fetchSheetData() { const values = getTargetSheet().getDataRange().getValues(); const map = new Map(); for (let i = 1; i < values.length; i++) { const [no, q, a] = values[i].map(v => (v || '').toString().trim()); if (!no || !q) continue; map.set(no, { content: `"No","${no}","question","${q}","answer","${a}"`, answer: } return map; }

/* ---------------------------- * Dify Operations * -------------------------- */ function addSegment(content, answer = '') { if (!content.trim()) return; const payload = { segments: [{ content, answer, keywords: [] }] }; request(`/datasets/${getProp('DATASET_ID')}/documents/${getProp('DOCUMENT_ID')}/se } function listSegments() { return request(`/datasets/${getProp('DATASET_ID')}/documents/${getProp('DOCUMENT_I } function updateSegment(id, content, answer = '') { const payload = { segment: { content, answer, enabled: true } }; request(`/datasets/${getProp('DATASET_ID')}/documents/${getProp('DOCUMENT_ID')}/se } function deleteSegment(id) { request(`/datasets/${getProp('DATASET_ID')}/documents/${getProp('DOCUMENT_ID')}/se

1. コードを貼り付けたら、保存ボタン（💾）をクリック

2. 一度「実行」ボタンをクリック

保存 → 実行

}

/* ---------------------------- * Synchronization * -------------------------- */ function sync() { trace('=== sync start ==='); const WAIT = Number(getProp('REQUEST_INTERVAL_MS', false)) || 800; const sheetData = fetchSheetData(); const segments = listSegments();

segments.forEach(seg => { const m = seg.content.match(/"No","([^"]+)"/); if (!m) return; const no = m[1]; const row = sheetData.get(no); if (row) { if (seg.content !== row.content || (seg.answer || '') !== row.answer) updateSe sheetData.delete(no); } else { deleteSegment(seg.id); } Utilities.sleep(WAIT); });

sheetData.forEach(r => { addSegment(r.content, r.answer); Utilities.sleep(WAIT); } trace('=== sync done ==='); }

/* ---------------------------- * Debounce Triggers * -------------------------- */ /** * ユーザ編集時に呼ばれる。既存タイマーをリセットし、DEBOUNCE_MS 後に pendingSync() を実行。 */ function onEdit(e) { const FN = 'pendingSync'; // 既存の保留トリガーを削除 ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === FN).forEach( // 新たに時間駆動トリガーをセット const delay = Number(getProp('DEBOUNCE_MS', false)) || 30000; // デフォ 30s ScriptApp.newTrigger(FN).timeBased().after(delay).create(); } /** onEdit から遅延呼び出しされるラッパー */ function pendingSync() { sync(); }

この段階で認証を要求されるはずなので、以下の手順で認証を実施してください。

ポップアップが出るのでOKをクリック。

Googleドライブを使っているGoogleアカウントをクリック。

左下の「詳細」をクリック。

更に下に表示される「（安全ではないページ）に移動」をクリック。

1. 右上の「すべて選択」をクリック

2. 右下の「続行」をクリック。

これで認証は完了です。

第5章：自動連携を確認する

第4章までで設定作業は完了です！ ということで実際にスプレッドシートにデータを入力してみてください。

入力を終えてから30秒経つと自動連携処理が開始されて10秒くらいするとDifyのナレッジにデータが 同期されているはずです！

おわりに

これで、Googleスプレッドシートの編集がDifyナレッジに自動的に同期される仕組みが完成しまし た！

実務で使える連携フローを自分で構築できると、情報管理やAI学習用データの整備がぐっと楽になり ます。 ぜひ、ご自身でも試してみてください！

