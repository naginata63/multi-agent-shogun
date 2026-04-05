#!/usr/bin/env python3
"""
CDP汎用画像生成スクリプト

Chrome CDP (port 9222) 経由でGemini Web UIを操作して画像を生成する。
漫画パネル以外の用途（note挿絵等）でもCDP方式（無料）で画像生成可能。

使い方:
  python3 scripts/cdp_image_gen.py \
    --prompt "生成したい画像の説明" \
    --output /path/to/output.jpg

  # リファレンス画像付き
  python3 scripts/cdp_image_gen.py \
    --prompt "..." --output out.jpg --ref-image ref.png

前提条件:
  - Chrome CDP port 9222 が起動していること
  - cdp_gemini_image_poc.py が存在すること
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# CDP基盤スクリプト
CDP_POC_SCRIPT = Path(__file__).resolve().parent.parent / "projects" / "dozle_kirinuki" / "scripts" / "cdp_gemini_image_poc.py"
CDP_URL = "http://localhost:9222"


def check_cdp_port():
    """CDP Chrome port 9222が起動しているか確認する。"""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/version")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="CDP汎用画像生成スクリプト (Chrome CDP経由・無料)",
        epilog="例: python3 cdp_image_gen.py --prompt '青い丸' --output test.jpg"
    )
    parser.add_argument("--prompt", required=True, help="画像生成プロンプト")
    parser.add_argument("--output", required=True, help="出力ファイルパス (jpg)")
    parser.add_argument("--ref-image", default=None, help="リファレンス画像パス（省略可）")
    parser.add_argument("--size", default="1024x1024",
                        help="画像サイズ（省略可・デフォルト1024x1024）。"
                             "注: CDP方式はGemini Web UIのデフォルトサイズで生成されるため、"
                             "この値はプロンプトに補足として追加されるのみ。")
    args = parser.parse_args()

    # CDP port確認
    if not check_cdp_port():
        print("[error] Chrome CDP port 9222 に接続できない。以下で起動してから再実行せよ:")
        print("  google-chrome --remote-debugging-port=9222 --user-data-dir=/home/murakami/.chrome-cdp &")
        sys.exit(1)

    # CDP基盤スクリプト確認
    if not CDP_POC_SCRIPT.exists():
        print(f"[error] CDP基盤スクリプトが見つからない: {CDP_POC_SCRIPT}")
        sys.exit(1)

    # リファレンス画像確認
    if args.ref_image and not Path(args.ref_image).exists():
        print(f"[error] リファレンス画像が見つからない: {args.ref_image}")
        sys.exit(1)

    # 出力ディレクトリ
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 一時出力ディレクトリ（cdp_gemini_image_poc.pyはディレクトリに出力）
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp(prefix="cdp_image_gen_"))

    # サイズ情報をプロンプトに補足（CDP自体はサイズ制御不可）
    prompt = args.prompt
    if args.size != "1024x1024":
        w, h = args.size.split("x")
        prompt += f"\nImage aspect ratio: {w}x{h} pixels, landscape orientation." if int(w) > int(h) else \
                  f"\nImage aspect ratio: {w}x{h} pixels, portrait orientation."

    # cdp_gemini_image_poc.pyを実行
    cmd = [sys.executable, str(CDP_POC_SCRIPT),
           "--prompt", prompt,
           "--out", str(tmp_dir)]
    if args.ref_image:
        cmd.extend(["--ref-image", args.ref_image])

    print(f"[cdp_image_gen] プロンプト: {args.prompt[:80]}...")
    print(f"[cdp_image_gen] 出力先: {output_path}")
    if args.ref_image:
        print(f"[cdp_image_gen] リファレンス: {args.ref_image}")

    result = subprocess.run(cmd, timeout=660)

    if result.returncode != 0:
        print(f"[error] CDP基盤スクリプトが失敗 (exit code {result.returncode})")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(1)

    # 生成された画像を検索
    jpgs = sorted(tmp_dir.glob("*.jpg"))
    if not jpgs:
        pngs = sorted(tmp_dir.glob("*.png"))
        if pngs:
            jpgs = pngs
    if not jpgs:
        print("[error] 生成された画像が見つからない")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(1)

    # 最初の画像を指定パスにコピー
    shutil.copy2(jpgs[0], output_path)
    size_kb = output_path.stat().st_size // 1024
    print(f"[cdp_image_gen] 完了: {output_path} ({size_kb}KB)")

    # 一時ディレクトリ掃除
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # 成功時は出力パスを標準出力
    print(str(output_path))


if __name__ == "__main__":
    main()
