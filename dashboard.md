# 📊 戦況報告
最終更新: 2026-04-09 06:30

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### 📋 漫画レビュー待ち
- **qnly_death v4**: https://youtu.be/Y7tm26PLPb0（P3リテイク済み）
- **お題漫画「あちらのお客様」**: http://192.168.2.7:8785/gallery_cmd1266.html（再生成中・OK/NGテロップP1左上のみ修正版）
- **お題漫画「私のために争わないで」**: http://192.168.2.7:8785/gallery_cmd1270.html（新規生成中）
- **bon_trick**: 再生成中（第2反復・P3/P6新名称版・足軽4作業中）

### 📋 総集編 — 殿の選定待ち
- 🐑 ピンク羊25件(15+10): https://youtu.be/obNdc44lqc0 追加候補: `work/cmd_1268_pink_sheep_additional.md` ⚠️合計475秒≈7分55秒（目標8分まで5秒差）
- 🎤 MEN迷言18件: https://youtu.be/MMh3Djlf8dE
- 🧊 おらふ名場面16件: https://youtu.be/LV4pY2O1tXs

### 🔧 夜間監査 2026-04-09 — STTパイプライン（CRITICAL 1 / HIGH 3 / MEDIUM 4）
- **CRITICAL**: `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py` L32 — PROJECT_DIR 1階層ズレ → `projects/projects/` の不完全声紋プロファイルを参照。話者識別精度低下の恐れ。修正: `.parent.parent.parent` → `.parent.parent.parent.parent`
- HIGH: `speaker_id_srt_based.py` L26 — MEMBERSリストハードコード（members.py未使用）
- HIGH: `vocal_stt_pipeline.py` L37 — sys.path未追加でModuleNotFoundError恐れ
- HIGH: `scripts/stt_merge.py.bak_1000` — 旧パス定義（誤復元でprofiles参照失敗）
- MEDIUM: --gemini廃止コード残存（2ファイル）/ subprocess capture_output欠落 / ロジック重複 他
- 詳細: `queue/reports/gunshi_report_nightly_audit_20260409_stt.yaml`

### 🔧 技術的残項目（優先度低）
- 漫画フォント30書体ギャラリー未選定: http://100.66.15.93:8783/work/font_comparison/

## 🔄 進行中（実行中のタスク）

| cmd | 内容 | 状態 |
|-----|------|------|
| cmd_1263_d | bon_trick全7パネル再生成（第2反復・P3/P6新名称） | 足軽4作業中 |
| cmd_1266_b | お題1「あちらのお客様」6枚再生成（テロップ修正版） | 足軽1作業中 |
| cmd_1270 | お題2「私のために争わないで」6枚新規生成 | 足軽2作業中 |
| cmd_1264_b | xlDFsyNm_eE STT再開（chunk_003 WhisperX→36分版完成） | 足軽3作業中 |
| cmd_1271 | srt_hotspot.py新規作成 + Layer4統合 | 足軽5作業中 |

## ✅ 本日の完了
| cmd | 内容 |
|-----|------|
| cmd_1269 | 夜間監査修正: pretool_check.shパス修正(4e16ead)/inbox_write dead code削除(e5985f4)/token.json追跡なし確認済み |
| cmd_1268 | ピンク羊追加候補10件発掘（合計25件・7分55秒） |
| cmd_1267 | qnly_death漫画ショートv4 YouTube非公開アップ |
| cmd_1266 | お題漫画「あちらのお客様」6枚生成 |
| cmd_1265 | 3総集編クリップ→YouTube非公開アップ |
| cmd_1264 | xlDFsyNm_eE STT完了（6名実名・323件） |
| cmd_1263 | qnly_death+bon_trick 漫画パネル14枚生成 |
| cmd_1258 | 中国系ショートパイプライン4機能追加 |
| cmd_1257 | 中国系ショート2本非公開アップ |
| cmd_1256 | ショート2本ffmpeg編集完了 |

## 足軽・軍師 状態

| 足軽 | CLI | 状態 | 現タスク |
|------|-----|------|---------|
| 1号 | Sonnet | 作業中 | subtask_1266b お題1再生成 |
| 2号 | Sonnet | 作業中 | subtask_1270a お題2新規生成 |
| 3号 | Sonnet | 作業中 | subtask_1264b STT再開 |
| 4号 | Sonnet | 作業中 | subtask_1263d bon_trick第2反復 |
| 5号 | Sonnet | 作業中 | subtask_1271a srt_hotspot.py |
| 6号 | Sonnet | idle | — |
| 7号 | Sonnet | idle | — |
| 軍師 | Opus | idle | — |

## APIキー状況
- **Vertex AI ADC**: ✅ 正常
- **GLM**: ⚠️ レート制限超過（リセット4/11）→ 足軽全員Sonnet切替済み

## チャンネル実績（2026-04-01更新）
- 登録者**1,007人** / 視聴回数**98.4万回** / 総再生時間**5,925時間**
- **収益化条件は未達**

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
