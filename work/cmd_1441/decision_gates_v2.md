# cmd_1441 殿判断ゲート v2: decision_gates_v2.md

殿2重指示反映の差し戻し改訂版。v1 (execution_plan.md §3 D1-D9) を再構成し、D4 訂正 (A1-a 復活) と D10 新設 (capability_tiers モデルmapping) を反映。動画系は保留処理につき D1/D2 は殿判断ゲートから除外。

- **作成**: 2026-04-24 / gunshi (subtask_1441_phaseB2)
- **前身**: work/cmd_1441/execution_plan.md (commit 889d948) の §3 Wave 2 殿判断ゲート一覧
- **併読**: work/cmd_1441/execution_plan_v2.md

---

## 1. 確定事項 (殿判断済・v2 反映対象)

| # | 判断事項 | 殿決定 | 関連 subtask | 実装への反映 |
|---|---------|--------|-------------|---------------|
| **確定1** | bloom_routing の扱い (v1 で D4 と呼称) | **A1-a 復活確定** (v1 推奨の A1-b 削除を却下) | p05-v2 | settings.yaml に bloom_routing + capability_tiers キー追加 |
| **確定2** | 動画系 4件 (TNT漫画/Day6 MIX/charlotte変換/part_info修正) | **保留** (仕組み改善優先) | paused_p06/12/13/14 | re-trigger 条件付き保留タグで保持 |
| **確定3** | p11 Opus観測 | **動画系除外の例外**として続行 | p01-v2 | 優先度A (今夜ウィンドウ) で最優先発令 |

---

## 2. 未決の殿判断ゲート (v2 で継続・D2-D9 再採番 + D10 新設)

**優先順序**: A1-a 復活の sub-gate である D10 を最優先。次に D3/D5/D6/D7/D9 の仕組み改善系、D8 MCN は別軸で並走。

### D10 (新設・最優先) capability_tiers モデルマッピング ★A1-a復活に付随する必須 sub-gate

- **問題**: bloom_routing 復活 (確定1) には L1-L6 のモデル割当が必要。現状 GLM/Sonnet/Opus[1m] の3モデルをどの階層に配置するかが未確定。軍師独断で決めてはならない事項。
- **選択肢**:
  - **Option α**: L1-L2=GLM / L3-L4=Sonnet / L5-L6=Opus[1m] (段階的エスカレーション型)
  - **Option β**: L1-L3=GLM / L4-L5=Sonnet / L6=Opus[1m] (GLM比重高・コスト最適)
  - **Option γ**: L1-L3=Sonnet / L4-L6=Opus[1m] (Sonnet ベースライン型・今夜特例は Opus)
  - **Option δ**: 殿がカスタム mapping を指定
- **軍師推奨**: **Option β** (GLM比重高・コスト最適・足軽が GLM で高頻度タスク対応可能) + **L6 は今夜限 Opus[1m]、平時は Sonnet fallback** (軍師常用モデル Sonnet との整合)
- **関連**: p05-v2 bloom_routing 復活 subtask の発令 blocker

### D3 skills/ whitelist運用 (v1: D4→D3 に繰上)

- **問題**: 新規 skill 作成毎に .gitignore に2行追加必要 (yt-dlp-js-runtimes-fix で hotfix 発生)
- **選択肢**:
  - Option a: whitelist 継続 + skill-creator にて2行追加工程を自動化
  - Option b: **skills/ 全体を tracked 運用に変更** (.gitignore から skills/ 除外)
- **軍師推奨**: **Option b** (新規skill作成毎の手動作業排除・根本解決)
- **関連**: p04-v2 / p06-v2

### D5 instructions/{generated,cli_specific,common,roles}/ archive化 (v1: D5)

- **問題**: 4サブディレクトリ 26ファイル全て 2026-03-02 から未更新・現役参照なし (足軽4号発見)
- **選択肢**:
  - Option a: **archive化** (`instructions/archive/202603/` へ git mv・履歴保持)
  - Option b: 現状維持 (ノイズとして許容)
  - Option c: 完全削除 (git log のみ残す)
- **軍師推奨**: **Option a** (履歴保持+可視ノイズ削減)
- **関連**: p09-v2

### D6 MEMORY.md Session Start 変更可否 (v1: D6)

