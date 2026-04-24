# cmd_1452 Phase1 Disk Cleanup Plan (棚卸しのみ・rm 禁止)

## メタ情報
- **作成者**: ashigaru4
- **作成日時**: 2026-04-24T23:55 JST
- **Phase**: 1 (棚卸し・非破壊)
- **target_path**: `/home/murakami/multi-agent-shogun/work/cmd_1452/disk_cleanup_plan.md`
- **rmは Phase3 以降** (Phase2 殿承認ゲート後)
- **CLAUDE.md D001 Tier1 禁忌パス除外済**

## 1. 現状 (df -h)

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb4       961G  800G  112G  88% /
```

- 使用率 **88%** (現在)
- 目標 **80%以下** → 最低 **約77GB** 削除必要 (961*0.08=77G)
- 入力目標「80GB回収」はこれに概ね一致

## 2. トップレベル構成 (`du -xh --max-depth=2 /home/murakami` より)

| path | size | 備考 |
|------|------|------|
| `/home/murakami/multi-agent-shogun/projects` | 552G | **99%が dozle_kirinuki/work (動画素材)** |
| `/home/murakami/.cache` | 48G | HF/pip/chrome/playwright等 |
| `/home/murakami/.claude_glm` | 25G | GLM プロファイル |
| `/home/murakami/ダウンロード` | 12G | 個人 DL 群 |
| `/home/murakami/.local` | 11G | Python user-site等 |
| `/home/murakami/multi-agent-shogun/work` | 9.9G | cmd_1424 が 9.4G |
| `/home/murakami/multi-agent-shogun/work_使用禁止フォルダ` | 8.2G | 名前通り凍結済archive |
| `/home/murakami/multi-agent-shogun/.venv` | 7.8G | Python venv |
| `/home/murakami/multi-agent-shogun/venv` | 7.5G | Python venv (重複候補) |
| `/home/murakami/.claude` | 7.4G | projects 6.3G |
| `/home/murakami/multi-agent-shogun/tools` | 6.4G | tool install群 |
| `/home/murakami/multi-agent-shogun/remotion-project` | 5.2G | remotion |
| `/home/murakami/multi-agent-shogun/venv_whisper` | 4.9G | WhisperX venv |

## 3. 削除候補テーブル (属性6項目)

凡例:
- **推奨判定**: `SAFE`=安全削除可 / `NEEDS_LORD_REVIEW`=殿確認要 / `KEEP`=削除推奨しない / `HOLD`=Phase2 再検討

### 3.1 Tier-A: SAFE (高信頼・再生成可能キャッシュ+明示tmp)

| path | size | mtime | 削除根拠 | リスク | 推奨判定 |
|------|------|-------|----------|--------|----------|
| `~/.cache/huggingface` | **28G** | 継続使用 | HF model cache・再DL可 | ★pin保護推奨 (§7 #4 参照)・単純 rm -rf 禁止・`huggingface-cli cache scan` で使用中モデル除外要 | SAFE (pin保護付き) |
| `~/.cache/pip` | **12G** | 継続使用 | pip DL cache・再DL可 | pip install初回遅延 | SAFE |
| `/tmp/remotion-webpack-bundle-iTEHrL` | **4.7G** | (要確認) | remotion ビルド tmp | 進行中 remotion job あれば影響 | SAFE (remotion未稼働時) |
| `/tmp/remotion-v4.0.447-assetsq73itspakc` | **4.6G** | (要確認) | remotion assets tmp | 同上 | SAFE (remotion未稼働時) |
| `/tmp/react-motion-renderURuQdd` | **4.1G** | (要確認) | render tmp | 同上 | SAFE (remotion未稼働時) |
| `/tmp/dozle_kirinuki.backup.1777030230` | **3.8G** | 2026-04-24 20:30 | **既知**: cmd_1446 filter-repo 完遂済 backup | 既に履歴書換 commit済なので不要 | SAFE |
| `~/.cache/google-chrome` | **3.1G** | 継続 | chrome cache・再生成可 | Chrome再起動時 cache 再構築 | SAFE |
| `~/.cache/ms-playwright` | **2.1G** | 継続 | playwright browsers・再DL可 | E2E test の browser 再DL | SAFE |
| `/home/murakami/multi-agent-shogun/work/cmd_1424` | **9.4G** | 2026-04-22〜23 | **既知**: cmd_1424 完遂済 (DAY6 multi-view audio verify) | 再計算時中間 segment 再生成要 | SAFE |
| **Tier-A 小計** | **約71.8G** | | | | |

### 3.2 Tier-B: NEEDS_LORD_REVIEW (削除可否判断要)

| path | size | mtime | 削除根拠 | リスク | 推奨判定 |
|------|------|-------|----------|--------|----------|
| `/home/murakami/multi-agent-shogun/work_使用禁止フォルダ` | **8.2G** | 2026-03-14 最終 | 名称「使用禁止」・3/14で止まっている archive | archive 参照価値 (cloud_stt_poc等の初期試作) | NEEDS_LORD_REVIEW |
| `~/.claude_glm` | **25G** (14G cache + 8.9G local) | 継続 | GLM CLI プロファイル。GLM使用時は必要 | 殿が GLM 運用停止済なら SAFE | NEEDS_LORD_REVIEW |
| `~/ダウンロード/IMG_9595.mov` | **3.9G** | (個人) | 個人動画 (殿資産) | 再取得不可の可能性 | NEEDS_LORD_REVIEW |
| `~/ダウンロード/COEIROINK_LINUX_GPU_v.2.13.0` + `.zip` | **4.4G** (2.9G+1.5G) | インストーラ | 既インストールなら .zip 削除可 | zip 消すと再DL必要 | NEEDS_LORD_REVIEW |
| `~/ダウンロード/source-han-serif-1.001R.zip` | **1.9G** | フォントzip | 展開済なら zip 不要 | 未展開なら KEEP | NEEDS_LORD_REVIEW |
| `~/ダウンロード/*.deb` 群 (chrome/vscode/discord/dingtalk) | **約700M** | 既インストール | インストール済 .deb は不要 | 再インストール時再DL必要 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20251220_超広大な山〜` | **1.5G** | 2025-12-20 | 公開済動画の素材 (推定) | 将来再編集不可 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260105_恐怖のくろねこ〜` | **1.3G** | 2026-01-05 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260111_*` (2件) | **2.6G** | 2026-01-11 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260126_ぶらり鬼畜旅〜` | **1.3G** | 2026-01-26 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260209_太陽に当たっては〜` | **1.4G** | 2026-02-09 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260214_寝ないと死ぬ世界〜` | **3.5G** | 2026-02-14 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260216_1億倍のチーズ〜` | **2.4G** | 2026-02-16 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260224_ニンジンしかない〜` | **1.5G** | 2026-02-24 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260303_超巨大ちらし寿司〜` | **3.2G** | 2026-03-03 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260312_最強のハンター〜` | **2.9G** | 2026-03-12 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260313_嘘つきだらけのポーカー〜` | **19G** | 2026-03-13 | 公開済ハイライト素材 | 大容量 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260314_一番乗りを目指せ〜` | **8.6G** | 2026-03-14 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260315_鉱石を掘って〜` | **5.0G** | 2026-03-15 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260319_都道府県が使える〜` | **6.3G** | 2026-03-19 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260320_おらふイングリッシュ〜` | **5.0G** | 2026-03-20 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260321_石になった友達〜` | **1.8G** | 2026-03-21 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260326_『アスレ』しかない〜` | **3.8G** | 2026-03-26 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260329_MBTIの能力〜` | **2.1G** | 2026-03-29 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260403_枯れ木に花〜` | **2.3G** | 2026-04-03 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260405_TNTしかないネザー〜` | **2.6G** | 2026-04-05 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260406_*` (5件) | **約22G** (11G+7.2G+4.7G+3.2G+2.1G+1.6G) | 2026-04-06 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260407_体力と手持ち共有〜` | **7.2G** | 2026-04-07 | 同上 | 同上 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/20260421_TNTしか使えない〜` | **5.3G** | 2026-04-21 | 最近公開 or 直前素材 | 要確認 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/clips_1286_pink_sheep` + `pink_sheep_clips` | **34G** (32G+1.8G) | (要確認) | pink_sheep クリップ群 | 未発行なら KEEP | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/auto_fetch` | **4.2G** | 自動取得 cache | 再取得可 | 再取得時間 | NEEDS_LORD_REVIEW |
| `projects/dozle_kirinuki/work/yt_subs` | **1.3G** | SRT group | 再生成可 (STTコスト発生) | AssemblyAI再実行要 | NEEDS_LORD_REVIEW |
| `~/.cache/anime-whisper-ct2` | **734M** | Whisper model | 再DL可 | 初回ロード遅延 | NEEDS_LORD_REVIEW |
| `~/.cache/whisper` | **672M** | Whisper model | 再DL可 | 同上 | NEEDS_LORD_REVIEW |
| `~/.cache/clip` | **338M** | CLIP model | 再DL可 | 同上 | NEEDS_LORD_REVIEW |
| `~/.cache/torch` | **115M** | torch cache | 再DL可 | 同上 | NEEDS_LORD_REVIEW |
| `~/.cache/thumbnails` | **543M** | OS thumb cache | 自動再生成 | 無し | SAFE (Tier-Aに繰上推奨) |
| `~/.cache/chroma` | **167M** | chroma DB cache | embedding 保持時は KEEP | 消すと embed 再計算 | NEEDS_LORD_REVIEW |
| `/tmp/claude-1000` | **22M** | claude CLI tmp | 消去可 | 無し | SAFE (Tier-Aに繰上推奨) |
| `/tmp/test_simple.mp4` + 他 `/tmp/*.mp4`/`.wav`/`.png` 軽量群 | **約10M** | テスト artifact | 無し | 無し | SAFE |
| **Tier-B 小計 (主要大物)** | **約170G** | | | | |

### 3.3 Tier-C: KEEP (現在稼働中・削除推奨しない)

| path | size | 削除推奨しない理由 |
|------|------|------|
| `projects/dozle_kirinuki/work/20260411_*Doom or Zenith*` Day1 | **22G** | #DoZ シリーズ WIP (公開待ち) |
| `projects/dozle_kirinuki/work/20260412_*Day2*` | **55G** | 同上 |
| `projects/dozle_kirinuki/work/20260413_*Day3*` | **38G** | 同上 |
| `projects/dozle_kirinuki/work/20260415_*Day5*` | **48G** | 同上 |
| `projects/dozle_kirinuki/work/20260416_*Day6*` | **107G** | **★Day6 MIX 進行中★ (cmd_1425 charlotte DL blocker)** 絶対 KEEP |
| `projects/dozle_kirinuki/work/20260417_*Day7*` | **16G** | Day7 WIP |
| `projects/dozle_kirinuki/work/20260417_*5日目ヒーラー〜*` | **25G** | **DOWNGRADED → NEEDS_LORD_REVIEW** (20260415_Day5 48G と重複候補・4/15版と差異確認要・冗長なら 25G 追加回収可) |
| `projects/dozle_kirinuki/work/20260418_*Day8*` | **18G** | Day8 WIP |
| `.venv` / `venv` / `venv_whisper` | **7.8+7.5+4.9=20.2G** | Python 実行環境 (壊すと全足軽停止) |
| `tools/` | **6.4G** | CLI tool install群 |
| `.git` | **3.7G** | リポジトリ (絶対 KEEP) |
| `.claude/projects` | **6.3G** | Claude Code session履歴 |
| `remotion-project/` | **5.2G** | 進行中 remotion project |

Tier-C 合計 約 **330G** は絶対 KEEP。

## 4. Tier-1 禁忌パス除外確認 (CLAUDE.md D001)

以下は本plan に**一切含まない**:
- `/`, `/mnt/c/*`, `/mnt/d/*`, `/home/*`, `~`
- `/mnt/c/Windows/`, `/mnt/c/Users/`, `/mnt/c/Program Files/`
- システムパス (`/usr`, `/bin`, `/etc`, `/var` の外部)
- 本plan の削除候補はすべて `/home/murakami/` 配下 (workingtree内 or 明示 tmp/cache)

## 5. 目標達成性評価

| Tier | 合計 | 達成貢献 |
|------|------|----------|
| Tier-A (SAFE) | 約 **72G** | 単独で目標 77GB の **93%** |
| Tier-A + thumbnails/claude-1000/tmpzakako | 約 **73G** | 目標ほぼ到達 |
| Tier-B 一部 (公開済動画 20251220〜20260320 = 約 50G) 追加 | **+50G** | **合計 123G** → 80%→約 75% まで下がる余力 |

**結論**: Tier-A だけで **目標 80%ライン (77G 削減) にほぼ届く**。Tier-B の「公開済動画 work dir」数件殿承認があれば **一気に 70%台へ** 下げられる。100GB以上の余力がある。

## 6. advisor 指摘反映ログ

| 指摘 | 対応 |
|------|------|
| task YAML Step 6 `find -size +1G` は dir entry (~4KB) しか測れない | `du -xh --max-depth=2 /home/murakami` に置換済。実効結果ここに反映 |
| du -x で同一 fs 限定 | 採用済 (`/mnt/c`,`/sys`,`/proc` 不走査) |
| `80G回収` は input goal・実測優先 | Tier-A 実測 72G + Tier-B 候補として honest 報告 |
| 投稿済動画判定 source-of-truth | manifest 不明瞭のため全て `NEEDS_LORD_REVIEW`・推測 keep しない |
| 既知候補 2 件の存在確認 | `/tmp/dozle_kirinuki.backup.1777030230` (3.8G) + `work/cmd_1424` (9.4G) いずれも存在確認済 |
| markdown table 出力 | 採用済 |
| log 保存先 | `/tmp/` 禁止・pretool_check により work/cmd_1452/ 以外書込不可 → 本 md に stdout 転記 |

## 7. Phase 2 殿承認ゲート向け要点

1. **Tier-A 約72GB** は家老→殿に即時承認要請推奨
2. **Tier-B 公開済動画** は analytics/published_at と video_id を突合する手間があるため Phase2 で殿判断ルール化推奨 (例: 「mtime 30日以上前 かつ analytics 公開済 ⇒ 削除対象化」)
3. **`/tmp/remotion-*` 3件 (13.4GB)** は Phase3 rm 前に `lsof /tmp/remotion-*` で稼働中プロセス無確認必須 (remotion render job blocker回避)
4. **`~/.cache/huggingface` (28GB)** は一括 `rm -rf` ではなく `huggingface-cli cache scan` で pin 保護推奨。安全化 step 必要
5. **禁忌確認**: Phase3 rm 対象 path を realpath で 1件ずつ解決し `/mnt/c`, `/`, `/home` bare 等に resolve しないこと確認必須
6. **★submodule 注意★**: `projects/dozle_kirinuki` は git submodule (session start 時 `m` dirty flag あり)。`projects/dozle_kirinuki/work/*` 配下を rm する場合、先に submodule 側で `cd projects/dozle_kirinuki && git status` → 作業中であれば stash/commit → 親 repo 側で rm の順。ignore対象でも untracked が混ざると submodule worktree が壊れる
7. **目標ライン薄氷**: ext4 は 5% 予約領域あり。df 88% は使用可能 ~913G ベース。80% 到達には **実質 70GB 回収**。Tier-A 72GB で ~80.1% と**ギリギリ**。Tier-B 追加数件 (Day5 重複25G・公開済動画群) で余裕確保推奨

## 8. 未解決ギャップ / 既知限界

- 公開済動画の manifest: `dozle_kirinuki/analytics/` に published_at JSON はあるが video_id ↔ work dir 名 のマッピング無し。Phase2 で殿 or 軍師にルール化要請
- `~/.claude_glm` (25G) は殿 GLM 運用方針依存。cmd_1450 付近で GLM 停止方針があれば SAFE に繰上げ可
- `ダウンロード/` 個人ファイルは原則 KEEP (殿資産)。殿本人の削除指示のみ有効

## 9. Phase 2/3 向けコマンド案 (★Phase3 までは実行禁止★)

```bash
# Tier-A (72G) 削除例 (殿承認後 Phase3 で実行)
rm -rf ~/.cache/huggingface      # 28G
rm -rf ~/.cache/pip              # 12G
rm -rf /tmp/remotion-webpack-bundle-iTEHrL       # 4.7G
rm -rf /tmp/remotion-v4.0.447-assetsq73itspakc   # 4.6G
rm -rf /tmp/react-motion-renderURuQdd            # 4.1G
rm -rf /tmp/dozle_kirinuki.backup.1777030230     # 3.8G
rm -rf ~/.cache/google-chrome    # 3.1G
rm -rf ~/.cache/ms-playwright    # 2.1G
rm -rf /home/murakami/multi-agent-shogun/work/cmd_1424   # 9.4G

# Phase4 検証
df -h /    # 80%以下確認
```

## 10. まとめ

- 削除候補 **Tier-A 約72G + 即時SAFE小物 1G ≒ 73G** で目標 77G 削減の 95% 到達
- 不足分は **Tier-B (公開済動画群 50GB+)** から殿判断で補う形が現実的
- **Day6 MIX (107G)** は絶対保護・cmd_1425 blocker
- **Phase1 は棚卸しのみ**・Phase2 殿承認後に Phase3 rm 別発令
- advisor 指摘 (task YAML Step 6 の find -size +1G 誤り) は本報告書で是正 + 家老へ口頭共有要
