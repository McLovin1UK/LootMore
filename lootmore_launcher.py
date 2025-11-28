"""Simple Lootmore launcher for configuring and running client scripts."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from config import DEFAULT_CONFIG, load_config, save_config

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "lootmore_config.json")

script_map = {
    "ARC Raiders": "ai_guide_arc_raiders.py",
}


class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lootmore Launcher")

        self.config_data = load_config(CONFIG_PATH)

        self.backend_var = tk.StringVar(value=self.config_data.get("backend_url", DEFAULT_CONFIG["backend_url"]))
        self.token_var = tk.StringVar(value=self.config_data.get("user_token", DEFAULT_CONFIG["user_token"]))
        self.game_var = tk.StringVar(value=self.config_data.get("game", DEFAULT_CONFIG["game"]))
        self.timeout_var = tk.StringVar(value=str(self.config_data.get("timeout_s", DEFAULT_CONFIG["timeout_s"])))
        self.focus_var = tk.StringVar(value=self.config_data.get("focus", DEFAULT_CONFIG["focus"]))
        self.speak_var = tk.BooleanVar(value=bool(self.config_data.get("speak", DEFAULT_CONFIG["speak"])))
        self.max_words_var = tk.StringVar(value=str(self.config_data.get("max_words", DEFAULT_CONFIG["max_words"])))
        self.interval_var = tk.StringVar(value=self.config_data.get("interval", DEFAULT_CONFIG["interval"]))

        self.status_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        def add_labeled(widget, label_text, row, **opts):
            label = ttk.Label(frame, text=label_text)
            label.grid(column=0, row=row, sticky="w", padx=(0, 8), pady=4)
            widget.grid(column=1, row=row, sticky="ew", pady=4)
            frame.columnconfigure(1, weight=1)
            if opts.get("span_two"):
                widget.grid(columnspan=2)

        backend_entry = ttk.Entry(frame, textvariable=self.backend_var, width=50)
        add_labeled(backend_entry, "Backend URL", 0)

        token_entry = ttk.Entry(frame, textvariable=self.token_var, width=50)
        add_labeled(token_entry, "User Token", 1)

        game_box = ttk.Combobox(frame, textvariable=self.game_var, values=list(script_map.keys()), state="readonly")
        add_labeled(game_box, "Game", 2)

        timeout_entry = ttk.Entry(frame, textvariable=self.timeout_var, width=10)
        add_labeled(timeout_entry, "Timeout (s)", 3)

        focus_entry = ttk.Entry(frame, textvariable=self.focus_var, width=50)
        add_labeled(focus_entry, "Focus", 4)

        speak_check = ttk.Checkbutton(frame, text="Enable speech", variable=self.speak_var)
        add_labeled(speak_check, "Speak", 5)

        max_words_entry = ttk.Entry(frame, textvariable=self.max_words_var, width=10)
        add_labeled(max_words_entry, "Max words", 6)

        interval_box = ttk.Combobox(frame, textvariable=self.interval_var, values=["off", "15s", "30s", "60s"], state="readonly")
        add_labeled(interval_box, "Interval", 7)

        button_row = ttk.Frame(frame)
        button_row.grid(column=0, row=8, columnspan=2, sticky="ew", pady=(10, 0))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        save_btn = ttk.Button(button_row, text="Save Config", command=self.save_config)
        save_btn.grid(column=0, row=0, sticky="ew", padx=(0, 6))

        launch_btn = ttk.Button(button_row, text="Launch", command=self.launch)
        launch_btn.grid(column=1, row=0, sticky="ew", padx=(6, 0))

        status_label = ttk.Label(frame, textvariable=self.status_var, foreground="#555")
        status_label.grid(column=0, row=9, columnspan=2, sticky="w", pady=(8, 0))

    def _parse_int(self, value, default):
        try:
            return int(value)
        except Exception:
            return default

    def _collect_config(self):
        data = {
            "backend_url": self.backend_var.get().strip() or DEFAULT_CONFIG["backend_url"],
            "user_token": self.token_var.get().strip(),
            "game": self.game_var.get().strip() or DEFAULT_CONFIG["game"],
            "timeout_s": self._parse_int(self.timeout_var.get(), DEFAULT_CONFIG["timeout_s"]),
            "focus": self.focus_var.get().strip() or DEFAULT_CONFIG["focus"],
            "speak": bool(self.speak_var.get()),
            "max_words": self._parse_int(self.max_words_var.get(), DEFAULT_CONFIG["max_words"]),
            "interval": self.interval_var.get().strip() or DEFAULT_CONFIG["interval"],
        }
        return data

    def save_config(self):
        data = self._collect_config()
        save_config(data, CONFIG_PATH)
        self.status_var.set("Configuration saved.")
        return data

    def launch(self):
        data = self.save_config()
        game = data.get("game")
        target = script_map.get(game)
        if not target:
            messagebox.showerror("Launch error", f"No script mapped for game '{game}'.")
            return

        target_path = os.path.join(BASE_DIR, target)
        if not os.path.exists(target_path):
            messagebox.showerror("Launch error", f"Script not found: {target_path}")
            return

        try:
            subprocess.Popen([sys.executable, target_path], cwd=BASE_DIR)
            self.status_var.set(f"Launched {game} guide…")
        except Exception as exc:
            messagebox.showerror("Launch error", str(exc))

    def run(self):
        self.root.mainloop()


def main():
    app = LauncherApp()
    app.run()


if __name__ == "__main__":
    main()