- **問題**: MEMORY.md 292行 (auto-load 上限 200 行超過懸念・G7 足軽4指摘)
- **選択肢**:
  - Option a: **core/*.md 分割 + shogun.md Session Start 同期更新** (MEMORY.md を 100行 index 化)
  - Option b: 現状維持 (超過分は truncate 許容)
- **軍師推奨**: **Option a** (視認性改善・重要事項埋没防止)
- **関連**: p10-v2

### D7 MCP 3D entity 削除可逆性手順承認 (v1: D7)

- **問題**: MCP 18 entity のうち 11 件 (61%) が 3D 開発設計書ポインタと化石化
- **選択肢**:
  - Option a: **snapshot + 全文転記 → delete_entities** (可逆性担保)
  - Option b: 削除せず放置 (化石化継続)
  - Option c: snapshotなしで即削除 (不可逆・非推奨)
- **軍師推奨**: **Option a** (snapshot必須・memory/3d_context.md 全文転記後に削除)
- **関連**: p11-v2

### D8 MCN v2 (v1: D8) ★別軸継続

- **問題**: ガイドラインURL/PDF + 送信チャネル確定 + AI 3段構え承認がブロッカー
- **選択肢**: 殿の外部情報・判断依存のため軍師側で option 化不能
- **軍師推奨**: 殿から以下を取得:
  - (1) ドズル社ガイドライン原文URL or PDF (添付)
  - (2) 送信先 (メール/フォーム/X DM 等の種別と宛先)
  - (3) AI画像生成の扱い (v1「相談事項」→ v2「3段構え提案」化 OK?)
- **関連**: mcn_v2 (Phase C Wave とは別軸で継続)

### D9 dozle_kirinuki submodule 履歴書換 (v1: D9)

- **問題**: google-cloud-sdk 数千オブジェクトが submodule 履歴に残留・194MB 超過で push 不可・12 commits 未公開
- **選択肢**:
  - Option a: **`git filter-repo --path google-cloud-sdk --invert-paths` + backup + force-with-lease** (推奨)
  - Option b: `git-lfs` 移行 (GitHub Free 1GB/月で実用困難)
  - Option c: submodule を非公開運用に変更 (最終手段)
- **軍師推奨**: **Option a** (1日作業想定・共同作業者なし確認・backup 必須・force-with-lease)
- **関連**: p12-v2

---

## 3. v1 → v2 ゲート対応表

| v1 ID | v1 項目 | v2 での扱い |
|-------|---------|-------------|
| D1 (v1) | Day6 MIX 優先区間 (3分×3箇所) | **保留** (paused_p12 復活時に殿判断) |
| D2 (v1) | cmd_1413採用/1411却下の再確認 | **保留** (paused_p14 復活時に殿判断) |
| D3 (v1) | skills whitelist vs 全体tracked | **D3 (v2)** そのまま継続 |
| D4 (v1) | bloom_routing A1-a復活 vs A1-b削除 | **確定1**(A1-a 復活) + **D10 新設** (capability_tiers mapping) |
| D5 (v1) | instructions 26file archive化 | **D5 (v2)** そのまま継続 |
| D6 (v1) | MEMORY.md Session Start 変更可否 | **D6 (v2)** そのまま継続 |
| D7 (v1) | MCP 3D entity 削除可逆性手順承認 | **D7 (v2)** そのまま継続 |
| D8 (v1) | MCN v2 ガイドラインURL/PDF等 | **D8 (v2)** 別軸継続 |
| D9 (v1) | dozle submodule 履歴書換 | **D9 (v2)** そのまま継続 |
| (v1 なし) | capability_tiers モデルmapping | **D10 (v2) 新設** |

---

## 4. 殿提示方法 (家老運用推奨)

1. **dashboard.md 🚨要対応** に以下 1 ブロック追加:
   ```
   🚨 cmd_1441 Phase C 発令前・殿判断要請 (6件)
   - D3 skills/ 全体tracked化 (推奨: Option b)
   - D5 instructions/ 26file archive化 (推奨: Option a)
   - D6 MEMORY.md core分割 (推奨: Option a)
   - D7 MCP 3D entity snapshot+削除 (推奨: Option a)
   - D9 dozle submodule 履歴書換 (推奨: Option a)
   - D10 capability_tiers モデルmapping (推奨: Option β)
   別軸: D8 MCN v2 (ガイドライン+送信先+AI扱い)
   ```
2. **ntfy 通知** で殿に一括通知 (`🚨 cmd_1441 Phase C 発令前 殿判断6件` レベル=重要)
3. 殿の回答を dashboard.md に受領 → 家老が各 subtask を `assigned` 化して発令

---

## 5. v2 北極星への影響

- **確定1 (bloom_routing 復活)**: 中長期的にモデル階層運用が復活 → コスト最適化寄与
- **確定2 (動画系保留)**: 短期的には北極星 (視聴者価値) への寄与が減るが、仕組み整備で再開時の速度が上がる
- **D10 未決定ブロック**: p05-v2 bloom_routing 実装が D10 殿判断待ちで停滞 → 長引けば優先度B 全体が後ろ倒し
- **D3-D9 未決定**: 各々 p04-v2 / p09-v2 / p10-v2 / p11-v2 / p12-v2 の発令ブロッカー

---

以上、decision_gates_v2.md として提出する。確定事項3件と未決9ゲート (D3/D5/D6/D7/D8/D9/D10) を整理した。
