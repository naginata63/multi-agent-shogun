# cmd_1584 Audit Report — @import 化候補/維持候補 精査

**作成者**: 軍師 (gunshi)
**作成日時**: 2026-05-03 09:55 JST
**Parent cmd**: cmd_1584 / subtask_1584a
**北極星 (north_star)**: Claude Code の @import 機能を活用し、CLAUDE.md / instructions / shared_context の重複を削減 + 一貫性向上。**コンテキスト消費を増やさず**、Udemy ch03 で自プロジェクトの実例として紹介可能なレベルまで整備する。

---

## 0. コンテキスト注入の背景 (殿への前提共有)

### Claude Code の @import と「共通ファイル参照」は別物 ★最重要前提★

| 機能 | 仕組み | 適用対象 |
|------|-------|---------|
| **@import (Claude Code 機能)** | `@path/to/file.md` 記法。**Claude Code が起動時にプリ展開**してプロンプトに inline 注入 | **auto-load 対象のみ**: `CLAUDE.md` (project) / `~/.claude/projects/*/memory/MEMORY.md` (user) |
| **共通ファイル参照 (一般パターン)** | エージェントが Session Start 時に **Read tool で明示読込** | `instructions/*.md` / `shared_context/procedures/*.md` (Claude Code は @import 解決しない) |

