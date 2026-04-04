---
name: collective-select
description: |
  HL/SH候補の並列集合知選定スキル。足軽5人（Claude3+GPT1+Gemini1）で独立分析→結果を集約→投票で候補決定。
  3社LLM混合で視点の多様性を確保。
  「集合知」「候補選定」「HL/SH選定」「/collective-select」で起動。
argument-hint: "[work_dir] [video_id]"
allowed-tools: Bash, Read, Edit, Write
---

# /collective-select — 並列集合知HL/SH候補選定スキル（3社LLM混合版）

## North Star

足軽5人（Claude3+GPT1+Gemini1）の独立分析を並列実行し、投票ベースでHL/SH候補を選定する。3社LLMの異なる視点で意外性のある候補も拾う。

## 概要

```
足軽1(Claude Opus): 分析 ─┐
足軽2(Claude Opus): 分析 ─┤
足軽3(Claude Opus): 分析 ─┼→ 家老が集約 → 殿に提示
足軽4(Codex GPT):   分析 ─┤
足軽5(Gemini):      分析 ─┘
```

3社混合の狙い: Claude組が見逃す候補をGPT/Geminiが拾う。同じ結論なら確信度UP。

## 実行手順（家老が実施）

### Phase 1: 準備

1. インプットファイルを `shared_context/collective_{video_id}.md` に配置:
   - 動画タイトル・概要
   - merged JSONのパス（`work/srt_and_candidates/merged_{video_id}.json`）— **SRT禁止。merged JSONを入力とする**
   - メンバー情報: `context/member_profiles.yaml` 参照指示
   - 動画の文脈（シリーズもの等あれば補足）

2. 足軽5人のモデルを切替:
   ```bash
   # Claude組（足軽1-3）をOpusに
   for i in 1 2 3; do
     bash scripts/inbox_write.sh ashigaru${i} "/model opus" model_switch karo
   done

   # GPT組（足軽4）をCodexに切替
   # 事前に足軽4のCLIをcodexに切替済みであること
   # 未切替なら: bash scripts/switch_cli.sh ashigaru4 --type codex
   # 起動コマンド: codex --search --dangerously-bypass-approvals-and-sandbox --no-alt-screen

   # Gemini組（足軽5）をGeminiに切替
   # 事前に足軽5のCLIをgeminiに切替済みであること
   # 未切替なら: 足軽5のpaneで /exit → gemini --sandbox=false --yolo
   ```

   **注意**: Codex/Geminiの起動は家老ではなく手動対応が必要な場合あり（switch_cli.shのバグ未修正）。
   tmux send-keysでの入力がClaude CLIと挙動が異なる点に注意。

3. 各足軽に以下のタスクYAMLを配布（5人とも同一内容。GPT/Geminiも日本語で回答可能）

### Phase 2: 分析プロンプト（タスクYAMLのcommandに記載）

