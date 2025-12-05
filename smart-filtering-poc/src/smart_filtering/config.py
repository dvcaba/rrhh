from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

# Default config lives at <project_root>/config/default.yaml
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "default.yaml"


@lru_cache(maxsize=1)
def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """
    Load YAML configuration once per process. If no path is provided, uses:
    - SMART_FILTERING_CONFIG env var (relative to project root allowed)
    - default.yaml in the config folder.
    """
    env_path = os.getenv("SMART_FILTERING_CONFIG")
    selected_path = Path(config_path or env_path or DEFAULT_CONFIG_PATH)
    if not selected_path.is_absolute():
        # Resolve relative paths against the default config directory
        selected_path = DEFAULT_CONFIG_PATH.parent / selected_path

    selected_path = selected_path.resolve()
    if not selected_path.exists():
        raise FileNotFoundError(f"Config file not found at {selected_path}")

    with selected_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    return cfg


def resolve_path(path_value: str | Path, project_root: Path | None = None) -> Path:
    """
    Resolve a possibly relative path to an absolute path anchored at project_root
    (defaults to repo root inferred from DEFAULT_CONFIG_PATH).
    """
    path = Path(path_value)
    if path.is_absolute():
        return path

    base_root = project_root or DEFAULT_CONFIG_PATH.parents[1]
    return (base_root / path).resolve()
