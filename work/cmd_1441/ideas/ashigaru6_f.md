# 足軽6号アイデア出し（動画系積残 / f カテゴリ）

cmd_1441 Phase A 足軽6号担当分。Day6 4視点MIX・過去DoZ未消化・TNT漫画ショート・on_hold案件・disk圧迫の具体策。
作成: 2026-04-24 13:35 / ashigaru6
関連: 将軍 5-A(video積残), 軍師 J(横断), 足軽3_c(file蓄積整理と重複関心)

---

## 1. 現状（定量ベースライン）

Phase B 統合で効果測定の基準値。

### 1-1. Day6 4視点素材（20260416_6日目_oo_men視点フォルダ）

| 視点 | ファイル | 本数 | codec | 合計尺 | 1パート代表サイズ | 備考 |
|------|----------|------|-------|--------|-------------------|------|
| oo_men | `t7JJlTDACyc_part_00〜09.mp4` | 10 | **h264** | 32,508秒(≒9h01m) | — | 公式動画DL済・ja.srt 同梱 |
| tsurugi | `multi/day6_tsurugi_part_00〜08.mp4` | 9 | **h264** | ≒7h22m | 2,653MB | cmd_1425で集約済 |
| hendy | `multi/day6_hendy_part_00〜08.mp4` | 9 | **h264** | ≒7h28m | 2,652MB | cmd_1425で集約済(Twitch 2749323185) |
| charlotte | `multi/day6_charlotte_part_00〜08.mp4` | 9 | **vp9** | ≒8h59m | 1,269〜1,391MB | cmd_1425で集約済(v19JAnVjZ_c) / **codec異質** |

- **cmd_1425 part_info.json の注記「oo_men_parts.jsonが存在しないため3視点のみ」は誤解を招く**。oo_men視点は同フォルダ root に `t7JJlTDACyc_part_*` として存在する（`multi/` は3視点専用の集約ディレクトリという運用）。
- **尺ズレあり**: 4視点間で ±1.5時間の差。MIX時は「誰の時刻に合わせるか」基準設計が要る。

### 1-2. DoZ 過去編（未消化素材の物量）

| フォルダ | サイズ | 視点 | 備考 |
|----------|--------|------|------|
| 20260416_6日目 | **107G** | oo_men+3視点multi | 本cmd対象 |
| 20260412_2日目 | 55G | oo_men視点 | 未消化 |
| 20260415_5日目(original) | 48G | oo_men | 20260417と重複 |
| 20260413_3日目 | 38G | oo_men | 未消化 |
| 20260417_5日目(oo_men) | 25G | oo_men+clip多数 | **cmd_1412 on_hold** / panels 7種散在 |
| 20260411_Day1 | 22G | oo_men | 未消化 |
| 20260418_8日目 | 18G | oo_men | 未消化 |
| 20260417_7日目 | 16G | oo_men | 未消化 |
| **合計(DoZ系8フォルダ)** | **329G** | — | **dozle_kirinuki/work 全体 514G の 64%** |

### 1-3. TNT（20260421）漫画ショート未消化

`20260421_TNTしか使えない世界でエンドラ討伐/` 配下:
- クリップ3本: `clip_960_1080.mp4`(cmd_1426で抽出済/120秒), `clip_enderman.mp4`, `clip_asobunokinshi.mp4`
- `manga_960_1080/`: panels_960_1080.json / _edited / _edited_v2 / _shogun_v3 / _shogun_v3_edited（7バリアント）、output/ に v1-v3 + p1_retry1/2 **完成動画未確認**
- `manga_asobunokinshi/`: panels_asobunokinshi.json 系 8バリアント、output/ は men_retry×3/orafu_retry×2 のみ **完成動画未確認**

### 1-4. 20260417_5日目_oo_men の panels バリアント散在

`panels_doz_healer_*.json` 系統 11種:
`panels_doz_healer.json` / `_raw.json` / `_20min.json` / `_20min_raw.json` / `_15931_16231.json` / `_15931_16231_raw.json` / `_16231_16531.json` / `_16231_16531_raw.json` / `_tono_edit.json` / `_tono_edit (コピー).json` / `_tono_edit_raw.json`
- 残存clip: `clip_14889_15489 / 14889_16089 / 15309_15489 / 15331_15631 / 15331_16531(717M/cmd_1413採用) / 15631_15931 / 15931_16231 / 16231_16531 / 2138_2318_invalid / full.mp4`

### 1-5. disk 圧迫

- `/dev/sdb4`: **796G used / 116G 残 / 88%**（dashboard警告）
- `projects/dozle_kirinuki/work/` 単独で **514GB**（全体の64%）
- Day6 4視点MIX 再エンコード（charlotte vp9 → h264 変換）中間出力で +8〜12GB追加必要見込み

### 1-6. on_hold / 未判断

