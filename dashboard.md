## 🎯 進行中
## 🎯 進行中

### cmd_1620 — Udemy中級編v4 赤章6章リライト [in_progress]
- ✅ ch05+ch06: 🟡×2 commit済 (75aa838) push指示中 → 軍師QC中
- ⏳ ch08+ch11: 足軽7号 作業中
- ⏳ ch13+ch16: 足軽1号 作業中

### cmd_1621 — Udemy初級編v4 全7章補修 [in_progress]
- ⏳ ch00+ch01: 足軽3号 作業中
- ⏳ ch02+ch05: 足軽5号 作業中
- ⏳ ch03+ch04+ch06: 足軽6号 作業中

## 🎯 進行中

### cmd_1620 — Udemy中級編v4 赤章6章 初学者向けリライト [in_progress]
- **担当**: 足軽2号(ch05+ch06) / 足軽7号(ch08+ch11) / 足軽1号(ch13+ch16) 並列実行中
- **注意**: .md が真ソース → .html を同期更新（修正指示配信済）

### cmd_1621 — Udemy初級編v4 全7章 補修 [in_progress]
- **担当**: 足軽3号(ch00+ch01) / 足軽5号(ch02+ch05) / 足軽6号(ch03+ch04+ch06) 並列実行中
- **目標**: 全7章🟢判定

## ⏸ 一時停止中

### cmd_1619 — ウィザー討伐v2 P4/P5/P7/P8 CDP生成 [blocked・殿判断待ち]
- PID kill済 (将軍対応)・既生成P1/P2/P3/P6 v2 PNG は images_chatgpt_cdp_wither/ に保持
- 今後方針: Gemini Imagen代替 / 別日再開 / 諦め → **殿判断待ち**

## 🎯 進行中

### cmd_1619 — ウィザー討伐v2 P4/P5/P7/P8 残4panel CDP再生成 [in_progress]
- **担当**: 足軽5号(CDP生成) → 軍師(QC) → 足軽1号(後処理)
- **進捗**: subtask_1619a (P4/P5/P7/P8生成) 足軽5号 着手中

### cmd_1620 — Udemy中級編v4 赤章6章 初学者向けリライト [in_progress]
- **目的**: ch05/06/08/11/13/16 の🔴(初学者お断り)判定を🟢/🟡に引き上げ
- **担当**: 足軽2号(ch05+ch06) / 足軽7号(ch08+ch11) / 足軽1号(ch13+ch16) 並列実行中
- **進捗**: 3グループ並列リライト → udemy-checker再レビュー → 全章PASS後に足軽2号が報告書作成

## ⏸ 一時停止中

(現在なし — cmd_1618 は cmd_1619 で引継ぎ処理中)

## ✅ 最近の完了

### cmd_1617 完了 (2026-05-04 軍師QC PASS)
- ウィザー討伐 8panel CDP/ChatGPT生成完了
- P04/P05: dozle変態仮面 / P07: bon起立・dozleシルエット OK
- gallery: http://192.168.2.4:8770/projects/dozle_kirinuki/work/20260504_リアルすぎる世界でウィザー討伐！【マイクラ】/images_chatgpt_cdp_wither/gallery.html

### cmd_1616 完了 (2026-05-04)
- ADbvr9TduZI 概要欄1行目「コイツはスケベに溢れとる！」キャッチコピー追加

### cmd_1615 完了 (2026-05-04 軍師QC PASS)
- 雪合戦縦型ショート YouTube非公開アップ完了
- YouTube URL: https://www.youtube.com/watch?v=ADbvr9TduZI (private)

### cmd_1614 完了 (2026-05-04 QC PASS)
- Discord AI NEWS復活

### cmd_1613 完了 (2026-05-04 FINAL QC PASS)
- STT audit 20件全修正 / **スキル化候補**: phased-audit-fix-with-interim-qc

## 🚨 要対応

### 🔄 cmd_1652完了 → server.py 再起動要 (殿/将軍 対応)

