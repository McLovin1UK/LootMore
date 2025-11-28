"""Shared configuration helpers for Lootmore client scripts."""
import json
import os
from copy import deepcopy
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "backend_url": "https://api.lootmore.ai/callout",
    "user_token": "",
    "game": "ARC Raiders",
    "timeout_s": 60,
    "focus": "Tactical callouts",
    "speak": True,
    "max_words": 15,
    "interval": "off",
}


def _merge_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(DEFAULT_CONFIG)
    for key, value in (data or {}).items():
        merged[key] = value
    return merged


def load_config(path: str) -> Dict[str, Any]:
    """Load the user config, merging in any missing defaults."""
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


def save_config(data: Dict[str, Any], path: str) -> None:
    """Persist the config, ensuring defaults are present."""
    merged = _merge_defaults(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