| cmd | status | 内容 |
|-----|--------|------|
| cmd_1412 | **on_hold** | DoZ5日目20分版の非公開アップ。殿判断待ち（10分版残置しつつ長尺レビュー用）|
| cmd_1411/1413/1414 | (dashboard上) done化済 | 殿判断反映済 |

---

## 2. やれてないこと

| # | 未対応事項 | 放置コスト |
|---|-----------|-----------|
| N1 | Day6 4視点MIX本体（charlotte vp9 + h264 3視点 → concat -c copy **不可**・再エンコード必須）| disk 8〜12GB追加 + NVENC所要時間数時間 / 実装ゼロだと殿の「4視点MIX見たい」待ちが解消しない |
| N2 | 過去DoZ編（Day2/3/5/7/8）の HL/SH候補選定が全て未実施 | 329GB の素材が塩漬け。今週 MCN 申請動線検討と足並みが揃わない |
| N3 | TNT 20260421 漫画ショート2本（960_1080 / asobunokinshi）が完成動画未アップ | クリップ・panels・retry成果物は揃っているが最終合成が止まっている |
| N4 | 20260417 panels 11バリアント + clip 10本の棚卸し・剪定 | 次cmd発令時に「どれが本採用か」が不明。殿判断（cmd_1413=採用/cmd_1411=却下）の結果が個別削除に反映されていない |
| N5 | cmd_1412 on_hold 案件の殿判断再提示動線がない | 1週間 on_hold 固定（timestamp 2026-04-18 → 本日 2026-04-24）。Phase A 棚卸しで浮上した以上 Phase B で判断要件を明示すべき |
| N6 | work/ 514GB のアーカイブ戦略未定（外付けHDD退避 or 中間ファイル削除基準） | disk 88% は Day6 MIX 実行の blocker。足軽1号 a カテゴリで disk 88% は別途上がっているが、動画系視点の削減候補リストは未提出 |
| N7 | 「完成動画が YouTube 非公開にアップ済か」の横断確認リストなし | upload.log が個別フォルダ散在。殿が「アップまだ？」と訊ねたとき即答できない |
| N8 | Day6 以外の4視点素材（過去 DoZ）はそもそも3視点DLすらしていない | MCN 申請後の「4視点MIX専門チャンネル」展開の下地が皆無 |

---

## 3. アイデア（8案・3軸ラベル付）

軸: 緊急度 = 今夜 / 今週 / 来月以降 | コスト = LOW(<10分) / MED(30分〜2時間) / HIGH(半日以上) | 効果 = QoL / 視聴者価値 / 事故防止