cmd_1652 (dashboard cancelボタン) の実装・py_compile PASS済 (commit be80269)。  
**server.py の再起動が必要** (新endpoint `/api/cmd_cancel` を有効化するため)。

```bash
pkill -f "python.*server.py" && sleep 1 && source ~/.bashrc && python3 /home/murakami/multi-agent-shogun/scripts/dashboard/server.py &
```

再起動後 → http://192.168.2.4:8770/ の pending/in_progress cmd 詳細ページに **🗑️ キャンセルボタン** が表示される。

### ❓ cmd_1647 v5 Phase1 進行中 → 事前4項目 殿確認待ち

cmd_1647 v5 Phase3 (章別執筆) を受領・Phase1 (事前4項目作成) を4足軽並列で起票済 (2026-05-06 05:08)。

| 足軽 | 担当 | subtask | 状態 |
|-----|------|---------|-----|
| ash1 | ch00-ch03 | subtask_1647_prewrite_ch00_ch03 | 進行中 |
| ash2 | ch04-ch06 | subtask_1647_prewrite_ch04_ch06 | 進行中 |
| ash3 | ch07-ch09 | subtask_1647_prewrite_ch07_ch09 | 進行中 |
| ash4 | ch10-ch11 | subtask_1647_prewrite_ch10_ch11 | 進行中 |

4足軽完了後、**事前4項目 (12章 × 対象問題/持ち帰り/ストーリー/実例) を殿にご確認いただきたい**。OK後にPhase2 (本文執筆) を起票する。

### ❓ cmd_1646完了 → A案SSE実装 cmd_1647a 起票 (殿判断待ち)

軍師による A案SSE設計 8軸QC完了 (2026-05-06 05:04)。殿が A案採用確定済。  
報告書: `queue/reports/2026-05-06_cmd_1646_a_design_qc.md`

**CRITICAL 抜け穴 5件 (実装前に要対処)**:
1. server.py = stdlib `ThreadingHTTPServer` (Flask非使用) — 設計コードはそのまま使用可
2. server.py 再起動で in-memory queue 全消失 → **SQLite Source of Truth + 接続初期化時に未読 push 必須**
3. Last-Event-ID 未実装 → msg_id を Event-ID として実装
4. feature flag なし deploy → **環境変数 `ENABLE_SSE_INBOX` 必須**
5. server.py 落ちで SSE 通知完全断絶 → systemd + 健全性 cron 必須

**Phaseロードマップ (最短3週間)**:
- Phase 1 (1-2日): server.py SSE endpoint 実装 → cmd_1647a
- Phase 2 (24h): gunshi 1agent 接続テスト
- Phase 3 (1週間観察): 全10agent 切替
- Phase 4 (別cmd): inbox_watcher.sh 廃止

**次アクション**: cmd_1647a (Phase1 実装) を起票するか、殿のご判断を仰ぎたし。

## 🚨 要対応

### 🚨 cmd_1639完了 → Phase 1 (cmd_1640) 起票判断

AnthropicエージェントAPI調査完了。推奨度サマリ:
- **S(即時)**: PushNotification (ntfy.sh置換候補) / MCP連携+Skill
- **A(中期)**: ScheduleWakeup / /loop dynamic / RemoteTrigger / Monitor (inotifywait置換) / Routines
- **B(長期)**: CronCreate(7日上限) / Background agents

**重要結論**: 既存ハーネスは成熟済 → 「置換」でなく「補完」戦略推奨

次アクション案 cmd_1640 (即時: PushNotification + ScheduleWakeup 先行実装) の起票を殿に判断を仰ぐ。
詳細: queue/reports/2026-05-05_cmd_1639_anthropic_agent_api_research.md

### 🚨 cmd_1638完了 → Udemy v5 Phase 3 (章別執筆) 起票判断

v5設計書10項目改訂完了 (860行)。Phase 3 (足軽による章別本文執筆) を起票するか殿判断を仰ぐ。
- レビューURL: http://192.168.2.4:8773/curriculum_intermediate_v5.html

