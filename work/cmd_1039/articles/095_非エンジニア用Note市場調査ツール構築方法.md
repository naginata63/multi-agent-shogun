# 非エンジニア用Note市場調査ツール構築方法

**URL**: https://note.com/sasuu/n/nab69a719f8f8

---

非エンジニア用Note市場調査ツール構築方 法

はじめに

必要なもの

構築手順

1. Googleスプレッドシートの作成

2. Google Apps Script（GAS）の設定

3. シート名の変更

5. スプレッドシートのレイアウト設定

6. データ取得機能の実行

7. データ取得の完了

トラブルシューティング

sasuu｜非エンジニアのAI活用術 2025年5月5日 21:30

目次 

すべて表示

はじめに

本記事では、NoteプラットフォームのAPIを活用して市場調査ツールを作成する方法を解説します。 GoogleスプレッドシートとGoogle Apps Script（GAS）を使用し、コーディング知識がなくても実装 できるように設計されています。

必要なもの

Googleアカウント

インターネット接続

構築手順

1. Googleスプレッドシートの作成

1. Googleドライブにアクセス

Google Driveにログイン

右クリックまたは「新規」ボタンをクリック

「Googleスプレッドシート」を選択

2. スプレッドシートの準備

ファイル名を「Note市場調査ツール」など分かりやすい名前に変更

2. Google Apps Script（GAS）の設定

1. スクリプトエディタを開く

スプレッドシートのメニューから「拡張機能」をクリック

「Google Apps Script」を選択

以下のコードをコピー

/** * スプレッドシートを開いたときに「調査」メニューを追加 */ function onOpen() { SpreadsheetApp.getUi() .createMenu('調査') .addItem('データ取得', 'analyzeNotes') .addToUi(); }

/** * B1 の検索キーワードを元に note API(v3) から指定件数までページングして取得し、

* 3行目から B〜J 列に出力する */ function analyzeNotes() { const ss = SpreadsheetApp.getActiveSpreadsheet(); const sheet = ss.getSheetByName('Competitors');

// B1 から検索キーワードを取得 const keyword = sheet.getRange('B1').getValue().toString().trim(); if (!keyword) { SpreadsheetApp.getUi().alert('B1 に検索キーワードを入力してください'); return; }

// 取得したい件数を指定（例：100件） const desiredCount = 100; // API の 1リクエストあたりの上限 const pageSize = 20;

// ページング用ループ let allNotes = []; let start = 0; let isLastPage = false; while (allNotes.length < desiredCount && !isLastPage) { const url = [ 'https://note.com/api/v3/searches', '?context=note', '&q=' + encodeURIComponent(keyword), '&size=' + pageSize, '&start=' + start ].join(''); const resp = fetchJson(url); const notes = (resp.data.notes && resp.data.notes.contents) || [];

allNotes = allNotes.concat(notes); isLastPage = resp.data.notes.is_last_page === true; start = resp.data.cursor.note;

// 最後のページまたは取得件数未満なら終了 if (notes.length < pageSize) break; }

// 指定件数に切り詰め const notesToProcess = allNotes.slice(0, desiredCount);

// like_count 降順ソート notesToProcess.sort((a, b) => b.like_count - a.like_count);

// 出力用２次元配列の生成 const values = notesToProcess.map(note => { // 日付フォーマット YYYY_MM_DD const rawDate = note.publish_at.split('T')[0]; const formattedDate = rawDate.replace(/-/g, '_');

// クリエイタ情報 (v2) 取得 const urlname = note.user.urlname; const creatorJson = fetchJson( 'https://note.com/api/v2/creators/' + encodeURIComponent(urlname) ); const followingCount = creatorJson.data.followingCount; const followerCount = creatorJson.data.followerCount;

// 記事URL を構成

コピーしたコードを、リンク先の動画の通りに貼り付けて保存ボタンをクリック

一度スプレッドシートを閉じて、再度開き直します。そうすることでメニューに「調査」項目が新 規追加されて表示されます。

const articleUrl = 'https://note.com/' + urlname + '/n/' + note.key;

// ハッシュタグ取得 (v3 note 詳細) const detailJson = fetchJson( 'https://note.com/api/v3/notes/' + encodeURIComponent(note.key) ); const tags = (detailJson.data.hashtag_notes || []) .map(h => h.hashtag.name) .join('、');

return [ note.user.name, // B列 followingCount, // C列 followerCount, // D列 note.name, // E列 articleUrl, // F列 `=IMAGE("${ note.eyecatch || '' }",4,158,300)`, // G列 formattedDate, // H列 note.like_count, // I列 tags // J列 ]; });

// 3行目から B〜J 列に書き込み if (values.length) { sheet.getRange(3, 2, values.length, values[0].length) .setValues(values); } }

/** * 指定 URL へ GET リクエストを送り、JSON を返すユーティリティ */ function fetchJson(url) { const res = UrlFetchApp.fetch(url, { method: 'get', headers: { 'Accept': 'application/json' }, muteHttpExceptions: true }); return JSON.parse(res.getContentText()); }

Gyazo Screen Video

Gyazo is the easiest way to record screenshots & videos y

gyazo.com

3. シート名の変更

1. シートタブの名称変更

スプレッドシート下部のシートタブを確認

必要なシート名をCompetitorsに変更：

5. スプレッドシートのレイアウト設定

画像の通り表の形を整える

6. データ取得機能の実行

1. 調査したいキーワードをB列2行目に入力しておく

1. カスタムメニューの操作

スプレッドシートに新しく表示された「調査」メニューをクリック

「データ取得」を選択

1. 認証プロセス

OKをクリック。

Googleドライブを使っているGoogleアカウントをクリック。

左下の「詳細」をクリック。

更に下に表示される「（安全ではないページ）に移動」をクリック。

1. 右上の「すべて選択」をクリック

2. 右下の「続行」をクリック。

以上で認証作業が完了です。

7. データ取得の完了

認証完了後、再度メニューから「調査」→「データ取得」をクリック。

スプレッドシートにデータが表示される（データ取得に1~2分かかります。）

以下のような警告が表示されます。右側にある「アクセスを許可」をクリック。 そうすることで取得したnoteのアイキャッチ画像が表示されます。

トラブルシューティング

よくある問題と解決策

1. 認証エラーが発生する場合

Googleアカウントの認証設定を確認

ブラウザのキャッシュをクリア

2. データが取得できない場合

APIキーが正しく設定されているか確認

ネットワーク接続を確認

3. スクリプトエラーが発生する場合

スプレッドシートIDが正しく入力されているか確認

シート名が正確に変更されているか確認

まとめ

このツールを使用することで、Noteプラットフォームの市場調査を効率的に実施できます。定期的な データ取得や分析に活用して、プラットフォームのトレンドを把握することが可能です。

コーディング未経験者でも手順に従えば簡単に実装できるため、デジタルマーケティングやコンテン ツ戦略の立案に役立ててください。

本ツールは2025年5月時点の情報に基づいています。APIの仕様変更等により、一部手順が変更される 可能性があります。

