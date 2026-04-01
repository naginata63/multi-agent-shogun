# CDP方式 リファレンス画像添付 + 縦型9:16 検証レポート (v2)

生成日時: 2026-04-02
担当: 足軽4号 (subtask_1074a)
前回参照: projects/dozle_kirinuki/work/cmd_1065/comparison_report.md

---

## 概要

cmd_1065での「CDP方式は16:9固定で縦型不可」という結論に対し、殿の指摘：
- 「リファレンス画像を入れたか？」
- 「縦型もできるだろ、指定してないだけじゃん」

上記を踏まえてリファレンス画像添付 + 縦型指定での再テストを実施した。

---

## 実施内容

### 実装完了項目

1. **スクリプト改修** (`work/cmd_1074/cdp_gemini_with_ref.py`)
   - リファレンス画像添付機能を追加 (Playwright `setInputFiles()` 方式)
   - ファイル添付ボタン候補セレクタを10種類用意
   - `input[type="file"]` を直接操作するフォールバック実装
   - プロンプトに縦型指定を追加:「9:16の縦型、768×1376ピクセルで生成してください」
   - P1/P3の両パネルに適切なキャラクターリファレンス画像を設定:
     - P1 (ぼん): `bon_skeptical_r1_rgba.png` + `oo_men_smug_r1_rgba.png`
     - P3 (MEN): `oo_men_smug_r2_rgba.png` + `bon_surprise_r1_rgba.png`

2. **リファレンス画像添付テスト**
   - ファイル添付ボタンの発見: **失敗**（Geminiのファイル入力要素が見つからない）
   - 考察: Gemini UIのファイル添付はDrag & Drop方式かチャット欄のclipboard操作で、`input[type="file"]` が通常の方法では操作できない可能性

---

## 認証問題の発見（重大）

### 問題の詳細

テスト実行中、Gemini UIへの認証が失敗することを発見した。

| テスト | 結果 | 詳細 |
|--------|------|------|
| `--update-cookies` でCookie再読み込み | 成功 | 31件復号完了 |
| Playwright persistent context + add_cookies | 失敗 | 「ログイン」表示 |
| Playwright non-persistent context + add_cookies | 失敗 | 「ログイン」表示 |
| 実Chromeプロファイルコピー（Cookies+LocalStorage+IndexedDB） | 失敗 | 「ログイン」表示 |
| curl + Cookie文字列 | 成功（HTTP 200）| ただしSPAの動的コンテンツは未確認 |

### 根本原因の推察

1. **Device Bound Session Credentials (DBSC)**
   - Google Chrome 123以降で段階ロールアウト中
   - セッションクッキーをデバイス固有の秘密鍵にバインド
   - 別の Chrome プロセス（Playwright）では鍵が一致せず認証失敗
   - 2026-04-01（cmd_1065実行時）は未展開だったが、2026-04-02に適用された可能性

2. **セッション失効**
   - cmd_1057/cmd_1065 (2026-04-01) 以降に Google がセッションを無効化した可能性
   - 同一機器の別 Chrome インスタンスでも認証失敗することから DBSC の可能性が高い

### 影響

- **CDP方式での Gemini UI 操作が現在不可能**
- Cookie injection 経由での認証が機能しない
- cmd_1057 PoC (2026-04-01) は成功、cmd_1074 (2026-04-02) は失敗

---

## Geminiサーバー障害（補足）

- テスト中 `https://gemini.google.com/app` が約25分間 502 エラーを返した（00:00-00:25 JST）
- 復旧後も認証問題により画像生成には至らなかった

---

## ファイル添付機能についての考察

### 実装した添付ロジック

```python
# 1. ファイル添付ボタン候補を10種のセレクタで探索
# 2. 見つかればクリックして input[type="file"] を探す
# 3. setInputFiles() でリファレンス画像を設定
```

### Gemini UIのファイル添付の実態

GeminiのWeb UIでは：
- **PC版**: テキストエリアの右側に「+」または画像アイコンがある
- **セレクタ**: 動的に生成されるため固定パスが困難
- **method**: ファイル選択ダイアログまたはドラッグ＆ドロップ

認証が復旧した場合のトライ方法:
```python
# ファイル添付ボタンの実際のセレクタを特定する追加調査が必要
# 候補: [aria-label="画像を追加"], button.upload-button, etc.
```

---

## 縦型指定についての考察

殿の指摘「縦型もできるだろ、指定してないだけじゃん」について：

### cmd_1065の問題

cmd_1065のプロンプトには縦型指定がなかった:
```
# cmd_1065のプロンプト（縦型指定なし）
"Minecraft 3D render style manga panel. MEN (blocky pink/magenta...)..."
```

→ 結果: 1024×559px (16:9横型)

### cmd_1074で追加した縦型指定

```
"IMPORTANT: Generate in 9:16 portrait orientation, 768×1376 pixels. "
"縦型9:16フォーマット、768×1376ピクセルで生成してください。"
```

### 縦型指定の有効性（推察）

Gemini UIでの実験ログ（他ユーザー報告）によれば:
- テキストで「縦型」「portrait」「9:16」を指定すると縦型画像が生成される
- ただしGemini 2.0 Flash Imageはデフォルトが1:1または16:9

**殿の主張は正しい可能性が高い** - 認証問題が解決すれば縦型指定で縦型画像が生成できると考えられる。

---

## 結論

| 検証項目 | 結果 |
|---------|------|
| ファイル添付機能の実装 | ✅ 実装済み（認証問題で未テスト） |
| 縦型指定の実装 | ✅ 実装済み（認証問題で未テスト） |
| 実際の縦型画像生成 | ❌ 認証失敗により不可 |
| リファレンス画像の反映確認 | ❌ 認証失敗により不可 |

### 推奨アクション

1. **認証問題の解決が必要**
   - DBSC対策: `--remote-debugging-port` でリアルChromeに接続するアプローチ
   - または: Chrome を `--remote-debugging-port=9222` で起動してPlaywrightがCDPで接続

2. **接続方法の変更案**
   ```python
   # 現行: launch_persistent_context (別Chromeインスタンス)
   # 変更: connect_over_cdp("http://localhost:9222") (既存Chromeインスタンスに接続)
   playwright.chromium.connect_over_cdp("http://localhost:9222")
   ```
   ただし Chrome を `--remote-debugging-port=9222` で起動する必要あり

3. **代替案**
   - Chrome拡張機能経由でのファイル操作
   - xdotoolによるGUI操作（headed mode必須）
   - または Gemini API（課金）での縦型+リファレンス生成に戻る

---

## ファイル一覧

```
work/cmd_1074/
├── cdp_gemini_with_ref.py          # 改修スクリプト（リファレンス添付+縦型対応）
├── execution_log.txt               # 実行ログ (attempt 1)
├── execution_log_v2.txt            # 実行ログ (attempt 2 - 認証失敗)
├── result_log_v2.json              # 実行結果JSON
├── snap_before_submit_p1.png       # P1送信前スクリーンショット（未ログイン状態）
├── snap_after_gen_p1.png           # P1生成後スクリーンショット（ログイン要求）
├── snap_before_submit_p3.png       # P3送信前スクリーンショット
├── snap_after_gen_p3.png           # P3生成後スクリーンショット
└── comparison_v2.md                # 本レポート
```