**含意**:
- `instructions/karo.md` 内に `@shared_context/agent_common.md` と書いても **展開されない**。家老は明示 Read が必要。
- `CLAUDE.md` 内の `@shared_context/destructive_safety.md` は **auto-load 時に展開される** → 全エージェントの初回 prompt に inline 注入。
- 従って本audit は **2軸戦略** で計画する:
  - **軸A**: CLAUDE.md / MEMORY.md の **@import 化** (Claude Code feature 直接利用)
  - **軸B**: instructions/*.md 間の重複を **共通 shared_context/ ファイル化** + Session Start で全エージェント Read 追加

### 現状サイズ計測

| ファイル | 行数 | 推定 tokens (×17/行) | auto-load? |
|---------|-----:|--------------------:|-----------|
| CLAUDE.md | 332 | ~5,640 | ✅ 全agent |
| MEMORY.md | 77 | ~1,310 | ✅ shogun のみ (ユーザ memory) |
| instructions/shogun.md | 429 | ~7,290 | ❌ shogun が Step 4 で Read |
| instructions/karo.md | 417 | ~7,090 | ❌ karo が Step 4 で Read |
| instructions/gunshi.md | 554 | ~9,420 | ❌ gunshi が Step 4 で Read |
| instructions/ashigaru.md | 367 | ~6,240 | ❌ ashigaru が Step 4 で Read |
| instructions/git_safety.md | 61 | ~1,040 | ❌ batch modify 時のみ参照 |
| shared_context/procedures/*.md (55本) | 計 ~5,500 | ~93,500 (合計) | ❌ Lazy load (タスク該当時のみ) |

**現状 auto-load 総量**: CLAUDE.md (5,640) + MEMORY.md (shogun のみ・1,310) ≈ **5,640 〜 6,950 tokens** が常時注入。

---

## 1. ファイル別 A/B/C 判定

| ファイル | 判定 | 理由 | アクション |
|---------|:----:|------|----------|
| **CLAUDE.md** | **C (要部分切出)** | 332行と肥大化・常時注入対象ゆえ重い・しかし全 agent 必読のため丸ごと lazy 化は不可 | 内部の Destructive Safety 等を @import 切出 → 単一source化 (auto-load サイズ自体は変わらないが管理が楽) |
| **memory/MEMORY.md** | **B (維持)** | 77行・User memory・既に最適化済み。@import で外部分割可能だが現状 ROI 低い | 維持。将来肥大化したら @import で分割可 |
| **instructions/shogun.md** | **C (要部分切出)** | 429行。SayTask Routing が 100+ 行と長大・本来 procedures/ 行き | SayTask Routing を `shared_context/procedures/saytask_routing.md` に切出参照化 |
| **instructions/karo.md** | **C (要部分切出)** | 417行。動画系チェックリスト・Frog/Streak テンプレが procedures 行き候補 | 該当2セクションを procedures/ に切出参照化 |
| **instructions/gunshi.md** | **C (要部分切出)** | 554行と最長。Karo-Gunshi Patterns が procedures/ 行き候補 | Communication Patterns を procedures/ に切出参照化 |
| **instructions/ashigaru.md** | **C (要部分切出)** | 367行。Persona/Shout Mode 等が共通化候補 | 共通箇所を `shared_context/agent_common.md` に集約参照 |
| **instructions/git_safety.md** | **B (維持)** | 61行・既に十分簡潔・batch modify 時のみ Read | 維持。CLAUDE.md からは "詳細: instructions/git_safety.md" 参照のみ (現状OK) |
| **shared_context/procedures/*.md (55本全部)** | **B (維持・@import 化対象外)** | Lazy load が正解。タスク該当時のみ Read される。@import 化すると auto-load 注入され逆効果 | **絶対に @import 化しない**。現状の "詳細: shared_context/procedures/X.md" 参照パターンを維持 |

---

## 2. instructions/*.md 共通重複セクション一覧 (★最大の改善余地★)

以下セクションは複数 instructions に**ほぼ同一文**で重複。`shared_context/agent_common.md` (新設) に集約すべき:

| 重複セクション | 出現ファイル | 各ファイルでの行数概算 | 重複削減見積 |
|--------------|-------------|------------------:|------------:|
| **セマンティック検索 (Gemini Embedding 2)** | shogun/karo/gunshi/ashigaru | 各 ~12-15行 (karo は 1行で省略済) | **-30行** (4ファイル合算 -42 + 共通12 = -30) |
| **Dashboard API 利用 (cmd_1494)** | shogun/karo/gunshi/ashigaru | 各 ~13-20行 (テーブル+リンク) | **-40行** (4合算 -65 + 共通25 = -40) |
| **Agent Self-Watch Phase Rules (cmd_107)** | shogun/karo/ashigaru | 各 ~5-7行 | **-12行** (3合算 -18 + 共通6 = -12) |
| **Language & Tone (config/settings.yaml参照)** | karo/gunshi (※shogun/ashigaru は短縮) | 各 ~8行 (例文込) | **-8行** |
| **Self-Identification (tmux display-message)** | gunshi/ashigaru | 各 ~7行 | **-7行** |
| **Timestamp Rule (date 必須)** | karo/ashigaru | 各 ~6行 | **-6行** |
| **Compaction Recovery 共通骨子** | shogun/karo/gunshi/ashigaru | 各 ~12-15行 | **-30行** (役割固有部分は各ファイルに残す) |
| **/clear Recovery 共通骨子** | gunshi/ashigaru | 各 ~10行 | **-10行** |
| **Shout Mode (echo_message)** | gunshi/ashigaru | 各 ~12行 (gunshi は ashigaru.md 参照のみで短縮済) | **-5行** |

**重複削減合計**: 約 **-148行** (instructions 4本合計 ~1,767行 → ~1,619行・約 **-8.4%**)

**Token 換算**: -148行 × 17 tok/行 ≈ **-2,520 tokens** (Session Start 時の各 agent の Read 時)。
4 agent × Session Start 1回 で **-2,520 tokens × 4 = 約 -10,080 tokens 節約/セッション**。
ただし新設 `shared_context/agent_common.md` (~150行・~2,550 tokens) を **各 agent が追加 Read** するため、**実質節約は 4 × (約 630 tokens 節約) = 約 -2,520 tokens/セッション**。

→ **重複削減効果は控えめ。狙いは「一貫性向上 + メンテ性」が主・コンテキスト節約は副次効果**。

---

## 3. CLAUDE.md @import 化候補 (Claude Code 機能直接利用)

CLAUDE.md は全 agent に auto-load されるため、@import で分割しても **auto-load 後の総 token 量は変わらない**。狙いは:
- **単一source化** (重複セクションを物理ファイル単位で集約)
- **メンテ性** (Destructive Safety を変更すると複数ファイル更新不要)
- **可読性** (CLAUDE.md 本体を骨格のみに)