## 🚨 要対応

### 🚨 cmd_1638完了 → Phase 3 (cmd_1639) 起票判断

v5設計書10項目改訂完了 (860行・受入条件19/19)。
Phase 3 (足軽による章別本文執筆) を起票するか殿判断を仰ぐ。
- レビューURL: http://192.168.2.4:8773/curriculum_intermediate_v5.html

### 📋 cmd_1636: DL完了。STT・字幕は後日
26本DL成功・7本既存SKIP・1本(QCFyL7tG-v4ライブ中)SKIP。
work/{YYYYMMDD}_{title}/input/ 命名規則で格納済。STT・字幕取得は後日別cmdで。

## 🚨 要対応

### 📋 cmd_1636: DL only 1並列実行中

**方針転換**: STT全面スキップ・字幕取得スキップ (IP BAN)。動画mp4 DLのみ1並列順次実行。
- 対象: 34本未DL + DL済5本(STT後日)
- ash1がsubtask_1636_dl_onlyを実行中
- sleep 5秒/本・HTTP429連続時は即停止
- 完了後: 字幕&STTは後日別cmdで実施

### 🚨 cmd_1638完了 → Phase 3 (cmd_1639) 起票判断

v5設計書10項目改訂完了 (860行・受入条件19/19)。
Phase 3 (足軽による章別本文執筆) を起票するか殿判断を仰ぐ。
- レビューURL: http://192.168.2.4:8773/curriculum_intermediate_v5.html

## 🚨 要対応

### 🚨 cmd_1638完了 → Phase 3 (cmd_1639 章別本文執筆) 起票判断

v5設計書 10項目改訂完了 (860行・受入条件19/19充足)。
**Phase 3 (足軽による章別本文執筆 cmd_1639想定) を起票するか殿判断を仰ぐ。**
- 軍師 non-blocking 観察3件: ch11 Skill実装難度バランス・ch04 Lazy Load比喩・ch07/ch11 Skill役割分担
- 詳細: queue/reports/2026-05-05_cmd_1638_v5_curriculum_revision.md §5-2
- レビューURL: http://192.168.2.4:8773/curriculum_intermediate_v5.html

## 🚨 要対応

### 📋 cmd_1638: 軍師 v5設計書10項目改訂中

軍師にsubtask_1638_v5_revision dispatch済み。殿の10項目レビュー指示に従いcurriculum_intermediate_v5_marp.mdを改訂中。
- 3層世界観スライド・Context Rot 3制約・Skills縦糸・逆引き辞典3段構造化 等
- 完了後: http://192.168.2.4:8773/curriculum_intermediate_v5.html で確認可能

## 🚨 要対応

### 🚨 cmd_1637完了 → Phase 2 (cmd_1638) 起票判断

v5詳細設計書 完成 (682行・5h35min・受入条件11/11)。
**Phase 2 (足軽による章別本文執筆 cmd_1638想定) を起票するか殿判断を仰ぐ。**
- 軍師の non-blocking 観察3件: ch09実例の質・橋渡しスライド最終言い回し・ch11題材調整
- 詳細: queue/reports/2026-05-05_cmd_1637_v5_curriculum_design.md §8-3
- レビューURL: http://192.168.2.4:8773/curriculum_intermediate_v5.html

## 🚨 要対応

### 🚨 cmd_1636: YouTube cookies.txt 手動配置が必要

**状況**: 18/57本完了。残39本がYouTube bot検出でDL blocked。cookies-from-browser全手法失敗(Chrome v11暗号化・firefoxプロファイルなし)。

**殿に必要なアクション**:
1. Chrome拡張「Get cookies.txt LOCALLY」(または同等) でyoutube.comのcookiesをエクスポート
2. ファイルを `/home/murakami/cookies_youtube.txt` に配置
3. 家老に「cookies配置完了」と通知

