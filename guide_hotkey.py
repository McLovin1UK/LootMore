import keyboard
import subprocess
import os

# Path to the main AI guide script (now includes its own overlay UI)
script_path = r"C:\AI\ArcGuide\ai_guide_arc_raiders.py"


def run_guide():
    # Launch a fresh process each time you press ]
    # The overlay appears while it's thinking / talking, then closes.
    subprocess.Popen(
        ["python", script_path],
        cwd=os.path.dirname(script_path)
    )


keyboard.add_hotkey(']', run_guide)

print("AI Guide hotkey active. Press ] at any time in-game.")
keyboard.wait()  # keep script running