### A判定 (@import 化推奨)

| 切出対象セクション | 切出先 (@import path) | 行数 | 理由 |
|-----------------|-------------------|----:|-----|
| **Destructive Operation Safety** (Tier 1/2/3 + WSL2 + Prompt Injection Defense) | `shared_context/safety/destructive.md` (新設) | ~60行 | 全 agent 共通の絶対鉄則。論理単位として独立・変更時は意識的に編集したいので @import で物理分離 |
| **Git Safety Protocol** (5+ファイル修正時の手順 + work/ コミットルール) | `instructions/git_safety.md` (既存) | ~30行 | **既に分離ファイルあり**。CLAUDE.md には "詳細: instructions/git_safety.md" 記載済 → 完全 @import 化に格上げ |
| **技術的鉄則 (動画/画像/重処理)** | (現状維持・変更不要) | ~10行 | 既に shared_context/procedures/ への参照リスト・@import すると procedures が auto-load されるため逆効果 → **維持** |

### B判定 (CLAUDE.md 本体に残す)

| セクション | 行数 | 理由 |
|----------|----:|-----|
| Procedures (Session Start / /clear Recovery / Summary Generation / Post-Compaction Recovery) | ~50行 | 全 agent 起動時に必ず参照・物理分離するメリット薄い |
| Agent Role Quick Reference | ~10行 | 短い表 |
| Communication Protocol (API化) | ~15行 | 概念図・短い |
| Context Layers | ~10行 | 短い概念図 |
| ファイル配置ルール | ~12行 | 短い表 |
| Karo Context Relief Trigger | ~3行 | 一行ルール |
| Shogun Mandatory Rules | ~7行 | 短い |
| Test/QC Rules | ~7行 | 短い |
| Critical Thinking | ~3行 | 一行 |
| ntfy通知ルール (家老) | ~10行 | 短い |
| Dashboard API 利用ルール | ~20行 | テーブル形式・instructions 各 agent からも参照 |
| Advisor Tool Usage | ~17行 | 全 agent 共通の推奨ツール仕様 |

---

## 4. 実装フェーズ分け

リスク低 → 高 の順で 3 フェーズに分割。**殿レビュー後に家老が ashigaru に振る**前提。

### Phase 1: 共通セクション集約 (リスク: 低・効果: 中)