```
## タスク
以下の動画から、ハイライト（HL）とショート（SH）の候補を選定せよ。
お前の分析は他の4人の分析と統合される。独立した視点で選べ。

## インプット（全部読め）
- 動画情報・merged JSON・ライブチャット: shared_context/collective_{video_id}.md を読め（SRTではなくmerged JSONのパスが記載されている）
- メンバー情報: projects/dozle_kirinuki/context/member_profiles.yaml
- HLナレッジ: projects/dozle_kirinuki/context/highlight_knowledge.md（§3.2選定基準・§3.3.1入力ソースを特に熟読）
- SHナレッジ: projects/dozle_kirinuki/context/shorts_knowledge.md
- HLテンプレ: projects/dozle_kirinuki/context/highlight_command_template.md（selected.jsonフォーマット）
- SHテンプレ: projects/dozle_kirinuki/context/shorts_command_template.md（selected.jsonフォーマット）
- 表情設計: projects/dozle_kirinuki/context/expression_design_v5.md

## HL選定基準（詳細は highlight_knowledge.md §3.2 を参照）
- 視聴者が「この動画見たい」と思うシーンを選べ
- 質>尺。10秒でも面白ければ入れろ。時間稼ぎ禁止
- 合計4-6シーン。8分超を狙えるならなお良い
- フック（冒頭つかみ）に最適なシーンを1つ指定せよ
- 各シーンは「フック→展開→オチ」の3要素必須
- 1シーン1話題（複数話題混在禁止）。途中開始・途中終了禁止
- 各シーン最大80秒
- エンドロール（本日もご視聴〜以降）は絶対含めない
- 収益化NGワード禁止: 死、殺、血、グロ等 → やられる/終わるに言い換え
- intro禁止区間: 動画の最後10%（ネタバレ防止）

## SH選定基準（詳細は shorts_knowledge.md を参照）
- ショート単体で面白いこと。面白ければ内輪ネタでもOK
- 視覚的インパクト・リアクション・オチの明確さを重視
- 数合わせ禁止。面白くないなら0本でいい。面白ければ何本でもいい

## 出力フォーマット（厳守）
### HL候補
1. **シーン名**（10文字以内）
   - タイムスタンプ: MM:SS〜MM:SS
   - メインスピーカー: {member_key}
   - 選定理由: （なぜ面白いか1行）
   - フック適性: あり/なし
   - confidence: 1-5（5=絶対入れるべき）

### SH候補
1. **シーン名**（10文字以内）
   - タイムスタンプ: MM:SS〜MM:SS
   - メインスピーカー: {member_key}
   - 選定理由: （なぜ面白いか1行）
   - 形式: 表情切替/漫画/ゲーム画面カット
   - confidence: 1-5

### 全体コメント
- この動画の一番の見どころは何か（1行）
- HL構成のおすすめ順序（フック→本編→オチ）
```

### Phase 3: 集約（家老が実施）

1. 5人の報告YAMLを読む
2. 以下のルールで集約:

| 投票数 | 扱い |
|--------|------|
| 3人以上が選んだシーン | **採用候補**（殿に推薦） |
| 2人が選んだシーン | **準候補**（殿に提示、判断を仰ぐ） |
| 1人だけが選んだシーン | **ユニーク候補**（独自視点として殿に提示） |

3. confidence平均で優先度ソート
4. フック適性ありのシーンを冒頭候補として明記
5. 結果をダッシュボードに記載し殿に提示

### Phase 4: 後片付け

1. Claude組（足軽1-3）をSonnetに戻す:
   ```bash
   for i in 1 2 3; do
     bash scripts/inbox_write.sh ashigaru${i} "default" model_switch karo
   done
   ```
   ※ "default"でsettings.yamlのデフォルトモデルに自動復帰（inbox_watcher対応済み）

2. GPT組（足軽4）をClaudeに戻す:
   足軽4のpaneで /exit → claude --model sonnet --dangerously-skip-permissions
   または: bash scripts/switch_cli.sh ashigaru4 --type claude

3. Gemini組（足軽5）をClaudeに戻す:
   足軽5のpaneで /exit → claude --model sonnet --dangerously-skip-permissions
   または: bash scripts/switch_cli.sh ashigaru5 --type claude

4. `shared_context/collective_{video_id}.md` はそのまま残す（再分析時に再利用）

## 注意事項

- **最終決定は殿**。AIの投票結果は参考。殿が1本しか選ばなくてもそれが正解
- **数合わせ禁止**。5人が全員「SH候補なし」なら0本で報告
- **面白さの判断基準は殿の感覚**。AIのvirality scoreやconfidenceは参考値でしかない
- SRTが長い場合（4000行超）は要約せず全文を渡せ。LLMに判断させるなら全文が必要
- 足軽のモデル切替は家老の責任。切替忘れ・戻し忘れに注意
- **モデル戻しは "default" を使え**（/model sonnet[1m]にするな。rate limit死する）
- Geminiは `--yolo` 必須（なしだと毎回コマンド許可を求めて止まる）
- Codexは `--dangerously-bypass-approvals-and-sandbox --no-alt-screen` 必須
- Geminiが英語で回答する場合あり。プロンプトに「日本語で回答せよ」を追加してもよい
- 集約時にGPT/Gemini独自候補は「LLM独自視点」としてマーク（多様性の指標）
