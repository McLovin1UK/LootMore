"""Simple Lootmore launcher for configuring and running client scripts."""
import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from urllib import request

from client.logging_setup import get_logger
from client.onboarding import run_onboarding_if_needed
from config import DEFAULT_CONFIG, get_config_path, get_version, load_config, save_config

LOGGER = get_logger("lootmore.launcher")
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = get_config_path()
APP_VERSION = get_version()

script_map = {
    "ARC Raiders": "ai_guide_arc_raiders.py",
}


class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Lootmore Launcher v{APP_VERSION}")

        run_onboarding_if_needed(str(CONFIG_PATH))
        self.config_data = load_config(str(CONFIG_PATH))

        self.backend_var = tk.StringVar(value=self.config_data.get("backend_url", DEFAULT_CONFIG["backend_url"]))
        self.token_var = tk.StringVar(value=self.config_data.get("user_token", DEFAULT_CONFIG["user_token"]))
        self.game_var = tk.StringVar(value=self.config_data.get("game", DEFAULT_CONFIG["game"]))
        self.timeout_var = tk.StringVar(value=str(self.config_data.get("timeout_s", DEFAULT_CONFIG["timeout_s"])))
        self.focus_var = tk.StringVar(value=self.config_data.get("focus", DEFAULT_CONFIG["focus"]))
        self.speak_var = tk.BooleanVar(value=bool(self.config_data.get("speak", DEFAULT_CONFIG["speak"])))
        self.max_words_var = tk.StringVar(value=str(self.config_data.get("max_words", DEFAULT_CONFIG["max_words"])))
        self.interval_var = tk.StringVar(value=self.config_data.get("interval", DEFAULT_CONFIG["interval"]))
        self.auto_start_var = tk.BooleanVar(value=bool(self.config_data.get("auto_start", DEFAULT_CONFIG["auto_start"])) )

        self.status_var = tk.StringVar(value="")
        self.update_status_var = tk.StringVar(value="")

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

        auto_start_check = ttk.Checkbutton(frame, text="Launch at login (hotkey helper)", variable=self.auto_start_var)
        add_labeled(auto_start_check, "Auto-start", 8)

        version_label = ttk.Label(frame, text=f"Launcher version {APP_VERSION}", foreground="#555")
        version_label.grid(column=0, row=9, columnspan=2, sticky="w", pady=(4, 0))

        button_row = ttk.Frame(frame)
        button_row.grid(column=0, row=10, columnspan=2, sticky="ew", pady=(10, 0))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)
        button_row.columnconfigure(2, weight=1)

        save_btn = ttk.Button(button_row, text="Save Config", command=self.save_config)
        save_btn.grid(column=0, row=0, sticky="ew", padx=(0, 6))

        launch_btn = ttk.Button(button_row, text="Launch", command=self.launch)
        launch_btn.grid(column=1, row=0, sticky="ew", padx=6)

        update_btn = ttk.Button(button_row, text="Check Updates", command=self.check_updates)
        update_btn.grid(column=2, row=0, sticky="ew", padx=(6, 0))

        status_label = ttk.Label(frame, textvariable=self.status_var, foreground="#555")
        status_label.grid(column=0, row=11, columnspan=2, sticky="w", pady=(8, 0))

        update_status_label = ttk.Label(frame, textvariable=self.update_status_var, foreground="#777")
        update_status_label.grid(column=0, row=12, columnspan=2, sticky="w", pady=(0, 0))

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
            "auto_start": bool(self.auto_start_var.get()),
        }
        return data

    def save_config(self):
        data = self._collect_config()
        save_config(data, str(CONFIG_PATH))
        LOGGER.info("Configuration saved to %s", CONFIG_PATH)
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
            LOGGER.info("Launched %s", game)
        except Exception as exc:
            messagebox.showerror("Launch error", str(exc))

    def _build_manifest_url(self, cfg):
        if cfg.get("update_manifest_url"):
            return cfg["update_manifest_url"]
        backend = (cfg.get("backend_url") or DEFAULT_CONFIG["backend_url"]).rstrip("/")
        if backend.endswith("/callout"):
            backend = backend.rsplit("/", 1)[0]
        return f"{backend}/version.json"

    def check_updates(self):
        cfg = self._collect_config()
        manifest_url = self._build_manifest_url(cfg)
        LOGGER.info("Checking update manifest at %s", manifest_url)
        self.update_status_var.set("Checking for updates…")
        try:
            with request.urlopen(manifest_url, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            remote_version = data.get("version")
            if remote_version and remote_version != APP_VERSION:
                self.update_status_var.set(f"Update available: {remote_version} (current {APP_VERSION})")
            elif remote_version:
                self.update_status_var.set(f"Up to date (v{APP_VERSION})")
            else:
                self.update_status_var.set("No version info in manifest.")
        except Exception as exc:
            LOGGER.warning("Update check failed: %s", exc)
            self.update_status_var.set("Update check failed (placeholder only)")

    def run(self):
        self.root.mainloop()


def main():
    app = LauncherApp()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        LOGGER.exception("Launcher crashed")
        raise