**配置後**: 家老がash1/2/3に `--cookies /home/murakami/cookies_youtube.txt` で再dispatch

### 🚨 cmd_1637完了 → Phase 2 (cmd_1638) 起票判断

v5詳細設計書 完成 (682行・5h35min・受入条件11/11)。
**Phase 2 (足軽による章別本文執筆 cmd_1638想定) を起票するか殿判断を仰ぐ。**
- 軍師の non-blocking 観察3件: ch09実例の質・橋渡しスライド最終言い回し・ch11題材調整
- 詳細: queue/reports/2026-05-05_cmd_1637_v5_curriculum_design.md §8-3
- レビューURL: http://192.168.2.4:8773/curriculum_intermediate_v5.html

## 🚨 要対応

### 🚨 cmd_1636: YouTube cookies.txt 手動配置が必要

**状況**: 18/57本完了。残39本がYouTube bot検出でDL blocked。cookies-from-browser全手法失敗(Chrome v11暗号化・firefoxプロファイルなし)。

**殿に必要なアクション**:
1. Chrome拡張「Get cookies.txt LOCALLY」(または同等) でyoutube.comのcookiesをエクスポート
2. ファイルを `/home/murakami/cookies_youtube.txt` に配置
3. 家老に「cookies配置完了」と通知

**配置後**: 家老がash1/2/3に `--cookies /home/murakami/cookies_youtube.txt` で再dispatch

**GZ1O6k1Fe3A** (649MB mp4・demucs済み) はcookies不要 → STTのみ再試行可

### 📋 cmd_1637: 軍師 v5詳細設計書作成中

軍師にsubtask_1637_v5_curriculum dispatch済み。curriculum_intermediate_v5_marp.md 生成待ち。

## 🚨 要対応

### 🍪 YouTube DL完全ブロック — 殿の手動操作が必要 (2026-05-05 17:20)

**ash1が試した6手法すべて失敗**:
1. `--cookies-from-browser chrome` → Chrome v11暗号化解除不可 (2436/2439件複号失敗・GUIセッションなし)
2. `--cookies-from-browser firefox` → プロファイル不存在
3. gdown cookies.txt → YNID 1件のみ不十分
4. deno/node JS runtime → LOGIN_REQUIRED
5. yt-dlp 2026.5.3 nightly → 同一エラー
6. 全player_client (ios/mweb/tv/web/android_vr) → 全LOGIN_REQUIRED

**根本原因**: Ubuntuサーバーにデスクトップセッションなし + Chrome v11暗号化がCLI環境で解除不可

**殿に必要な操作 (2択)**:

#### 選択肢A: cookies.txt手動エクスポート (推奨)
1. Windows/Mac の Chrome (YouTube ログイン済み) で拡張機能「Get cookies.txt LOCALLY」をインストール
2. youtube.com でcookies.txtをエクスポート
3. サーバーの `/home/murakami/cookies_youtube.txt` に配置
4. 家老に「cookies配置完了」と通知 → ash1-3 に `--cookies /home/murakami/cookies_youtube.txt` でリトライ dispatch

#### 選択肢B: 時間待ち
- YouTube IP制限は数時間〜数日で解除される場合あり
- 現在 16/56 完了 (ash4 が 11本成功) → 残 40本待機

**現在の状況**:
- ash1: blocked (retry1全失敗)
- ash2/3: 停止指示済み・cookies配置待ち
- ash4: 11/14成功・2本(o6vunreR_yM/qFpCsQhwxwQ)は状況不明
- ash5: fullbatch1-4完了待ち (blocked)

## 🚨 要対応

### 🤖 YouTube bot検出 — 殿の判断要 (2026-05-05 16:30)
**概要**: cmd_1636 4並列一斉DLがYouTube bot判定を受け、39本のDLが不可に

