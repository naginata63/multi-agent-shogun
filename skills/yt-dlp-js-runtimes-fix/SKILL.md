---
name: yt-dlp-js-runtimes-fix
description: |
  yt-dlp で YouTube 動画 DL 時に n-challenge solving failed / Sig extraction failed / nsig extraction failed
  などの bot 検知エラーが出たら、`--js-runtimes node` を追加して node v20+ で n-challenge を突破する。
  「yt-dlp 失敗」「n-challenge」「Sig extract failed」「nsig 抽出失敗」「YouTube DL bot 検知」「js-runtimes」で起動。
  Do NOT use for: yt-dlp の通常 DL（素材取得は /video-pipeline を使え）。
  Do NOT use for: cookies / impersonate 系の認証エラー（それは別 hotfix）。
allowed-tools: Bash, Read
---

# yt-dlp-js-runtimes-fix — yt-dlp n-challenge 突破スキル

## North Star

YouTube 側の bot 検知（n-challenge / Sig extraction）で yt-dlp が DL 失敗した時、
`--js-runtimes node` 1 オプション追加で復旧させ、足軽が 5 手法試行する無駄を排除する。

## 起動トリガー（症状）

以下のいずれかが yt-dlp の stderr / log に出たら本スキル発動：

| 症状 | 例 |
|------|-----|
| n-challenge 失敗 | `n-challenge solving failed` |
| Sig 抽出失敗 | `Signature extraction failed: Some formats may be missing` |
| nsig 抽出失敗 | `nsig extraction failed: Some formats may be missing` |
| 動画形式取得不可 | `Requested format is not available` （n-challenge 起因の場合） |

## 根本原因

yt-dlp 2026.03.17 以降、デフォルト JS runtime が **deno** になった。
deno 未インストール環境では n-challenge を解けず、YouTube 側の動画 URL 署名が取得できない。

| Runtime | 既存 | 備考 |
|---------|------|------|
| deno | ✗ 未インストール | yt-dlp デフォルト |
| **node** | ✓ v20.20.0 既存 | 本スキルで利用 |
| firefox | ✗ 未インストール | impersonate 用 |

## 解決策（1 行追加）

```bash
yt-dlp --js-runtimes node <URL>
```

既存の yt-dlp コマンドに `--js-runtimes node` を追加するだけ。他オプション（`-f`, `--cookies-from-browser` 等）はそのまま維持。

## 実証例（cmd_1425 シャルロット案件）

| 項目 | 内容 |
|------|------|
| 動画 ID | `v19JAnVjZ_c`（シャルロット 8h55m） |
| 失敗手法 | chrome cookies / CDP cookies / firefox / impersonate / cookies.txt（5 手法全滅） |
| 成功手法 | CDP cookies + `--js-runtimes node` |
| 成果 | day6_charlotte_full.mp4 32151s / 11.3GB DL 成功 |
| QC 判定 | gunshi_report_qc_1425c2.yaml: PASS |

実行例：
```bash
yt-dlp \
  --cookies-from-browser chrome:Default \
  --js-runtimes node \
  -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
  -o "/path/to/output.%(ext)s" \
  "https://www.youtube.com/watch?v=v19JAnVjZ_c"
```

## 検証コマンド

### 環境確認

```bash
# node の存在確認（v20+ 必須）
node --version
# 期待: v20.20.0 以上

# yt-dlp が --js-runtimes を認識するか確認
yt-dlp --help 2>&1 | grep js-runtimes
# 期待: --js-runtimes RUNTIMES の行が表示される
```

### 動作確認（短い動画で試走）

```bash
# 30 秒だけ DL してエラー有無確認
yt-dlp --js-runtimes node --download-sections "*0-30" -o /tmp/test.%(ext)s "<URL>"
echo "exit_code=$?"
# 期待: exit_code=0 かつ /tmp/test.mp4 生成
```

### 失敗時の切り分け

```bash
# まず --js-runtimes node なしで再現確認
yt-dlp -F "<URL>" 2>&1 | tee /tmp/ytdlp_no_js.log

# 次に --js-runtimes node 付きで実行
yt-dlp --js-runtimes node -F "<URL>" 2>&1 | tee /tmp/ytdlp_with_js.log

# 比較（n-challenge 系エラーが消えていれば本スキル該当）
diff /tmp/ytdlp_no_js.log /tmp/ytdlp_with_js.log
```

## 適用範囲

本スキルは以下のスクリプト / ワークフロー全てで適用可能：

- `projects/dozle_kirinuki/scripts/main.py`（DL 段）
- `projects/dozle_kirinuki/scripts/highlight_pipeline.py`
- `/video-pipeline` スキルの DL 段
- 単発の `yt-dlp` 直叩き

## ワークフロー（足軽用）

1. yt-dlp 失敗ログを Read で確認、上記「起動トリガー」に該当するか判定
2. `node --version` で v20+ を確認（未インストールなら `apt install nodejs` または別解検討）
3. 失敗した yt-dlp コマンドに `--js-runtimes node` を追加して再実行
4. 成功時：hotfix_notes に `--js-runtimes node 適用` と記録 → 報告
5. 失敗時：本スキルでは解決不可 → 別 hotfix（cookies refresh, impersonate 等）を検討

## 注意事項

- `--js-runtimes node` は **node v20+** 前提。それ以下では JS API 互換性で別エラーが出る可能性
- 本スキルは bot 検知系のみ対象。401/403（認証）/ 404（動画削除）には無効
- yt-dlp 自体が古い場合は `pip install -U yt-dlp` を先に実行
- 既存の `--cookies-from-browser` 等と併用可能（むしろ併用推奨）

## 関連参照

| 参照先 | 内容 |
|--------|------|
| `queue/reports/gunshi_report_qc_1425c2.yaml` | 軍師による HIGH 価値評価・5 手法試行履歴 |
| `work/cmd_1425/charlotte_parts.json` | シャルロット 9 パート分割実証データ |
| `.claude/commands/skill-creator.md` | スキル設計仕様（本 SKILL.md の母体） |
