#!/usr/bin/env python3
"""
members.py — ドズル社メンバー共通ユーティリティ

load_members_from_yaml() を一箇所に集約。
vocal_stt_pipeline.py / stt_merge.py / speaker_id.py の3ファイルから import する。
"""

from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_PROFILES_PATH = _SCRIPT_DIR.parent / "projects" / "dozle_kirinuki" / "context" / "member_profiles.yaml"


def load_members_from_yaml(profiles_path: Path | None = None) -> list[str]:
    """member_profiles.yamlからメンバーキー一覧を読み込む。失敗時はデフォルト値を返す。"""
    if profiles_path is None:
        profiles_path = _DEFAULT_PROFILES_PATH
    try:
        import yaml
        with open(profiles_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return list(data.get("members", {}).keys())
    except Exception:
        return ["dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"]
