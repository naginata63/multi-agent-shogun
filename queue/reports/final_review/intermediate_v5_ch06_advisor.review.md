| 観点 | 重大度 | 具体的問題 | 該当行 | 推奨対応 |
|------|--------|-----------|--------|---------|
| ⑤ スライド数 | **高** | 全21枚 (cover2枚+本編19枚)・推奨10-12枚を大幅超過 | 全体 | 【統合候補】Slide2「ch06タイトル」→Slide1 coverへ吸収/Slide16+17「実例営業+PM」→1枚2列/Slide5「ゴール」→Slide4「困りごと」と統合/Slide8「ch03-05の復習」→Slide3「前回の復習」と統合。目標15枚以内 |
| ① 致命傷 (要verify) | **中** | `type: advisor_20260301`/beta header `advisor-tool-2026-03-01`/`platform.claude.com` ドメイン — 訓練データ範囲では確認できず・公式一次ソース未verify | Slide11 | スライド内に「⚠️ beta」注記はあるが、**講師として収録前に Anthropic 公式 docs (docs.anthropic.com) で identifier・ドメインを必ず再確認**。`platform.claude.com` は `docs.anthropic.com` または `console.anthropic.com` の誤記疑い |
| ① 致命傷 (要verify) | **中** | hook「全 29 種類」と断定 | Slide15 注釈 | Anthropic公式hookイベント数は8-10程度 (PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/SubagentStop/Stop/Notification/PreCompact等) が一般的認識。29は本リポ内合意値だが**公式ドキュメント未verify**。「公式29種類」と書くなら一次ソースリンク添付・なければ「複数のライフサイクルイベント」とぼかせ |
| ③ 専門用語の唐突登場 | **中** | `server_tool_use block` / `tools 配列` / `beta header` / `executor` がSlide11-12で連続して登場・社会人2-3年目の非エンジニアには負担大 | Slide11, Slide12 | ターゲット (なんとかIT用語わかる程度) を考慮し、**JSON snippetとハイブリッド構造図はAppendix送り**または「エンジニアの方は付録参照」と分離。本編は「APIの設定で別AIを呼べる仕組み」程度に簡略化 |
| ④ フック文型 | **中** | カバータイトルが説明型「context windowを膨らませず別AIの判断を取り込む — advisor」・断定型でも痛点呼びかけでもない | Slide1 cover | 例:「AIの『大丈夫です』を信じて大恥をかいたあなたへ」(痛点)/「AIに第三者レビューを仕込む方法は3つしかない」(断定) |
| ⑥ ターゲット適合 | **中** | Slide11のJSON/beta header/API tools配列は「なんとかIT用語わかる程度」では理解困難・離脱リスク | Slide11 | JSON snippetは「設定例 (詳細は付録)」と1行に圧縮・本編は概念のみ |
| ② 論理飛躍 | **低** | Slide12「ハイブリッド構造 (executor=client / advisor=server-side)」が前提なしで登場・非エンジニアにはピンとこない | Slide12 | 「executor=あなたの手元のClaude Code、advisor=Anthropicのサーバー上の別AI」と用語の置換明示 |
| ⑦ 章間整合性 | 良 | ch03 LitM・ch04 4道具 (chunk/RAG/claude-mem/手動ドキュメント化)・ch05 3段重ね役割別ファイル+サブエージェントを正確に踏襲・ch07 hookへの橋渡しも明確 | Slide3, Slide8, Slide15 | 維持 |
| ⑧ handoff/rehydrate残存 | 良 | 該当なし (殿削除指示反映済) | — | — |
| ⑨ v4/v5/なぎなた残存 | 良 | 該当なし (殿削除指示反映済) | — | — |

**総合所見**: ch04「長文を作らない」原則の応用としてadvisorを位置づけた構造設計は秀逸で、ch03→ch04→ch05→ch06→ch07の連続性が最も整理された章。ch05既習の「サブエージェント」と本章「advisor」を *context流入量* という同一物差しで比較する切口は受講者の腑に落ちやすい。一方、**スライド21枚と圧縮必須**であり、特にSlide11 (advisor仕様JSON) はターゲット層に対して技術密度が高すぎる。`advisor_20260301`/`platform.claude.com`/「hook全29種類」の3点は訓練データで確証できず**収録前に Anthropic公式一次ソースで再verify必須**。フック文型は説明型で無難すぎ、痛点型「AIの『大丈夫です』を信じて失敗したあなたへ」等への差替を推奨。

**総合重大度**: **中** (構造・整合性は◎、スライド数圧縮+用語層の調整+一次ソースverify が必要)

**残存問題**:
- スライド数21枚 → 15枚以内に圧縮 (統合4箇所提案済)
- advisor識別子・ドメイン・hook 29種類の一次ソース未verify (収録前必須確認)
- Slide11技術密度過剰 (JSON/beta header/server_tool_use block) → 付録分離
- カバータイトルが無難 → 痛点型/断定型に差替
- Slide12「ハイブリッド構造」用語の橋渡し不足
