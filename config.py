"""Shared configuration helpers for Lootmore client scripts.

Configuration and logs are stored under the user's roaming AppData
folder on Windows for a smoother installer experience. On non-Windows
systems, we fall back to a dot-folder in the user's home directory.
"""
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

APP_DIR_NAME = "Lootmore"
CONFIG_FILENAME = "config.json"
VERSION_FILENAME = "VERSION"

DEFAULT_CONFIG: Dict[str, Any] = {
    "backend_url": "https://api.lootmore.ai/callout",
    "user_token": "",
    "game": "ARC Raiders",
    "timeout_s": 60,
    "focus": "Tactical callouts",
    "speak": True,
    "max_words": 15,
    "interval": "off",
    "auto_start": False,
    "update_manifest_url": "",
}


def get_appdata_dir() -> Path:
    """Return the platform-appropriate application data directory."""
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME
    # Fallback for non-Windows dev environments
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def get_config_path(filename: str = CONFIG_FILENAME) -> Path:
    """Return the default config path and ensure the folder exists."""
    path = get_appdata_dir() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _merge_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(DEFAULT_CONFIG)
    for key, value in (data or {}).items():
        merged[key] = value
    return merged


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the user config, merging in any missing defaults."""
    path = path or str(get_config_path())
    if not os.path.exists(path):
        return deepcopy(DEFAULT_CONFIG)

    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("Config must be a JSON object")
    except Exception:
        # Fall back to defaults if the file is unreadable or invalid
        return deepcopy(DEFAULT_CONFIG)

    return _merge_defaults(loaded)


def save_config(data: Dict[str, Any], path: Optional[str] = None) -> None:
    """Persist the config, ensuring defaults are present."""
    path = path or str(get_config_path())
    merged = _merge_defaults(data)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


def get_version(version_path: Optional[str] = None) -> str:
    """Load the semantic version string from VERSION file."""
    version_path = version_path or Path(__file__).resolve().parent / VERSION_FILENAME
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"
