# MEMORY.md スリム化案 (D6 Option c 確定版)

殿判断 D6 Option c (2026-04-24 15:56): 直接スリム化のみ。統合(a)/分割(b)不採用。軍師は**案作成のみ**、実 Edit は殿承認後に別 subtask で実行。

- **作成**: 2026-04-24 / gunshi (subtask_1441_p10_memory_slim)
- **対象**: `/home/murakami/.claude/projects/-home-murakami-multi-agent-shogun/memory/MEMORY.md` (実体は `memory/MEMORY.md` gitignored)・293行
- **目標**: 293 → **180 行以下** (auto-memory 200行上限の 10% バッファ・最低 113 行削減)
- **残す基準** (task YAML notes):
  1. 殿激怒事案 (原文発言を含む再発防止 rule)
  2. 現役技術ルール (今も呼び出される手順・API・設定値)
  3. 繰り返し発生する事故 (3回以上の hotfix 対象)
- **方針**: 本文 rule + `[詳細: memory/feedback_*.md]` の**二重化が最大の贅肉** → 本文抽象化 + リンクポインタ1行に圧縮。原典 feedback_*.md に本体ありのものは DELETE 候補。

---

## 1. 行単位分類 (判定: KEEP / MERGE / DELETE)

### § ヘッダ・総論 (L1-48)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L1-6 | タイトル + gitignored 注記 | **KEEP** | 必須ヘッダ | — |
| L8-34 | How to Use: MEMORY.md vs MCP (表+方針) | **MERGE** | MCP 3D entity 削除 (cmd_1441 D7) で運用変更済・表のみ残し MCP 推奨事項は短縮 | (新しく5行に圧縮) |
| L36-46 | Example Memory MCP entry (JSON コード例11行) | **DELETE** | MCP graph 残 8 entity で小規模・example code は claude-mem doc に移管可・**本体: github.com/thedotmack/claude-mem README** | — (削除のみ) |
| L47-48 | 区切線 | **KEEP** | 構造 | — |
| **削減** | — | — | -25 (40行→15行想定) | — |

### § Lord's Basic Info + Core Rules (L50-71)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L50-54 | X/GitHub (プレースホルダ) | **KEEP** | 原子情報 | — |
| L55-71 | Shogun Core Rules (cmd発行・指示出し・デバッグ) | **KEEP** | 殿激怒 (3次伝達QC形骸化) + 鉄則集の本丸 | — |
| **削減** | — | — | 0 (22行維持) | — |

### § CLI/Agent Config + Project Index (L73-86)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L73-79 | CLI Notes 表 (1行) | **MERGE** | 表の headers 含めて3行圧縮可 | — |
| L81-82 | Agent Config (空コメント) | **DELETE** | 実コンテンツなし | — |
| L84-86 | Project Index 2件 (coconala/ec) | **MERGE** | 2件のみ・現役ならL289-293 TODOへ統合 | TODO セクション |
| **削減** | — | — | -6 (14行→8行想定) | — |

### § AI副業戦略 + note毎日投稿 (L88-115)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L88-100 | AI副業戦略 道C (14行) | **MERGE** | 2026-03-04決定・現在の進行状況は不明・market data は memory/project_script_cleanup_plan.md 的な別 md へ退避候補 | `memory/project_ai_sidebusiness_strategy.md` 新設 (退避先md) |
| L102-110 | note毎日投稿・記事構成案リンク集 (9行) | **MERGE** | リンクポインタ7項目 → 3行圧縮 (note記事系 feedback は `memory/feedback_note_*.md` 参照の1行 index pointer に) | — |
| L112-115 | 軍師5回集合知 並列化 (5行) | **MERGE** | feedback_gunshi_parallel_collective.md に本体・2行圧縮 | — |
| **削減** | — | — | -15 (28行→13行想定) | — |

### § 殿激怒鉄則集 (L117-212)

