"""First-run onboarding to collect backend URL and token."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from config import DEFAULT_CONFIG, load_config, save_config, get_config_path
from client.logging_setup import get_logger

logger = get_logger("lootmore.onboarding")


class OnboardingWindow:
    def __init__(self, initial_config: Optional[Dict[str, str]] = None):
        cfg = initial_config or DEFAULT_CONFIG
        self.root = tk.Tk()
        self.root.title("Lootmore Setup")
        self.root.resizable(False, False)

        self.backend_var = tk.StringVar(value=cfg.get("backend_url", DEFAULT_CONFIG["backend_url"]))
        self.token_var = tk.StringVar(value=cfg.get("user_token", ""))

        frame = ttk.Frame(self.root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Welcome to Lootmore", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, text="Enter your backend URL and token to get started.").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 10))

        ttk.Label(frame, text="Backend URL").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.backend_var, width=48).grid(row=2, column=1, pady=4, sticky="ew")

        ttk.Label(frame, text="User Token").grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.token_var, width=48, show="*").grid(row=3, column=1, pady=4, sticky="ew")

        button_row = ttk.Frame(frame)
        button_row.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_row, text="Save", command=self._save_and_close).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(button_row, text="Cancel", command=self.root.destroy).grid(row=0, column=1)

        frame.columnconfigure(1, weight=1)

        self.saved_config: Optional[Dict[str, str]] = None

    def _save_and_close(self):
        backend = self.backend_var.get().strip()
        token = self.token_var.get().strip()

        if not backend:
            messagebox.showerror("Backend required", "Please provide a backend URL.")
            return
        if not token:
            messagebox.showerror("Token required", "Please provide your user token.")
            return

        self.saved_config = {
            "backend_url": backend,
            "user_token": token,
        }
        self.root.destroy()

    def run(self) -> Optional[Dict[str, str]]:
        self.root.mainloop()
        return self.saved_config


def run_onboarding_if_needed(config_path: Optional[str] = None) -> Dict[str, str]:
    config_path = config_path or str(get_config_path())
    existing = load_config(config_path)
    if existing.get("backend_url") and existing.get("user_token"):
        return existing

    logger.info("Starting first-run onboarding UI")
    onboarding = OnboardingWindow(existing)
    saved = onboarding.run()
    if saved:
        combined = {**existing, **saved}
        save_config(combined, config_path)
        logger.info("Onboarding complete and configuration saved")
        return combined

    logger.warning("Onboarding cancelled by user; keeping existing config")
    return existing


if __name__ == "__main__":
    run_onboarding_if_needed()