**現在の進捗 (56本中)**:
| バッチ | 担当 | 成功 | 失敗 |
|--------|------|------|------|
| B1 | ash1 | 4/14 (IKu8Dad0YyY等) | 10本 (GZ1O6k1Fe3A含む) |
| B2 | ash2 | 1/14 (FtPg-vcyH7I) | 13本 |
| B3 | ash3 | 0/14 | 14本 |
| B4 | ash4 | 11/14 | 2本 |
| **計** | | **16/56** | **39本** |

**失敗理由**:
- 4並列同時DLがYouTubeのbot検出を誘発
- GZ1O6k1Fe3A: AssemblyAI timeout (649MB長尺・別問題)
- その他: `ERROR: Sign in to confirm you're not a bot`

**解決策 (殿の判断を仰ぐ)**:
1. **cookies-from-browser追加**: downloader.pyに`--cookies-from-browser chrome`を追加し再試行 (Chromeのログイン状態を使用)
2. **間隔を空けてリトライ**: 1並列に減らしてシリアル実行 (bot検出回避)
3. **時間をおいて再試行**: IP制限が解除されるまで待機

**ash2/3/4の完了報告を待ち中。報告後に対応策を確定する。**

## 🚨 要対応

**（2026-05-05 15:40 更新）Gemini API誤報訂正**: 将軍が build --update 直接実行で正常完了確認。scene_search_v2はVertex AI ADC認証使用・GEMINI_API_KEYは未使用。前回の🚨Gemini APIキー期限切れ警報は誤認だったため取り消し。

## 🚨 要対応

### 🔑 GEMINI APIキー期限切れ (2026-05-05)
- **現象**: `google.genai.errors.ClientError: 400 INVALID_ARGUMENT. API key expired.`
- **影響**: scene_search_v2 build --update が全面停止。cmd_1636 の index 追加フェーズが blocked
- **対応**: 殿が GEMINI_API_KEY を更新 → `source ~/.bashrc` → 家老に通知
- **暫定処置**: video-pipeline (DL+Demucs+STT) は継続可。index 追加は API 更新後

### 📊 cmd_1636 進捗 (2026-05-05 15:30+)
- ash1-4: 4並列直接 dispatch 完了・各自処理中
- ash1: IKu8Dad0YyY 完了確認
- ash2: T-vKXTT7b8M (旧stepA2) + FtPg-vcyH7I + _0HIJZdn94A 処理中
- ash3: BcPWm_mCpp4 処理中
- ash4: QMpQZbUTfj4 処理中
- RAM 37GB available / Swap=0 / GPU 1335MB/8188MB (正常)
- ash5 (index2): GEMINI API更新待ちで blocked

## 🚨 要対応

### [2026-05-05] Gemini APIキー期限切れ
- **影響**: scene_search_v2.py build (embedding生成) が全停止
- **cmd_1631**: index部分不完全 (xZTtk4pJcAs words: 5/434のみembedded)
- **cmd_1636**: 56本 indexing ステップ実行不可
- **対策**: vocal_stt_pipeline (AssemblyAI+Deepgram) は継続 → DL+STT先行処理中
- **要対応**: GEMINI_API_KEY更新後に家老へ通知 → index再構築を即実行

## 🚨 要対応

### [2026-05-05] Gemini APIキー期限切れ
- **影響**: scene_search_v2.py build (embedding生成) が全停止
- **cmd_1631**: index部分不完全 (xZTtk4pJcAs words: 5/434のみembedded・chunks: 1/85のみ)
- **cmd_1636**: 56本 indexing ステップ実行不可
- **対策**: vocal_stt_pipeline (AssemblyAI/Deepgram/ECAPA-TDNN) は継続可 → DL+STT先行処理中
- **要対応**: GEMINI_API_KEY を更新次第、家老に通知せよ → index再構築ジョブを即実行する

## 🚨 要対応

*(現在 要対応なし)*

## 🚨 要対応

### [cmd_1631/1632] scene_search_v2.py 未作成 + scene_index_v2 stale 25本 (2026-05-05 家老調査)