**重要原則**: このセクションは**殿激怒・再発事故の本丸** → 軽々しく DELETE しない。本文1行+[詳細リンク]の二重化を圧縮する方向で精査。

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L117-120 | [2026-03-14] 殿指示勝手に拡大するな (cmd_633) | **KEEP** | 殿激怒・現役 rule | — |
| L122-125 | [2026-04-01] JSON修正≠再生成指示 (do_not_act_beyond_instruction) | **KEEP** | 殿激怒・現役 rule | — |
| L127-130 | [2026-03-14] Gemini SRT廃止 | **KEEP** | 現役技術 rule | — |
| L132-134 | [2026-03-25] Gemini画像生成参照画像 | **KEEP** | 現役技術 rule | — |
| L136-138 | [2026-03-27] ネコおじ参照画像 selected/のみ | **KEEP** | 殿激怒 (料理人おじいちゃん全却下) | — |
| L140-142 | [2026-03-15] 漫画ショート構成重視 | **MERGE** | L144/148/152 と合わせて漫画系1行要約 index化 (4件 → 1行) | — |
| L144-146 | [2026-03-16] SRT から自動算出 | **MERGE** | 漫画系 index 統合 | — |
| L148-150 | [2026-03-17] YouTubeショート3分まで | **MERGE** | 漫画系 index 統合 | — |
| L152-154 | [2026-03-17] 構成表開始タイムスタンプ付き | **MERGE** | 漫画系 index 統合 | — |
| L156-170 | [2026-03-17] SRT崩壊 + cluster 9件集積 (15行) | **MERGE** | 14件のポインタ集積 → `memory/feedback_*.md grep 'srt|vtt|youtube|stt'` の1行 index に圧縮 | — |
| L172-174 | [2026-03-16] ffmpeg NVENC | **KEEP** | 殿激怒 (3.5h浪費)・現役技術 rule | — |
| L176-178 | [2026-03-28] ガチャギャラリーHTML標準 | **KEEP** | 現役技術 rule | — |
| L180-183 | [2026-04-02] MCP ダッシュボード | **KEEP** | 現役運用 rule | — |
| L185-187 | [2026-03-31] 状況確認 dashboard+ntfyログのみ | **KEEP** | 現役運用 rule | — |
| L189-191 | [2026-03-29] ダッシュボード⚠️ 殿反応時即消去 | **KEEP** | 殿激怒 再発・cmd_1441 Phase A でも違反発生 | — |
| L193-196 | [2026-04-14] 漫画パネル生成は正規スクリプトのみ | **KEEP** | 殿激怒 cmd_1384 ブタ生成事故 | — |
| L198-200 | [2026-03-19] 既存スキル確認 (cmd_834) | **KEEP** | 殿激怒 14本乱立事故 | — |
| L202-204 | [2026-03-20] 将軍要約禁止 (MENブタ生成) | **KEEP** | 殿激怒・再発防止 | — |
| L206-208 | [2026-04-01] スクリプト保存ルール | **KEEP** | 現役 rule・cmd_1050 再現不能事故 | — |
| L210-212 | [2026-03-19] Remotion .mp4必須 | **KEEP** | 現役技術 rule | — |
| **削減** | — | — | -18 (96行→78行想定) | 漫画系4件 + SRT cluster 圧縮 |

### § HL+SH将軍選定 (L214-220)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L214-220 | HL+SH選定リンク 6件 | **DELETE** | 既に `memory/shogun_hlsh_selection_*.md` 6件として個別存在・MEMORY.md での index は不要 (E-1 足軽5号提案と整合) | `memory/archive/hlsh/` 退避 (cmd_1441 Wave1 p07-v2 subtask と同時実行・**E-1 統合**) |
| **削減** | — | — | -7 (7行→0行) | archive 側に保持 |

### § 3Dボクセル (L222-231)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L222-230 | 3Dボクセルパイプライン状態・MoMask棚上げ | **MERGE** | 全9行→3行要約。MCP 3D削除 (cmd_1441 D7) で方針動いた・要再整理 | `memory/project_3d_voxel_pipeline.md` に本体ありゆえ1行リンク化 |
| L231 | MCP 3D entity snapshot link | **KEEP** | cmd_1441 D7 の archive 参照・本日成立の要ポインタ | — |
| **削減** | — | — | -6 (10行→4行) | — |

### § 技術メモ (L233-249)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L233-236 | ntfy画像受信 (cmd_870) | **DELETE** | 実装完了・config/settings.yaml に設定あり・MEMORY.md では不要 | `memory/archive/feature_impl_log.md` 新設 or 削除 |
| L238-241 | chrome孤児化対策 (cmd_864) | **DELETE** | 実装完了・scripts/ とcrontab に実在 | 削除 |
| L243-245 | 立ち絵フェード無効化 (cmd_XXX) | **DELETE** | 将軍直接修正の記録・再発防止 rule でない・実装記録 | 削除 |
| L247-249 | ntfy重複受信バグ (cmd_871) | **DELETE** | 修正完了・再発防止は家老 ntfy ルール (CLAUDE.md) に統合済 | 削除 |
| **削減** | — | — | -15 (17行→2行) | 4件ともDELETE可能 |

