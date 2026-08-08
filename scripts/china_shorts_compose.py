#!/usr/bin/env python3
"""China shorts composer: JSON定義から動画合成を実行する。

Usage:
    python3 scripts/china_shorts_compose.py <compose.json> [--dry-run]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

FONTS = {
    "zero": os.path.expanduser("~/.local/share/fonts/ZeroGothic.otf"),
    "reggae": os.path.expanduser("~/.local/share/fonts/ReggaeOne-Regular.ttf"),
    "kei": os.path.expanduser("~/.local/share/fonts/keifont.ttf"),
}

BORDER_MAP = {
    "zero": 9,
    "reggae": 15,
    "kei": 11,
}

# compose.json に必須のトップレベルキー (cfg["..."] 直接アクセス対策)
REQUIRED_KEYS = {
    "source", "layers", "crop", "canvas", "fps", "bitrate",
    "cuts", "narration", "thumbnail", "output", "subtitles",
}


def validate_config(cfg: dict) -> None:
    """必須キー欠落を起動時に検出し、KeyError ではなく分かりやすいメッセージにする"""
    missing = sorted(REQUIRED_KEYS - cfg.keys())
    if missing:
        raise KeyError(
            f"compose.json に必須キーが不足しています: {missing} "
            f"(存在するキー: {sorted(cfg.keys())})"
        )


def run(cmd, dry_run=False):
    print(f"  CMD: {' '.join(cmd[:5])}... ({len(cmd)} args)")
    if dry_run:
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-500:]}")
        raise RuntimeError(f"ffmpeg failed (exit {result.returncode})")


def probe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path)
    ]).decode().strip()
    return float(out)


def step_layer(cfg, work_dir, dry_run=False):
    """Step 1: レイヤー合成（bg + overlay + crop）"""
    print("[Step1] Layer compositing...")
    src = work_dir / cfg["source"]
    bg = work_dir / cfg["layers"]["background"]
    ov = work_dir / cfg["layers"]["overlay"]
    opacity = cfg["layers"]["background_opacity"]
    crop = cfg["crop"]
    canvas = cfg["canvas"]
    fps = cfg["fps"]
    dur = probe_duration(src)
    out = work_dir / "_layered.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s={canvas['w']}x{canvas['h']}:d={dur}:r={fps}",
        "-stream_loop", "-1", "-i", str(bg),
        "-i", str(src),
        "-stream_loop", "-1", "-i", str(ov),
        "-filter_complex",
        f"[0:v]setsar=1[black];"
        f"[1:v]scale={canvas['w']}:{canvas['h']},setsar=1,format=rgba,colorchannelmixer=aa={opacity}[bg];"
        f"[2:v]crop={crop['w']}:{crop['h']}:{crop['x']}:{crop['y']},setsar=1[src];"
        f"[black][bg]overlay=0:0[layer1];"
        f"[layer1][src]overlay=(W-w)/2:(H-h)/2[layer2];"
        f"[3:v]scale={canvas['w']}:{canvas['h']},setsar=1,colorkey=white:0.3:0.2[ov];"
        f"[layer2][ov]overlay=0:0[vout]",
        "-map", "[vout]", "-map", "2:a",
        "-c:v", "h264_nvenc", "-preset", "p4", "-b:v", cfg["bitrate"], "-r", fps,
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(dur),
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, dry_run)
    print(f"  -> {out} ({dur:.1f}s)")
    return out


def step_cut(cfg, layered_path, dry_run=False):
    """Step 2: カット割り（trim + concat）"""
    print("[Step2] Cutting segments...")
    cuts = cfg["cuts"]
    n = len(cuts)
    fps = cfg["fps"]
    out = layered_path.with_name("_cut.mp4")

    # Build filter_complex
    splits_v = f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n)) + ";"
    splits_a = f"[0:a]asplit={n}" + "".join(f"[a{i}]" for i in range(n)) + ";"

    trims = ""
    concat_inputs = ""
    for i, c in enumerate(cuts):
        trims += (
            f"[v{i}]trim={c['start']}:{c['end']},setpts=PTS-STARTPTS[sv{i}];"
            f"[a{i}]atrim={c['start']}:{c['end']},asetpts=PTS-STARTPTS[sa{i}];"
        )
        concat_inputs += f"[sv{i}][sa{i}]"

    concat = f"{concat_inputs}concat=n={n}:v=1:a=1[vout][aout]"
    fc = splits_v + splits_a + trims + concat

    cmd = [
        "ffmpeg", "-y", "-i", str(layered_path),
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "h264_nvenc", "-preset", "p4", "-b:v", cfg["bitrate"], "-r", fps,
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, dry_run)
    dur = 0 if dry_run else probe_duration(out)
    print(f"  -> {out} ({dur:.1f}s)")
    return out


def step_narration(cfg, cut_path, work_dir, dry_run=False):
    """Step 3: ナレーション載せ"""
    print("[Step3] Adding narration...")
    nar = work_dir / cfg["narration"]["file"]
    vol = cfg["narration"]["source_volume"]
    out = cut_path.with_name("_cut_nar.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(cut_path),
        "-i", str(nar),
        "-filter_complex",
        f"[0:a]volume={vol}[a0];[a0][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, dry_run)
    print(f"  -> {out}")
    return out


def step_se(cfg, nar_path, work_dir, dry_run=False):
    """Step 4: SE載せ"""
    se_cfg = cfg.get("se", {})
    if not se_cfg:
        print("[Step4] No SE configured, skipping.")
        return nar_path

    print("[Step4] Adding SE...")
    dur = 0 if dry_run else probe_duration(nar_path)
    out = nar_path.with_name("_cut_nar_se.mp4")

    filters = []
    se_inputs = []
    input_args = ["-i", str(nar_path)]
    idx = 1

    if "end" in se_cfg:
        se_end = se_cfg["end"]
        se_file = work_dir / se_end["file"]
        offset_ms = int((dur - se_end["offset_from_end"]) * 1000)
        vol = se_end.get("volume", 0.8)
        input_args += ["-i", str(se_file)]
        filters.append(f"[{idx}:a]adelay={offset_ms}|{offset_ms},volume={vol},apad=whole_dur={int(dur)+1}[se{idx}]")
        se_inputs.append(f"[se{idx}]")
        idx += 1

    # Chain: main + SE with normalize=0
    main_filter = "[0:a]volume=1.0[main]"
    mix = f"[main]{se_inputs[0]}amix=inputs=2:duration=first:dropout_transition=0:weights=1 1:normalize=0[aout]"

    fc = ";".join(filters) + f";{main_filter};{mix}"

    cmd = ["ffmpeg", "-y"] + input_args + [
        "-filter_complex", fc,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd, dry_run)
    print(f"  -> {out}")
    return out


def step_thumb_and_subtitle(cfg, se_path, work_dir, dry_run=False):
    """Step 5: サムネ作成 + 結合 + 字幕焼き込み（1パス）"""
    print("[Step5] Thumbnail + subtitle burn (1-pass)...")
    thumb_cfg = cfg["thumbnail"]
    thumb_img = work_dir / thumb_cfg["image"]
    thumb_dur = thumb_cfg["duration"]
    thumb_se = work_dir / thumb_cfg["se"]
    fps = cfg["fps"]
    canvas = cfg["canvas"]
    bitrate = cfg["bitrate"]
    thumb_path = work_dir / "_thumb.mp4"
    out = work_dir / cfg["output"]

    # Create thumbnail video
    cmd_thumb = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(thumb_dur), "-i", str(thumb_img),
        "-i", str(thumb_se),
        "-vf", f"scale={canvas['w']}:{canvas['h']}:force_original_aspect_ratio=decrease,"
               f"pad={canvas['w']}:{canvas['h']}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "h264_nvenc", "-preset", "p4", "-b:v", bitrate, "-r", fps,
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart",
        str(thumb_path),
    ]
    run(cmd_thumb, dry_run)

    # Build drawtext filters with thumb_dur offset
    dt_filters = []
    line_height = 75  # default spacing between lines

    for sub in cfg["subtitles"]:
        font_key = sub["font"]
        font_path = FONTS[font_key]
        borderw = BORDER_MAP[font_key]
        color = sub.get("color", "white")
        size = sub["size"]
        y_base = sub["y"]
        start = sub["start"] + thumb_dur
        end = sub["end"] + thumb_dur

        for i, line in enumerate(sub["text"]):
            escaped = line.replace(":", "\\:").replace("'", "\\'")
            y_expr = f"{y_base}+{i * (size + 15)}" if i > 0 else y_base
            dt_filters.append(
                f"drawtext=fontfile={font_path}:text='{escaped}':"
                f"fontsize={size}:fontcolor={color}:"
                f"borderw={borderw}:bordercolor=black:"
                f"shadowcolor=black:shadowx=5:shadowy=5:"
                f"x=(w-text_w)/2:y={y_expr}:"
                f"enable='between(t\\,{start}\\,{end})'"
            )

    # Credit
    credit = cfg.get("credit", "")
    if credit:
        escaped_credit = credit.replace(":", "\\:").replace("'", "\\'")
        dt_filters.append(
            f"drawtext=fontfile={FONTS['zero']}:text='{escaped_credit}':"
            f"fontsize=30:fontcolor=white:borderw=2:bordercolor=black:"
            f"x=20:y=h-50:"
            f"enable='between(t\\,{thumb_dur}\\,999)'"
        )

    drawtext_chain = ",".join(dt_filters)

    fc = (
        f"[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[vcombined][acombined];"
        f"[vcombined]{drawtext_chain}[vout]"
    )

    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(thumb_path),
        "-i", str(se_path),
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[acombined]",
        "-c:v", "h264_nvenc", "-preset", "p4", "-b:v", bitrate, "-r", fps,
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out),
    ]
    run(cmd_final, dry_run)
    dur = 0 if dry_run else probe_duration(out)
    print(f"  -> {out} ({dur:.1f}s)")
    return out


def cleanup(work_dir):
    """中間ファイル削除"""
    for name in ["_layered.mp4", "_cut.mp4", "_cut_nar.mp4", "_cut_nar_se.mp4", "_thumb.mp4"]:
        p = work_dir / name
        if p.exists():
            p.unlink()
            print(f"  Cleaned: {name}")


def main():
    parser = argparse.ArgumentParser(description="China shorts composer")
    parser.add_argument("config", help="compose.json path")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--keep-temp", action="store_true", help="Keep intermediate files")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    work_dir = config_path.parent

    with open(config_path) as f:
        cfg = json.load(f)

    # 必須キー検証 (cfg["..."] 直接アクセス前の preflight)
    validate_config(cfg)

    print(f"=== China Shorts Compose ===")
    print(f"Config: {config_path}")
    print(f"Work dir: {work_dir}")
    print(f"Output: {cfg['output']}")
    print()

    os.chdir(work_dir)

    # Step 1: Layer
    layered = step_layer(cfg, work_dir, args.dry_run)

    # Step 2: Cut
    cut = step_cut(cfg, layered, args.dry_run)

    # Step 3: Narration
    nar = step_narration(cfg, cut, work_dir, args.dry_run)

    # Step 4: SE
    se = step_se(cfg, nar, work_dir, args.dry_run)

    # Step 5: Thumbnail + Subtitle (1-pass)
    final = step_thumb_and_subtitle(cfg, se, work_dir, args.dry_run)

    # Cleanup
    if not args.keep_temp and not args.dry_run:
        print("\n[Cleanup]")
        cleanup(work_dir)

    print(f"\n=== Complete ===")
    print(f"Output: {final}")


if __name__ == "__main__":
    main()
