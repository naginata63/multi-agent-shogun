# Remotion Architecture — dozle_kirinuki

## 概要

ドズル社切り抜きプロジェクトでは Remotion (React 動画フレームワーク) を利用し、オーバーレイ合成・漫画ショート等の動的レンダリングを行う。

## ディレクトリ構成

### remotion-overlay/ (現行・稼働中)

**用途**: Shorts・漫画・劇場風のオーバーレイ合成

| Composition ID | コンポーネント | 用途 | 解像度 |
|---|---|---|---|
| `ShortsOverlay` | ShortsComposition | ゲーム画面+テロップ+立ち絵のShorts合成 | 1080x1920 |
| `MangaShorts` | MangaComposition | 漫画パネル形式ショート | 1080x1920 |
| `TheaterOverlay` | TheaterComposition | 劇場風オーバーレイ | 1080x1920 |
| `TextAnimDemo` | TextAnimDemoComposition | テキストアニメーションパターン検証用 | 1080x1920 |

**エントリポイント**: `remotion.ts` → `src/Root.tsx` (全Composition登録)

**Python側呼出**: `main.py:render_with_remotion()` が `remotion-overlay/` を `cwd` として `remotion render` を実行。2-pass NVENC で最終エンコード。

### remotion-project/ (計画中・未作成)

**想定用途**: 長尺・プレビュー系コンポーネント

| 想定Composition | 用途 |
|---|---|
| DozPreview | 4視点プレビュー |
| DozFull | フル動画合成 |
| OrarishTelop | オラーリッシュテロップ |
| OdinCountdownTest | カウントダウン演出 |

現在は `remotion-overlay/` に集約されている。将来的に長尺系が増えた場合、責務分離のために `remotion-project/` を独立させる設計。

## 呼出フロー

```
main.py (Python)
  └→ render_with_remotion(clip, output, props, work_dir)
       └→ cwd: remotion-overlay/
       └→ node_modules/.bin/remotion render remotion.ts <CompositionId>
       └→ 中間ファイル → ffmpeg NVENC 2-pass → 最終MP4
```

`input-props-*.json` は Remotion へ渡す props (字幕・話者・色等)。`main.py` は tempfile で動的生成するため、既存JSONファイルは手動テスト用。

## 注意事項

- `npm install` は `remotion-overlay/` 直下で実行 (node_modules 管理は各Remotionプロジェクト単位)
- `vertical_convert.py` は Remotion を使わず ffmpeg 直叩き。sys.path ガードで `font_config` モジュールを解決
