# 足軽5号アイデア出し（memory MCP + memory/*.md 整理 / e カテゴリ）

cmd_1441 Phase A 足軽5号担当分。memory層の化石化・散在問題に対する具体実装提案。
作成: 2026-04-24 13:02 / ashigaru5
関連: 将軍 1-D / 5-C, 軍師 J-7 / J-8, cmd_1436 Phase3-M

---

## 1. 現状（定量ベースライン）

Phase B 統合で効果測定の基準値。

| 指標 | 現値 | 備考 |
|------|------|------|
| memory MCP entities 総数 | **18** | タスクYAML記載「17」とズレあり（差分要調査） |
| うち 3D 開発設計書系 entities | **11 (61%)** | render_mc_two / motions / camera_director / scene_templates / expression_index / Character Skins Library / expression_design_v5 / motion_system_v2_design / 3d_roadmap / render_mc / Minecraft 3D Rig |
| 最終 observation 追加日 | **2026-04-03** (expression_index.json 1件のみ) | それ以外は全て 2026-03-12 以前 = **3週間以上停滞** |
| memory/*.md 総ファイル数 | **102** | ディレクトリ直下 |
| うち feedback_*.md | **60** | 事故・教訓記録 |
| うち project_*.md | **14** | プロジェクト状態記録 |
| うち shogun_hlsh_selection_*.md | **8** | HL/SH選定済み動画の履歴（作業完了・以後参照頻度低） |
| うち *.png 画像 | **4** | remotion_v4/v6_current / v6_frame / ass_shorts_reference |
| MEMORY.md 行数 | **292 行** | shogun が session start step 3 で明示 Read (auto-memory ではなく project memory) |
| MEMORY.md フォーマット統一度 | **低** | 見出し／表／bullet が混在。日付 prefix も `[2026-03-14]` / `(2026-04-12更新)` / `〜2026-03-05` 等バラバラ |
| 比較: 各エージェント auto-memory | **117 行** | `~/.claude/projects/-home-murakami-multi-agent-shogun/memory/MEMORY.md` (別物)。CLAUDE.md auto memory ルールで 200 行上限あり |

**問題要約**:
- MCP は 3D 設計書ポインタ集として化石化・積極的知見蓄積停止
- *.md は 102 件に膨張・重複・形骸化候補多数
- project MEMORY.md 292 行は視認性・navigability 低下・重要事項の埋没リスク（auto-memory とは別ファイルのため 200 行上限は直接適用されない）

---

## 2. やれてないこと

| # | 未対応事項 | 放置コスト |
|---|-----------|-----------|
| N1 | MCP への `add_observations` 呼出タイミング不在 | 殿判断・事故教訓が MCP に届かず `read_graph` 初期化効果が薄れる |
| N2 | memory/ 月次棚卸し未実施 | 履歴化すべき hlsh_selection 8 件・画像 4 枚が滞留 |
| N3 | claude-mem (cmd_1440 実装) と MCP の役割分担未定義 | cmem 稼働後に同観察が3層に重複蓄積するリスク |
| N4 | MEMORY.md 200 行上限の物理制約 未認識 | 292 行 → 末尾約 90 行が session start 時に読まれない可能性 |
| N5 | `feedback_*.md` リンク切れ・参照切れチェック自動化なし | feedback_remotion_output_format 等の古ルールが生きたまま参照される |

---

## 3. アイデア（8案・3軸ラベル付）

軸: 緊急度 = 今夜 / 今週 / 来月以降 | コスト = LOW(<10分) / MED(30分〜2時間) / HIGH(半日以上) | 効果 = QoL / 運用改善 / 事故防止

| # | アイデア | 緊急度 | コスト | 効果 | 根拠・具体実装 | 依存 |
|---|---------|--------|--------|------|---------------|------|
| E-1 | **memory/archive/ 新設 + shogun_hlsh_selection 8件 + *.png 4枚を移動** | 今週 | LOW | 運用改善 | 履歴化対象を `memory/archive/{hlsh,images}/` へ `git mv`。MEMORY.md の該当リンクは `archive/hlsh/...` へ更新 | なし（単独実行可） |
| E-2 | **MEMORY.md セクション分割（肥大化による視認性低下対策）** | 今週 | MED | 運用改善 | 292 行を index + `memory/core/rules.md`(shogun core rules) / `memory/core/projects.md`(project index) / `memory/core/cli.md` / `memory/core/knowledge.md` に分割。shogun が step 3 で MEMORY.md index → 必要に応じ core/*.md を read する形へ。MEMORY.md は 100 行以下の純粋 index に。※ auto-memory (`~/.claude/projects/.../MEMORY.md` 117行) とは別ファイルのため 200 行上限は直接適用されない点に留意 | なし |
| E-3 | **MEMORY.md フォーマット統一スキーマ制定** | 今週 | MED | 運用改善 | 単一書式: `### [YYYY-MM-DD] タイトル` 見出し + `- [詳細](relative_path.md) — 1行要約` のみ。表形式は禁止。converter スクリプトで既存を一括変換 | E-2 と同時実行推奨 |
| E-4 | **MCP `add_observations` 呼出タイミングを instructions/shogun.md に明文化** | 今週 | LOW | 事故防止 | 明文化対象タイミング: (a) 殿激怒・指摘受領時 (b) cmd完了で新ルール確立時 (c) 事故再発時 (d) 収益化・MCN等戦略決定時。shogun.md のタスクフロー step に「add_observations チェックポイント」追加 | なし |
| E-5 | **memory/ 月次棚卸し cmd 定例化（schedule 登録）** | 来月 | LOW | 運用改善 | `/schedule` で毎月末 28 日 09:00 に「cmd_auto_memory_review」を cron 発令。内容: (1) `grep -L '2026-0[4-9]' memory/feedback_*.md` で3ヶ月参照なし feedback を抽出 (2) shogun が見て archive/削除判断 | `/schedule` 既に導入済 |
| E-6 | **3D 系 11 entities を `memory/3d_context.md` 集約 + MCP から削除** | 今週 | HIGH | QoL | 3D 開発設計書は作業ディレクトリ `projects/dozle_kirinuki/shared_context/3d_*.md` に既に存在する場合が多い。MCP 版は重複ポインタ → 削除し MEMORY.md に `- [3D context](3d_context.md)` 1行リンクに縮約。MCP entity 数 18 → 7 へ軽量化。残す entity: Karo / rule_yaml_first / strategy_ai_sidebusiness / note_daily_strategy / 殿のPC環境 / ドズル社メンバー / note_neta_cho。**可逆性確保**: 事前に `mcp__memory__read_graph > memory/archive/mcp_snapshot_YYYYMMDD.json` を git commit し、全 observation を `memory/3d_context.md` へ全文転記してから `delete_entities` 実行。復旧手順も同 md に記載 | 3D系設計書パスの実在確認（実際に `shared_context/` 配下等に存在するか） |
| E-7 | **feedback_*.md 重要教訓を MCP `Karo` / `rule_yaml_first` entity に観察昇格** | 今週 | MED | 事故防止 | 「殿激怒」「cmd_XXXで発覚」level 10 件程度を選抜し `add_observations` で entity に追加。MEMORY.md 上の該当箇所は `- [XXX](feedback_xxx.md) [MCP: Karo#obs] — 要約` と MCP 参照を併記 | E-4 明文化完了後 |
| E-8 | **claude-mem (cmem) vs MCP vs MEMORY.md 三層モデル文書化** | 今夜 | LOW | 事故防止 | `shared_context/memory_architecture.md` 新設。役割分担: **cmem** = 会話自動観察ログ (read-only 蓄積) / **MCP** = 明示的ルール・エンティティグラフ (shogun が能動的に `add_observations`) / **MEMORY.md** = session start 自動ロード index (200 行以内)。cmd_1440 Phase1 と即連動 | cmd_1440 仕様確定 |

**最優先3件**（Phase B 推奨）:
- **E-8**（三層モデル）: cmd_1440 稼働前に役割分担を定義しないと cmem/MCP/MEMORY.md の重複蓄積が始まる（事故防止・最高優先）
- **E-4 + E-7**（MCP 呼出タイミング明文化 + 重要教訓観察昇格）: MCP 化石化の根本対策。E-4 を先行し E-7 で実践する順序
- **E-1**（archive 新設）: 最小コストで見た目 102 → 90 件に削減・効果即時

---

## 4. 具体実装スケッチ

### 4-1. archive ディレクトリ構造案 (E-1)

```
memory/
├── MEMORY.md                    # 200 行 index
├── MEMORY.md.sample
├── shogun_memory.jsonl
├── core/                        # E-2 で分割 (auto-load 対象外)
│   ├── rules.md                 # Shogun Core Rules (cmd発行・指示・デバッグ)
│   ├── projects.md              # Project Index + 4月計画 + TODO
│   ├── cli.md                   # CLI Notes + Agent Config
│   └── knowledge.md             # YouTube VTT/STT/画像生成モデル決定 等
├── archive/                     # E-1 新設
│   ├── hlsh/                    # shogun_hlsh_selection_*.md 8件
│   └── images/                  # remotion_v*.png / ass_shorts_reference.png
├── feedback_*.md                # 継続使用 (60件)
├── project_*.md                 # 継続使用 (14件)
└── reference_*.md               # 継続使用 (3件)
```

### 4-2. MEMORY.md 統一スキーマ (E-3)

```markdown
## <セクション見出し>

### [2026-MM-DD] <短タイトル>
- [詳細](memory/feedback_xxx.md) — 1行要約（最大80文字）
- [MCP観察: Karo#obs_N](mcp://memory/Karo) — 要約（MCPに昇格済の場合のみ）

### [2026-MM-DD] <次の項目>
...
```

禁止: 表形式・bullet ネスト・複数段落

### 4-3. 月次棚卸し cmd 雛形 (E-5)

```yaml
# queue/shogun_to_karo.yaml 追記用
cmd_auto_memory_review:
  schedule: "0 9 28 * *"   # 毎月28日 09:00
  steps:
    - 1. grep -L '2026-0[N-9]' memory/feedback_*.md で3ヶ月参照なし抽出
    - 2. ls -lt memory/shogun_hlsh_selection_*.md で古い選定メモ抽出
    - 3. mcp__memory__read_graph で最終観察 > 30日の entity 抽出
    - 4. 上記リストを dashboard.md 🚨要対応 に提示 → 殿判断
    - 5. 殿判断後 archive/ 移動 or 削除 or 観察追加
  acceptance_criteria:
    - "memory/archive/ への移動実施 or 継続使用と殿判断記録"
    - "MCP 観察復活件数を報告"
```

### 4-4. 三層モデル提案 (E-8)

| 層 | 媒体 | 書込者 | 読込タイミング | 用途 |
|----|------|--------|---------------|------|
| L1 自動ログ | claude-mem (cmem) | 全会話 auto | `mem-search` skill 経由 | 過去会話の全文検索・意思決定追跡 |
| L2 明示ルール | mcp__memory__ | shogun が能動的 `add_observations` | session start `read_graph` | 教訓・事故根本原因・戦略決定 |
| L3 常時参照 | memory/MEMORY.md + core/*.md | shogun が編集 | session start 自動 read | 現在のルール・プロジェクト一覧・TODO |

**重複回避ルール**:
- cmem は生ログ・MCP は要約 (cmem ID を observation 内に参照)
- MEMORY.md は MCP の index として機能 (「MCP: Karo#obs_N」記法)

---

## 5. Phase B 統合時の申し送り

- **E-6 (3D entity 削除)** は軍師 J-7 の「1-D MCP memory 化石化 → cmd_1436 Phase3-M と統合」と直接リンク。**実装時に cmd_1440 とも衝突調整要**。削除前の snapshot + 全文転記を必須手順化してから実行
- **E-8 (三層モデル)** は cmd_1440 Phase1 の前提条件として位置づけることを推奨。cmd_1440 稼働前に役割分担を固めないと同観察が3層重複する
- 本 e カテゴリは **実装コスト中〜低**・Phase B で一括 subtask 化可能（家老命名: `subtask_1441e_{archive/schema/mcp_obs/3layer}`）
- **target_path フィールド付与の先例**: 本タスク着手時に `pretool_check.sh` が work/cmd_* 直接書込みを BLOCK → 足軽が自分で `target_path: work/cmd_1441/ideas/ashigaru5_e.md` を task YAML に追記して回避。今後 work/cmd_* 出力を伴う足軽タスクは**家老がタスク割当時点で `target_path:` を必ず含める**運用を推奨（cmd_1441 Phase B で配る 80-120 subtask に全適用）

## 6. 足軽5号からの追加確認事項

- MCP entity 数「17 or 18」齟齬: 本調査で 18 確認。タスクYAML 17 は古い値の可能性 → 軍師に再計測依頼したい
- memory/memo_drill_miyazaki.md / note_c2_article.md 等の個別メモ類: 用途不明 → 殿本人確認が必要（足軽では判断不能）
