import keyboard
import os
import subprocess
import sys
import time
from pathlib import Path

from client.logging_setup import get_logger
from config import get_config_path, load_config

# Path to the main AI guide script (now includes its own overlay UI)
SCRIPT_PATH = Path(__file__).resolve().parent / "ai_guide_arc_raiders.py"
CONFIG_PATH = get_config_path()
STARTUP_KEY_NAME = "LootmoreHotkey"
LOGGER = get_logger("lootmore.hotkey")
COOLDOWN_S = 4.0
_last_trigger_ts = 0.0


def run_guide():
    """Launch the ARC guide script from the same folder as this hotkey helper."""
    global _last_trigger_ts

    now = time.monotonic()
    if now - _last_trigger_ts < COOLDOWN_S:
        LOGGER.info("Hotkey pressed during cooldown; ignoring.")
        return

    if not SCRIPT_PATH.is_file():
        LOGGER.error("Guide script not found at %s", SCRIPT_PATH)
        return

    # Launch a fresh process each time you press ]
    # The overlay appears while it's thinking / talking, then closes.
    subprocess.Popen(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(SCRIPT_PATH.parent)
    )
    _last_trigger_ts = now


def _set_startup(enable: bool) -> bool:
    """Register/unregister the script for autorun in Windows startup."""
    if os.name != "nt":
        return False
    try:
        import winreg
    except Exception as exc:  # pragma: no cover - Windows specific
        LOGGER.warning("winreg not available for startup registration: %s", exc)
        return False

    run_key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                cmd = f'"{sys.executable}" "{Path(__file__).resolve()}"'
                winreg.SetValueEx(key, STARTUP_KEY_NAME, 0, winreg.REG_SZ, cmd)
                LOGGER.info("Enabled Lootmore hotkey auto-start")
            else:
                try:
                    winreg.DeleteValue(key, STARTUP_KEY_NAME)
                    LOGGER.info("Disabled Lootmore hotkey auto-start")
                except FileNotFoundError:
                    pass
        return True
    except Exception as exc:  # pragma: no cover - Windows specific
        LOGGER.warning("Failed to modify startup registry: %s", exc)
        return False


def ensure_startup_from_config():
    cfg = load_config(str(CONFIG_PATH))
    _set_startup(bool(cfg.get("auto_start")))


def main():
    ensure_startup_from_config()
    keyboard.add_hotkey(']', run_guide)
    LOGGER.info("AI Guide hotkey active. Press ] at any time in-game.")
    keyboard.wait()  # keep script running


if __name__ == "__main__":
    main()
