from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from open_waterfall.core.config.schema import OpenWaterfallConfig


def _project_root(start: Path) -> Path | None:
    for directory in [start, *start.parents]:
        if (directory / "pyproject.toml").exists() or (directory / ".git").exists():
            return directory
    return None


def _load_dotenv_files(config_path: Path) -> None:
    candidate_paths: list[Path] = [Path.cwd() / ".env", config_path.parent / ".env"]

    for root in {_project_root(Path.cwd()), _project_root(config_path.parent)}:
        if root is not None:
            candidate_paths.append(root / ".env")

    seen: set[Path] = set()
    for candidate in candidate_paths:
        resolved = candidate.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        load_dotenv(resolved, override=False)


def _substitute_env(config_str: str) -> str:
    for key, value in os.environ.items():
        config_str = config_str.replace(f"${{{key}}}", value)
    return config_str


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    config_str = _substitute_env(path.read_text())
    raw = yaml.safe_load(config_str) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"config at {path} must be a mapping")
    return raw


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def _profile_refs(raw: dict[str, Any]) -> list[str]:
    refs: list[str] = []

    single = raw.get("profile")
    if isinstance(single, str) and single.strip():
        refs.append(single.strip())

    multiple = raw.get("profiles")
    if isinstance(multiple, list):
        refs.extend(str(item).strip() for item in multiple if str(item).strip())

    return refs


def _resolve_profile_path(config_path: Path, profile_ref: str) -> Path:
    shipped_profiles_dir = Path(__file__).resolve().parents[2] / "profiles"
    ref_path = Path(profile_ref)

    candidates: list[Path] = []
    if ref_path.is_absolute():
        candidates.append(ref_path)
    else:
        candidates.extend(
            [
                config_path.parent / ref_path,
                config_path.parent / f"{profile_ref}.yaml",
                shipped_profiles_dir / ref_path,
                shipped_profiles_dir / f"{profile_ref}.yaml",
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"unable to resolve config profile '{profile_ref}'")


def _load_profiles(config_path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for profile_ref in _profile_refs(raw):
        profile_path = _resolve_profile_path(config_path, profile_ref)
        merged = _deep_merge(merged, _load_yaml_dict(profile_path))
    return merged


def load_config(config_path: str) -> OpenWaterfallConfig:
    """Load config, profiles, and environment-backed placeholders."""
    path = Path(config_path).resolve()
    _load_dotenv_files(path)
    raw = _load_yaml_dict(path)
    merged = _deep_merge(_load_profiles(path, raw), raw)
    merged.pop("profile", None)
    merged.pop("profiles", None)
    return OpenWaterfallConfig.model_validate(merged)