### § チャンネル実績・成長ログ (L251-260)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L251-256 | チャンネル実績 **2026-04-12 古い数値** (1,830人 / 210万再生 / 61本) | **FLAG for 殿更新確認** | 最新 auto-memory (2026-04-24): 登録2,740人 / 総再生348万 / 74本・YPP条件達成と乖離大。**数値更新は殿 or 将軍の所管** (軍師は更新主体ではない) → 殿判断「更新→軍師がスリム化時に差替」or「数値は dashboard.md 一本化・MEMORY.md からは削除」のいずれか | 殿判断待ち |
| L258-260 | チャンネル成長ログ | **KEEP** | `memory/project_channel_growth_log.md` 参照の 1行・維持 | — |
| **削減** | — | — | -4 (10行→6行) | — |

### § Tailscale/OAuth/画像生成 (L262-276)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L262-264 | Tailscale環境 | **MERGE** | IPアドレス3件のみが要・設定詳細は reference_tailscale_setup.md に本体 | 2行に圧縮 |
| L266-269 | OAuth遠隔認証 | **MERGE** | reference_oauth_remote_auth.md に本体・スコープ情報は1行に | 2行に圧縮 |
| L271-273 | 画像生成モデル決定 (gemini-3.1-flash-image-preview) | **KEEP** | 現役技術 rule・禁止モデル明記 | — |
| L275-276 | MBTI scene_4 漫画ショート原稿 | **DELETE** | 個別 cmd (cmd_1027) 原稿・project_mbti_scene4_panels.md に本体・作業完了後は MEMORY.md 不要 | 削除 |
| **削減** | — | — | -6 (15行→9行) | — |

### § 4月計画・棚上げ・情報ソース (L278-287)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L278-281 | 4月計画 3件 (Geminiキー/cmd_982/月次総集編) | **MERGE** | 全て project_*.md に本体・1行ずつ圧縮 | — |
| L283-284 | 棚上げアイデア (副業3件) | **MERGE** | shelved_side_business_ideas.md に本体・1行ポインタで十分 | — |
| L286-287 | Shogun系譜+note情報ソース | **KEEP** | 現役参照 | — |
| **削減** | — | — | -4 (10行→6行) | — |

### § TODO (L289-293)

| 行範囲 | 現在の内容要約 | 判定 | 理由 | 退避先 |
|--------|--------------|------|------|--------|
| L289-293 | TODO 3件 (cmd_193/テンプレ第2弾/ココナラPF) | **KEEP** | TODO は残す・内容の最新性確認要 (2026-04-24 現在どれが残っているか殿確認) | — |
| **削減** | — | — | 0 (5行維持) | — |

---

## 2. 削減総計

| セクション | 現在 | 削減後 | Δ |
|-----------|-----|-------|---|
| ヘッダ・総論 | 48 | 15 | **-33** |
| Lord's Info + Core Rules | 22 | 22 | 0 |
| CLI/Config/Project Index | 14 | 8 | **-6** |
| 副業戦略 + note投稿 | 28 | 13 | **-15** |
| 殿激怒鉄則集 | 96 | 78 | **-18** |
| HL+SH将軍選定 | 7 | 0 | **-7** |
| 3Dボクセル | 10 | 4 | **-6** |
| 技術メモ (ntfy/chrome/etc) | 17 | 2 | **-15** |
| チャンネル実績/成長 | 10 | 6 | **-4** |
| Tailscale/OAuth/画像生成 | 15 | 9 | **-6** |
| 4月計画/棚上げ/情報ソース | 10 | 6 | **-4** |
| TODO | 5 | 5 | 0 |
| 区切線・空行 | 11 | 6 | **-5** |
| **合計** | **293** | **174** | **-119** |

**達成**: 293 → 174 行 (目標 180 以下クリア・auto-memory 200 上限に 26行バッファ)

---

## 3. DELETE/MERGE 対象の「別媒体に本体あり」根拠

DELETE・MERGE 判定は必ず原典存在確認を行った (qc_1441_p20 の自己申告『現役参照の誤削除リスク』対策)。