**発見**: cmd_1631/1632 の AC が前提とする `scene_search_v2.py` は **未作成**。かつ scene_index_v2 metadata に深刻な staleness を確認。

**実態**:
- merged JSON 違反: **1本のみ** (xZTtk4pJcAs — A/B/C/D/E/F 混在)
- scene_index_v2 metadata 違反: **26本** (うち 25本は merged JSON 修正済みだが index 未再構築)
- `scene_search_v2.py` は context ファイルに記載あるが scripts/ に存在しない

**問題**: cmd_1631 AC #4 「scene_search_v2.py info の話者一覧から A-F が消えている」は xZTtk4pJcAs 1本を直しても満たせない (25本分が残る)

**選択肢** (殿ご判断をお願いします):
- **(A) スコープ限定**: cmd_1631 は xZTtk4pJcAs 再STT + scene_search_v2.py 新規作成のみ。AC #4 を「xZTtk4pJcAs 分の A-F 消失」に緩和。stale 25本は別 cmd (index 全 rebuild) で後日対応
- **(B) スコープ拡張**: cmd_1631 を xZTtk4pJcAs 再STT + scene_index_v2 全 rebuild (25本分 stale 解消) まで含める
- **(C) 分割**: cmd_1631 は xZTtk4pJcAs 限定。別 cmd_1633 で scene_index_v2 全 rebuild

**現在の状態**: cmd_1631/1632 はタスク未起票。殿の選択後に着手。

## 🚨 要対応

（現在、殿の判断を要する案件はありません。cmd_1622 R3アラートはcmd_1630で対応中）

## 🚨 要対応

### cmd_1621: beginner ch05 🟡 2回リトライ上限到達
- ch05「Hookの入門」が v1/v2/v3 の3回レビューすべて🟡
- acceptance_criteria は全章🟢必須 (🟡禁止)
- 残指摘: exit 0/2の意味・$1の説明・grep -q パイプの意味不明瞭
- **殿判断**: A) ch05は🟡で例外許容 / B) もう1回補修許可 / C) 🟡でcmd_1621完了と見なす

### cmd_1621: beginner ch03 🟡 — 補修中
- ch03は🟡 (ashigaru6が3回目補修中)
- こちらは上限未到達・継続作業中

### phased-audit-fix-with-interim-qc スキル化候補 (旧)
- A: スキル化する / B: 見送り — 殿判断待ち

### cmd_1618 殿選定待ち
- ウィザー討伐漫画 P4/P5/P7/P8 再開方針: A)CDP再開 / B)Gemini Imagen / C)諦め

## 📊 進行中 cmd
## 📊 進行中 cmd

### ✅ cmd_1620 完了 — 中級編v4赤章6章リライト
- 2026-05-04 23:04 完了
- 全6章 🟡/🟢 達成: ch05🟡/ch06🟡/ch08🟡/ch11🟡/ch13🟡/ch16🟢
- 完了報告書: queue/reports/2026-05-04_cmd_1620_intermediate_v4_red_chapter_rebuild.md
- git push 済 (origin/main 43cdc6e)
- 殿レビューURL: http://192.168.2.4:8773/lectures/intermediate_v4_ch05_context_economics.html

### cmd_1621 進行中 — 初級編v4全7章補修
- ch00🟢✓ / ch01🟢✓ (subtask_1621_ch00_01 done)
- ch02🟡→🟢へ再補修中 / ch05🟡→🟢へ再補修中 (ashigaru5)
- ch03 commit済 / ch04作業中 / ch06作業中・温存 (ashigaru6)
- 注意: 全7章🟢必須 (🟡不可)
- 残: ch02/ch03/ch04/ch05/ch06の🟢達成待ち

### cmd_1619 停止中 — ウィザー討伐漫画P4/P5/P7/P8
- 殿命令でCDP生成停止済
- 再開方針は殿判断待ち

## 📊 進行中 cmd