| # | アイデア | 緊急度 | コスト | 効果 | 根拠・具体実装 | 依存/注意 |
|---|---------|--------|--------|------|---------------|-----------|
| **F-1** | **charlotte vp9 → h264_nvenc 先行トランスコード（4視点codec統一）** | 今週 | MED | 視聴者価値 | Day6 4視点MIX の blocker は charlotte のみvp9。MIX実行前に `multi/day6_charlotte_part_*.mp4` を h264_nvenc(p4 CQ=23, 1080p維持) で事前変換→別ディレクトリ保存。これで4視点とも h264 になり、以降の MIX は `ffmpeg -filter_complex hstack/vstack` や `multi_view_sync.md` 手順にのれる。**中間生成物必須保存**（CLAUDE.md Intermediate Artifact Rule）| disk +8〜12GB 確保が先。F-6と順序性あり |
| **F-2** | **過去DoZ編 HL/SH 候補一括選定（集合知スキル `/collective-select` バッチ）** | 今週 | HIGH | 視聴者価値 | Day2/3/5/7/8（5本・oo_men視点のみ）を `/collective-select` でHL候補+SH候補を一気に選定。1本あたり30〜45分 × 5本 = 2.5〜4時間。SRT はDL済（t*_part*.ja.srt or フォルダ内）。成果物: `work/cmd_1441/phaseB_hlsh_selection/{day}.json` | batch_safety: 集合知LLM呼出は1本ずつ（並列禁止）。cmd_1441 Phase B 用の下地データになる |
| **F-3** | **TNT 20260421 漫画ショート2本を /manga-short で完走** | 今夜 | MED | 視聴者価値 | panels_960_1080_shogun_v3_edited.json / panels_asobunokinshi_shogun_v3_edited.json の2本は「shogun_v3_edited」= 殿編集済み最終版。`/manga-short` 工程（panels_check.html確認済ならすぐ合成可）で output MP4 生成 → 非公開アップ。新規.py禁止ルール内で既存スキル完走のみ | tono_edit.mkv(縦型素材)/tono_edit_vertical.mp4 がフォルダ内に存在する点は確認済み（合成時入力）|
| **F-4** | **work/ 退避候補リスト作成（disk 514GB → 300GB目標）** | 今週 | LOW | 事故防止 | md で「**完了動画のraw parts(t*_part_*.mp4)** と **没clip** を退避候補として列挙」。外付けHDD or 別ドライブ退避の判断は殿に委ねる。具体候補: (a)20260412-15/17-18 の `t*_part_*.mp4` = DL済み・アップ済動画の原本（合計270GB）, (b)20260417 の `clip_2138_2318_invalid.mp4` `clip_15309_15489.mp4` 等 cmd_1411/1413 で却下された中間clip | Intermediate Artifact Rule との整合: STT/panels JSON は残す。raw parts のみ退避対象 |
| **F-5** | **cmd_1412 on_hold 再提示テンプレ（殿判断要件を明示）** | 今夜 | LOW | 運用改善 | work/cmd_1441/phaseB_decisions/cmd_1412_recheck.md を新設。内容: (a)10分版s8vF-lVpiRwの再生数/CTR/平均視聴時間を generate_dashboard.py から抽出, (b)20分版アップ後の期待効果シナリオ3案, (c)殿判断の選択肢(1)アップのみ(2)10分版差替(3)20分版cancel。dashboard 🚨要対応 に項目追加（家老に依頼） | 殿判断依存。アイデア出しの本義である「Phase B で判断」に合致 |
| **F-6** | **20260417 panels バリアント剪定ルール定義（命名規約＋削除基準）** | 今週 | MED | 事故防止 | 命名規約を md に制定: `panels_{video_short}_{start}_{end}{_raw,_edited,_shogun_v{N}}.json`。採用版 (cmd_1413 = `_15331_16531` 系の shogun_v3_edited) 以外は `panels/_deprecated/` へ git mv。clip も cmd_1413 採用 `clip_15331_16531.mp4` 以外を `clip/_deprecated/` へ退避。将来の制作者（殿 or 足軽）が一目で本採用ファイルを特定できる状態にする。**削除は殿承認後Phase Bで実施** | 家老が cmd_1413/1414 の採用履歴を確定していることが前提。git mv でリカバリ可 |
| **F-7** | **Day6 MIX 優先区間指定ワークフロー md 作成（9時間全部は要らない）** | 今夜 | LOW | 視聴者価値 | shared_context/procedures/day6_mix_workflow.md 新設。ステップ: (1)殿が優先候補を決める（例: 3視点で同時対戦した盛り上がり箇所 or MEN実況ハイライト3箇所）, (2)oo_men視点のSRTから候補時間帯を特定, (3)他3視点で対応する時刻を `multi_view_sync.md` 既存手順でオフセット算出, (4)各視点clip抽出(-c copy)→F-1トランスコード済charlotteを使用→`hstack/vstack` 合成, (5)BGM追加→非公開アップ。全視点9時間MIXは disk/時間ともに現実的でない。「3分×3箇所 MIX」に限定 | `shared_context/procedures/multi_view_sync.md` 既存活用（新規.py禁止） |
| **F-8** | **動画系積残バックログ集計ビュー（dashboard拡張 or md ひとまず）** | 来月以降 | MED | QoL | 月次で「未消化 raw 動画 / panels未完成 / upload未実施 / on_hold案件」を一覧表示するmdをPhase B以降で生成。v1は手作業集計、v2で既存 `scripts/generate_dashboard.py` にセクション追加（ルール: 新規.py禁止なので既存を拡張）| v1は手書きmdで十分。v2は cmd_1438 のpolish完了 dashboard への追記として発令 |

---

## 4. 最優先3件（Phase B 推奨）

- **F-3**（TNT 漫画ショート完走）: **今夜即着手可**・既存スキルで完結・成果が即視える・ cmd_1441 Phase A 期間中に1本仕上がれば殿のモチベ向上に直結
- **F-1 + F-7**（charlotte トランスコード + Day6 MIX 優先区間ワークフロー）: Day6 4視点MIX を「9時間MIX は現実的でない」という認識合わせとセットで進める。F-1 先行→F-7 で具体区間合意→実MIXは Phase C 以降
- **F-4**（work/ 退避候補リスト）: disk 88% は dashboard 🚨要対応。退避候補が出揃わないと Day6 MIX も漫画ショートも止まる連鎖リスクあり。LOW コストで先行実行可

---

## 5. Phase B への引き継ぎメモ

- 本アイデア出しは足軽6号視点の積残棚卸し。**優先度・採否・実装担当の確定は Phase B 軍師統合で実施**。
- 足軽3号 c カテゴリ（ファイル蓄積整理）と **F-4/F-6 は関心重複**。Phase B で統合調整推奨。
- 足軽1号 a カテゴリ（disk 88%）とも F-4 は直結。退避戦略はここで一本化すべき。
- 軍師 j カテゴリ（横断）が「Day6 MIX を Phase C の目玉に据えるか」を決めれば F-1/F-7 の緊急度が上がる。
- 新規.py 禁止ルール厳守。F-1/F-2/F-3/F-7 はいずれも既存スクリプト・既存スキル・既存procedures活用で完結する設計。
- F-5（cmd_1412 再提示）は Phase B で家老が dashboard 🚨要対応 に追記する流れが自然。