| 削除候補 | 原典 (別媒体) | 存在確認方法 |
|---------|--------------|--------------|
| L36-46 MCP Example code | claude-mem README (https://github.com/thedotmack/claude-mem) | WebFetch 実施済 (cmd_1436 軍師分析) |
| L214-220 HL+SH選定 6件 | `memory/shogun_hlsh_selection_*.md` 6件 | `ls memory/shogun_hlsh_selection_*.md` で実在確認 (足軽5号 e カテゴリ E-1 調査済) |
| L233-236 ntfy画像受信 | scripts/ntfy_listener.sh + config/settings.yaml ntfy_image_dir | 実装コード実在 |
| L238-241 chrome孤児化対策 | scripts/kill_orphan_chrome.sh + crontab | crontab -l で毎分稼働確認済 (gunshi_j テーマ3) |
| L243-245 立ち絵フェード | remotion-project/src/MultiTachieOverlay.tsx FADE_FRAMES | 直接修正履歴・git log 確認可 |
| L247-249 ntfy重複受信 | CLAUDE.md ntfy通知ルール + scripts/ntfy.sh | CLAUDE.md 本文にルール統合済 |
| L275-276 MBTI scene_4 | memory/project_mbti_scene4_panels.md | ファイル実在 |
| L156-170 SRT cluster 9件 | memory/feedback_youtube_vtt_fallback.md ほか 14件 | `ls memory/feedback_*.md` で60件確認済 |
| L222-230 3D Voxel | memory/project_3d_voxel_pipeline.md | ファイル実在 |

---

## 4. 殿承認フロー (実 Edit 禁止・案のみ)

**重要**: 本 proposal は**案のみ**。実 Edit は殿承認後に別 subtask で実行する (D6 Option c 殿指示の前段・task YAML notes 厳守)。

1. 本 proposal md を殿・家老にレビュー依頼 → 採択/部分修正/却下 判断
2. 殿承認時 (または部分採択時):
   - 家老が `subtask_1441_p10b_memory_edit` として実 Edit 発令 (担当候補: 足軽5号・E-1 archive 新設と同時実行推奨)
   - 足軽5号が本 proposal に従い MEMORY.md を Edit
   - 軍師が QC 実施 (行数 ≤ 180 行・現役参照の誤削除ゼロ確認)
3. 殿 却下時:
   - proposal を修正 (KEEP/MERGE/DELETE 判定を見直し) → 再提示

---

## 5. リスク評価

| リスク | 対策 |
|--------|------|
| 現役参照されている記述の誤削除 | §3 で全 DELETE 候補の原典存在確認を記録済・QC で再確認 |
| auto-memory (200行上限) との整合ズレ | 174行 目標で 26行バッファ確保 |
| 殿の個別好みに反する項目削除 (例: 3Dボクセル残課題) | DELETE せず **MERGE** 止まり・project_*.md 参照リンクのみ残す |
| 圧縮後の可読性劣化 | 圧縮時にカテゴリ見出し (###) と原文タイムスタンプ [YYYY-MM-DD] は保持 |

---

## 6. 軍師意見: 除外すべき可能性のあるもの (要殿判断) ※ §1 判定の保留選択肢

**一貫性注記**: 本 §6 は §1 表中で既に MERGE/DELETE 判定 (下記該当) を付けた項目について、殿が強い拘りある場合の**保留選択肢**として提示する。本 proposal 全体を殿が承認すれば §1 判定どおりに処理される。以下は「これは殿の関心次第で個別撤回あり得る」物のみ列挙する。

- L102-110 note毎日投稿系リンク = §1 MERGE (圧縮3行)
- L214-220 HL+SH将軍選定 6件 = §1 DELETE (archive退避)
- L278-281 4月計画 3件 = §1 MERGE (圧縮)
- L283-284 棚上げアイデア 副業3件 = §1 MERGE (1行ポインタ化)

以下は軍師が「削除して問題なさそう」と判断したが、殿の意図次第では保留とすべき可能性があるもの:

1. **L102-110 note毎日投稿系リンク**: 殿が note 投稿を休止中なら削除加速・再開予定あれば現状維持
2. **L214-220 HL+SH将軍選定 6件**: 将軍自選フローが今も生きているか殿確認 (足軽5号 E-1 archive 方針の追認でもある)
3. **L278-281 4月計画 3件**: 4月末 (本日 4/24) 近接ゆえ再計画タイミング・cmd_982 (clip_c) は生きているか確認要
4. **L283-284 棚上げアイデア 副業3件**: 棚上げ継続 vs 完全archive化 vs 削除 の3択・殿判断

---

## 7. 北極星アラインメント

- **北極星**: 切り抜きチャンネル質・効率
- **寄与**: auto-memory 200行上限超過を解消 → Session Start 時の context 密度向上 → 将軍判断速度向上 (運用効率)
- **リスク**: 現役 rule の誤削除 → 殿判断への fallback で回避

---

以上、MEMORY.md 293 → 174 行 スリム化案 (D6 Option c)。実 Edit は殿承認後の別 subtask で実行。