### cmd_1620 — 中級編v4 赤章6章リライト
- 状態: **report作成中** (ashigaru2が完了報告書+git push+ntfy担当)
- ch05🟡 / ch06🟡 / ch08🟡 / ch11🟡 / ch13🟡 / ch16🟢 — 全章acceptance_criteria充足
- 次: subtask_1620_report (ashigaru2) → git push → ntfy → cmd_1620完了

### cmd_1621 — 初級編v4 全7章補修
- 状態: **3足軽並列作業中** (ch00/01=ashigaru3, ch02/05=ashigaru5, ch03/04/06=ashigaru6)
- ch00🟢 / ch02🟡→再補修中 / ch03✅commit / ch05🟡→再補修中
- ch01/ch04/ch06はまだ作業中
- 注意: cmd_1621 acceptance_criteriaは全章🟢必須 (🟡禁止)

### cmd_1619 — ウィザー討伐漫画P4/P5/P7/P8 (停止中)
- 殿命令でCDP生成停止済 (2026-05-04 21:30)
- 既生成: P1/P2/P3/P6 v2のみ
- 再開方針は殿判断待ち

## 🔧 技術負債 / 矛盾検出
## 🔧 技術負債 / 矛盾検出

### cmd_1623 動画制作スクリプト矛盾検出 (2026-05-05)
- **findings**: H=1 / M=9 / L=12 (計22件)
- **H1 最重要**: `main.py:164-217` `render_with_remotion()` が参照する Remotion パスは `remotion-overlay/` だが cmd_1623 指定は `remotion-project/` — **完全不一致・後続cmd修正必要**
- M件: make_expression_shorts.py import未使用3件・vertical_convert.py ハードコードパス2件 等
- 報告書: `queue/reports/2026-05-05_cmd_1623_mujun_detection.md`
- 推奨 follow-up cmd 6件 (報告書末尾参照)

## 📋 進行中
## 📋 進行中

| cmd | project | status | 内容 |
|-----|---------|--------|------|
| cmd_1622 | udemy_course | in_progress | 中級編v4全21章補修 — appendix_abc (ashigaru7) 完了待ち |
| cmd_1625 | multi-agent-shogun | in_progress | dashboard_lifecycle.sh cron環境exit非0 根本調査・修正 (ashigaru1) |
| cmd_1626 | dozle_kirinuki | in_progress | cmd_1623矛盾検出H1+M1-M9解消 — main.py (ashigaru2) + vertical_convert.py+doc (ashigaru3) |

### 完了（本日）
- **cmd_1624** ✅ gunshi inbox蓄積ループ対策 (案A: ashigaru.md gunshi_qc:falseルール + 案B: stop_hook古unread2時間自動既読化) — commit 2d61122 push済
- **cmd_1623** ✅ 夜間矛盾検出 — H=1/M=9/L=12 (22件) — 報告書: queue/reports/2026-05-05_cmd_1623_mujun_detection.md

## 🚀 進行中
## 🚀 進行中

（現在進行中のcmdはありません）

## 🚀 進行中

### cmd_1630: 中級編 v4 appendix_a/b/c 🟢化 + cmd_1622完了処理 (2026-05-05)
- 目的: appendix_a/b/c を補修→udemy-checker再レビュー🟢化し、cmd_1622全章をpush・殿レビューへ
- 足軽1: subtask_1630_appendix_a (appendix_a 補修+🟢化)
- 足軽2: subtask_1630_appendix_b (appendix_b 補修+🟢化)
- 足軽3: subtask_1630_appendix_c (appendix_c 補修+🟢化)
- 足軽7: subtask_1630_finalize (完了報告書2件 — blocked待機中)
- 完了後: 家老がgit push → dashboard更新 → ntfy送信

### cmd_1622: 中級編 v4 全21章 🟢化 (2026-05-04)
- 補足: appendix_a/b/c補修はcmd_1630に移管。ch00-18は全🟢完了

## ✅ 最近の戦果
## ✅ 最近の戦果