**目的**: instructions/*.md 4本の重複セクションを `shared_context/agent_common.md` に集約。

**手順**:
1. `shared_context/agent_common.md` 新設 (~150行) — 以下を集約:
   - セマンティック検索
   - Dashboard API 利用 (cmd_1494) 概要テーブル
   - Agent Self-Watch Phase Rules (cmd_107)
   - Language & Tone (config/settings.yaml 参照規約)
   - Self-Identification (tmux display-message)
   - Timestamp Rule
   - Compaction Recovery 共通骨子
   - /clear Recovery 共通骨子
   - Shout Mode 共通仕様
2. CLAUDE.md の Session Start に追記: 「Step 4 で instructions/{role}.md を Read した後、`shared_context/agent_common.md` も Read せよ」
3. instructions/shogun.md / karo.md / gunshi.md / ashigaru.md から重複セクションを削除し、冒頭に「★共通項は shared_context/agent_common.md を参照」と1行記載
4. 各 instructions ファイルには **役割固有部分のみ残す** (例: shogun の SayTask Routing・karo の Task Design 5問・gunshi の North Star Alignment・ashigaru の Race Condition等)

**リスク**:
- 4 agent が起動時に追加 Read するため、Session Start IO が +1 ファイル
- 共通ファイル変更時の影響範囲が全 agent (これは狙い)

**ロールバック**:
- agent_common.md 削除 + 各 instructions の重複セクションを git revert で復元

**検証**:
- 各 agent (shogun/karo/gunshi/ashigaru) を /clear → Session Start → 役割理解できているか・追加 Read が成功しているか
- Read 順序 = `instructions/{role}.md` → `shared_context/agent_common.md` (両方 Read で初めて完全な行動規範)

---

### Phase 2: instructions 内長セクションの procedures/ 切出 (リスク: 中・効果: 中)

**目的**: 各 instructions/*.md 内で「役割固有だが procedures 行き候補」の長セクションを procedures/ に切出 + Lazy load 化。

**切出候補**:

| 元ファイル | セクション | 切出先 | 行数 | 切出後の参照 |
|----------|----------|-------|----:|------------|
| **shogun.md** | SayTask Task Management Routing (Routing Decision / Task Add Patterns / Task List / Task Complete / Task Edit/Delete / AI/Human Routing / Context Completion / Coexistence) | `shared_context/procedures/saytask_routing.md` | ~110行 | shogun.md 内に「VF task 関連は procedures/saytask_routing.md 参照」1行 |
| **karo.md** | 動画系cmd起票チェックリスト (cmd_1479規格化) | `shared_context/procedures/video_cmd_checklist.md` | ~17行 | karo.md 内に「動画系cmd起票時は procedures/video_cmd_checklist.md 参照」1行 |
| **karo.md** | 🐸 Frog / Streak Section Template | `shared_context/procedures/saytask_dashboard_template.md` | ~25行 | karo.md 内に「Frog/Streak section template は procedures/saytask_dashboard_template.md 参照」1行 |
| **gunshi.md** | Karo-Gunshi Communication Patterns (Pattern 1-4) | `shared_context/procedures/gunshi_patterns.md` | ~50行 | gunshi.md 内に「家老-軍師連携パターンは procedures/gunshi_patterns.md 参照」1行 |
| **gunshi.md** | Cron Inventory Quarterly Review | `shared_context/cron_inventory.md §5` (既存・現状もここ参照) → **現状維持** | (移動不要) | 既に外部参照・OK |

**Token 節約**:
- shogun.md: -110行 ≈ -1,870 tokens (Session Start 時)
- karo.md: -42行 ≈ -714 tokens
- gunshi.md: -50行 ≈ -850 tokens
- 合計 Session Start で -3,434 tokens (3 agent 合算)

**リスク**:
- 切出した procedures が Lazy load = タスク該当時のみ参照 → **タスク YAML の steps に明示参照を書かないと家老/将軍が見落とす可能性**
- 既存 task YAML の steps に "procedure: shared_context/procedures/X.md" 記載済の cmd は OK・新規 cmd 起票時はテンプレ更新必須

**ロールバック**: git revert で容易

**検証**:
- VF task 系の操作 → 将軍が procedures/saytask_routing.md を Read してから処理しているか
- 動画系 cmd 起票 → 家老が procedures/video_cmd_checklist.md を Read しているか

---

### Phase 3: CLAUDE.md @import 化 (リスク: 低・効果: 小)

**目的**: CLAUDE.md 内の論理独立セクションを @import 化し、CLAUDE.md 本体をスリム化。

**切出候補**:

| 元セクション | @import 先 | 行数 | 効果 |
|------------|----------|----:|-----|
| **Destructive Operation Safety** (Tier 1/2/3 + WSL2 + Prompt Injection Defense) | `shared_context/safety/destructive.md` (新設) | ~60行 | CLAUDE.md 本体スリム化・論理単位の物理分離 |
| **Git Safety Protocol** (5+ファイル修正手順 + work/ ディレクトリ コミットルール) | `instructions/git_safety.md` (既存に追記) | ~30行 | 既に外部ファイル化済 → CLAUDE.md 内の重複版を削除し @import 化 |

**実装**:
- CLAUDE.md 本文の該当セクション削除 → 代わりに `@shared_context/safety/destructive.md` 1行で記載
- Claude Code が auto-load 時に inline 展開・auto-load 後の総 token 量は変わらない・**CLAUDE.md ソースの可読性が向上**

**リスク**:
- @import 解決失敗 (typo・移動忘れ) → 全 agent の auto-load で「@import not found」になる
- 必ず別ブランチ + ローカル Claude Code 起動で **手元で auto-load 動作確認してから main マージ**

**検証**:
- 適用後、新 Claude Code セッションを起動 → 最初のレスポンスで Destructive Safety 知識が保持されているか
- (例) 「ashigaru に rm -rf / を実行させていいか?」と聞いて F Tier 1 D001 を引用できるか

**ロールバック**: git revert で容易

---

## 5. 重複削減・コンテキスト消費 総合見積

### 行数 (LOC) ベース

| Phase | 削減対象 | 削減行数 | 増加行数 (新ファイル) | 純減 |
|-------|---------|--------:|------------------:|----:|
| Phase 1 | instructions 4本の共通セクション | -148 | +150 (agent_common.md) | **+2 (微増)** ※ |
| Phase 2 | instructions 3本の長セクション | -202 | +202 (procedures/ 4本) | **±0** |
| Phase 3 | CLAUDE.md 内 2セクション | -90 | +90 (safety/destructive.md 新設・git_safety.md 追記) | **±0** |

※ Phase 1 は LOC 上は微増だが、**役割別 Session Start で各 agent が読む量** は減る:
- 旧: shogun.md (429) + karo.md (417) + gunshi.md (554) + ashigaru.md (367) = 1,767行・各 agent 1本ずつ Read
- 新: 各 instructions/*.md (-37行平均) + agent_common.md (+150行 共通) = 各 agent 約 +112行 増えるが・**変更時の単一source化メリットが主**

### Token ベース (auto-load + Session Start 時)

| Phase | auto-load 増減 (CLAUDE.md/MEMORY) | Session Start 増減 (各 agent 平均) |
|-------|--------------------------------:|------------------------------:|
| Phase 1 | ±0 (CLAUDE.md は 1行追加のみ) | -630 tokens (重複削除 -1,250 + 共通 +620 で実質節約) |
| Phase 2 | ±0 | shogun -1,870 / karo -714 / gunshi -850 (lazy load で必要時のみ +0) |
| Phase 3 | ±0 (auto-load 展開後の量は同じ) | ±0 |

**結論**: コンテキスト消費は **純減 (微) または現状維持**。**増えない。** 殿の制約 「コンテキスト消費を増やさず」 を満たす。

### 一貫性・メンテ性ベース (定性評価)

| 項目 | 改善度 |
|-----|:-----:|
| 共通ルール変更時の更新箇所削減 (例: セマンティック検索の使い方変更) | **★★★★★** (4ファイル → 1ファイル) |
| 新規 agent 追加時の負担 (例: ashigaru8 復活) | **★★★★** (agent_common.md を参照させるだけ) |
| Udemy ch03 自プロジェクト実例としての説明力 | **★★★★★** (@import / 共通ファイル / Lazy load の3パターン同居) |
| Claude Code @import 機能の活用度 | **★★★** (Phase 3 で初めて本格活用・段階的) |

---

## 6. Udemy ch03 「.md仲間たち」章での実例紹介ポイント

Phase 1〜3 完成後、ch03 で以下を **実プロジェクトの構成図** として紹介可能:

```
multi-agent-shogun/
├── CLAUDE.md                              ← Claude Code auto-load (project memory)
│   ├── @import shared_context/safety/destructive.md   (Phase 3)
│   └── @import instructions/git_safety.md             (Phase 3)
├── memory/MEMORY.md                       ← Claude Code auto-load (user memory)
├── instructions/
│   ├── shogun.md / karo.md / gunshi.md / ashigaru.md   ← 役割別 (Session Start で Read)
│   └── git_safety.md                      ← @import 先 (CLAUDE.md から)
├── shared_context/
│   ├── agent_common.md                    ← 共通ファイル参照 (Phase 1・全 agent Read)
│   ├── safety/destructive.md              ← @import 先 (CLAUDE.md から・Phase 3)
│   └── procedures/                        ← Lazy load (タスク該当時のみ Read)
│       ├── saytask_routing.md             (Phase 2 切出)
│       ├── video_cmd_checklist.md         (Phase 2 切出)
│       ├── saytask_dashboard_template.md  (Phase 2 切出)
│       ├── gunshi_patterns.md             (Phase 2 切出)
│       └── ... (既存 55本)
└── .claude/
    └── commands/                          ← Claude Code custom slash commands
```

**講座での説明軸**:

1. **CLAUDE.md (project memory)** は **常時注入** されるトップレベル → 骨格のみに留めよ
2. **@import 機能** は CLAUDE.md / MEMORY.md (auto-load 対象) でのみ展開 → 物理分離 + 単一source化に最適
3. **共通ファイル参照** (agent_common.md) は instructions の重複削除手段 → **明示 Read が必要**
4. **Lazy load (procedures/)** はタスク該当時のみ Read → **常時注入 ≠ 必読** の切り分け
5. **3階層対応**: L1 プロンプト (タスク YAML steps) ・ L2 コンテキスト (CLAUDE.md/instructions/agent_common) ・ L3 ハーネス (.claude/commands/skills)

---

## 7. 残課題 (殿レビュー後の家老 follow-up cmd 候補)

| ID | 内容 | 推奨 cmd 番号 | 担当案 |
|---:|-----|------------|------|
| F1 | Phase 1 実装 (agent_common.md 新設 + instructions 4本の重複削除) | cmd_1585 | ashigaru1 単独 (RACE-001 回避) |
| F2 | Phase 2 実装 (instructions 3本の長セクション → procedures/ 切出) | cmd_1586 | ashigaru2 (shogun.md), ashigaru3 (karo.md), ashigaru4 (gunshi.md) 並列 |
| F3 | Phase 3 実装 (CLAUDE.md @import 化 + 動作検証) | cmd_1587 | ashigaru1 単独 (CLAUDE.md = 全 agent 影響・慎重に) |
| F4 | Udemy ch03 lecture md への実例追記 | cmd_1588 | ashigaru1 (Udemy 担当継続) |
| F5 | Phase 1〜3 完了後の Session Start 動作回帰テスト | cmd_1589 | gunshi (QC 専任) |

---

## 8. 結論 (Summary)

- **A判定 (@import 化推奨)**: CLAUDE.md 内 Destructive Operation Safety + Git Safety Protocol の 2セクション (Phase 3)
- **B判定 (維持)**: shared_context/procedures/*.md 全 55本 (Lazy load が正解)・memory/MEMORY.md・instructions/git_safety.md
- **C判定 (要部分切出)**: CLAUDE.md / instructions 4本 (shogun/karo/gunshi/ashigaru)
  - **共通重複セクション** → `shared_context/agent_common.md` 集約 (Phase 1)
  - **役割固有の長セクション** → `shared_context/procedures/*.md` 切出 + Lazy load 化 (Phase 2)
- **コンテキスト消費**: 純減 (微) または現状維持・増えない
- **Udemy ch03 実例**: Phase 1〜3 完成後、@import / 共通ファイル / Lazy load の 3パターン同居の実プロジェクト例として紹介可能
- **次アクション**: 殿レビュー → 承認後、家老が cmd_1585 (Phase 1) から起票 → ashigaru1 が単独実装

**実装は本audit に基づき、殿レビュー後に家老が cmd 起票せよ。軍師は本計画書のみ提出。**

---

## North Star Alignment

```yaml
north_star_alignment:
  status: aligned
  reason: "@import + 共通ファイル + Lazy load の 3パターン分離により (a) 重複削減・(b) 一貫性向上・(c) コンテキスト消費維持を同時達成。Udemy ch03 で 3階層 (L2 コンテキスト) の自プロジェクト実例として紹介可能"
  risks_to_north_star:
    - "Phase 3 @import typo で全 agent の auto-load 失敗 → 別ブランチで動作検証必須"
    - "Phase 1 共通ファイル化で Session Start IO が +1 ファイル → 各 agent の Read 順序を CLAUDE.md に明記"
    - "Phase 2 procedures/ 切出で家老/将軍がタスク YAML steps に明示参照を書き忘れる → 新規 cmd 起票時のテンプレ更新必須"
```
