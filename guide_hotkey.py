import keyboard
import subprocess
import sys
from pathlib import Path

# Path to the main AI guide script (now includes its own overlay UI)
SCRIPT_PATH = Path(__file__).resolve().parent / "ai_guide_arc_raiders.py"


def run_guide():
    """Launch the ARC guide script from the same folder as this hotkey helper."""
    if not SCRIPT_PATH.is_file():
        print(f"Guide script not found at {SCRIPT_PATH}")
        return

    # Launch a fresh process each time you press ]
    # The overlay appears while it's thinking / talking, then closes.
    subprocess.Popen(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(SCRIPT_PATH.parent)
    )


keyboard.add_hotkey(']', run_guide)

print("AI Guide hotkey active. Press ] at any time in-game.")
keyboard.wait()  # keep script running