### cmd_1632 完了 (2026-05-05 14:00)
- dozle_video_list.csv 最新化 + quality_status列追加 + audit_video_index_consistency.py 新規作成
- Audit: ok=66 / violation_alphabet=1(xZTtk4pJcAs) / index_missing=10362
- 4/2以降未処理57本リスト化済み
- 報告書: queue/reports/2026-05-05_cmd_1632_video_index_audit.md

### cmd_1630 完了 (2026-05-05 12:30)
- Udemy 中級編 appendix_a/b/c 全3章 🟢 補修完了
- 報告書: queue/reports/2026-05-05_cmd_1630_intermediate_appendix_completion.md

## ✅ 最近の戦果

### cmd_1630 完了 (2026-05-05)
- Udemy 中級編 appendix_a/b/c 全3章 補修完了・全て 🟢
- 報告書: queue/reports/2026-05-05_cmd_1630_intermediate_appendix_completion.md

## ✅ 最近の戦果

### cmd_1630 完了 (2026-05-05)
- Udemy 中級編 appendix_a/b/c 全3章 補修完了・全て 🟢
- appendix_b は4回レビューの末 🟢 達成
- 報告書: queue/reports/2026-05-05_cmd_1630_intermediate_appendix_completion.md
- cmd_1622 全21章 🟢 一覧: queue/reports/2026-05-04_cmd_1622_intermediate_v4_all_green.md

### cmd_1631/1632 起票済み (2026-05-05)
- cmd_1631: xZTtk4pJcAs 完全再STT → ash4(stt) ash5(index) ash7(report)
- cmd_1632: dozle_video_list.csv 最新化 + audit script → ash1(csv) ash2(audit) ash3(report)

## 進行中
## 進行中

### cmd_1636 (4並列video-pipeline + scene_search_v2 index)
- **状況**: ash1-4 全員4並列フル稼働中 (2026-05-05 15:30+)
- ash1: IKu8Dad0YyY 完了後、次動画へ
- ash2: FtPg-vcyH7I → _0HIJZdn94A と処理中 (T-vKXTT7b8Mはstepで先行完了)
- ash3: BcPWm_mCpp4 処理中
- ash4: QMpQZbUTfj4 処理中
- ash5 (index2): fullbatch1-4完了後に build --update 実行予定
- **将軍cmd_correction受領確認** (msg_20260505_154028): A/B/C対応完了
  - A) cmd_1631: done確認済 (建前でdone更新済だが実際はash5が完了・将軍建前実行でも確認)
  - B) index2ブロック解除: GEMINI_API_KEY確認ステップ削除済・Vertex AI ADC認証明記
  - C) 誤認防止memory追記済 (feedback_scene_search_v2_auth.md)
- **現在 n_videos=68** (将軍15:28確認) → 目標~124
- RAM 37GB available / Swap=0 / GPU稼働中

## 🔍 夜間矛盾検出
## 🔍 夜間矛盾検出

### cmd_1641 インフラ系 (2026-05-06 02:08完了)

**検出: H5 / M9 / L6 = 計20件** ([報告書](queue/reports/2026-05-06_cmd_1641_infra_mujun.md))

| ID | 重要度 | 内容 | 修正コスト |
|----|--------|------|------------|
| H1 | HIGH | ntfy.sh L26-27: Tailscale IP二重置換が同一IPでno-op (typo疑い) | 1行・5分 |
| H2 | HIGH | inbox_watcher.sh L204: disable_normal_nudge 戻り値が反転(可読性低下) | 確認必要 |
| H3 | HIGH | inbox_write.sh: Python venv yaml依存がcritical path・単一障害点 | 中期対応 |
| H4 | HIGH | inbox_watcher.sh L62-68: _EFFECTIVE_CLI glm→claude強制でdrift WARN flood | 要確認 |
| H5 | HIGH | stop_hook_inbox.sh: cmd_1100 ハードコードwatermarkが時代遅れ | 軽微 |

M/L 各詳細は報告書参照。
