import os
import io
import base64
import tempfile
import time
import ctypes
import subprocess
import sys

from PIL import ImageGrab
from openai import OpenAI

import tkinter as tk
from tkinter import ttk
import threading

from client.logging_setup import get_logger
from config import DEFAULT_CONFIG, get_config_path, load_config

# -------- CONFIG --------
CONFIG_PATH = str(get_config_path())
logger = get_logger("lootmore.arc_guide")


VOICE_SYSTEM_PROMPT_TEMPLATE = """You are a veteran ARC Raiders tactical operator viewing a live gameplay screenshot.

Your job is to give ONE short, sharp, actionable voice callout (max {max_words} words).

Priorities for what you describe:
1) ENEMIES & THREATS:
   - If enemies, drones, turrets or obvious danger are visible, mention them FIRST.
   - Call out their direction (left, right, ahead, behind, high ground, low ground).
   - Warn if the player is overexposed, in the open, or about to be flanked.

2) ENVIRONMENT & OBJECTS AROUND THEM (NOT JUST THE PLAYER):
   - Sometimes talk about the surroundings: cover, high ground, buildings, vehicles,
     loot crates, ammo boxes, extraction points, doors, choke points, vantage points.
   - Don't always focus on the player's gun or HUD; vary between threats and terrain.

3) LIGHT SOURCES & VISUAL CLARITY:
   - Distinguish between handheld flashlights, weapon lights, and streetlights or mounted lamps.
   - Small, focused beams coming from characters or weapons are flashlights/weapon lights, NOT streetlights.
   - Large poles with mounted lights or lamps above roads/structures are streetlights.

STYLE:
- Tactical, calm, experienced squad leader.
- Max {max_words} words, no filler, no greetings, no explanations, no second sentence.
- Sound like a quick in-comms callout, not a narrator.
- Current focus: {focus}.
"""
VISION_MODEL = "gpt-4.1"
TTS_MODEL    = "gpt-4o-mini-tts"
TTS_VOICE    = "alloy"
# ------------------------


def _coerce_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def load_user_config():
    """Load and validate the user configuration file."""
    cfg = load_config(CONFIG_PATH)

    logger.info("Loaded configuration from %s", CONFIG_PATH)

    cfg["backend_url"] = cfg.get("backend_url") or DEFAULT_CONFIG["backend_url"]
    cfg["user_token"] = cfg.get("user_token") or DEFAULT_CONFIG["user_token"]
    cfg["game"] = cfg.get("game") or DEFAULT_CONFIG["game"]
    cfg["focus"] = cfg.get("focus") or DEFAULT_CONFIG["focus"]
    cfg["interval"] = cfg.get("interval") or DEFAULT_CONFIG["interval"]
    cfg["speak"] = bool(cfg.get("speak", DEFAULT_CONFIG["speak"]))
    cfg["timeout_s"] = _coerce_int(cfg.get("timeout_s"), DEFAULT_CONFIG["timeout_s"])
    cfg["max_words"] = _coerce_int(cfg.get("max_words"), DEFAULT_CONFIG["max_words"])

    if not cfg.get("backend_url"):
        raise ValueError("backend_url missing from configuration")
    if not cfg.get("game"):
        raise ValueError("game missing from configuration")

    return cfg


def build_system_prompt(cfg):
    return VOICE_SYSTEM_PROMPT_TEMPLATE.format(
        max_words=cfg.get("max_words", DEFAULT_CONFIG["max_words"]),
        focus=cfg.get("focus", DEFAULT_CONFIG["focus"]),
    )


def _apply_word_limit(text: str, max_words: int) -> str:
    if not text:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


# ---------- Overlay UI (NO THREADS) ----------
class ArcOverlay:
    """
    Minimal always-on-top text overlay for Lootmore.
    Shows simple status / latency text in the top-right corner.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Window position (top-right)
        width, height = 360, 80
        screen_w = self.root.winfo_screenwidth()
        x = screen_w - width - 20
        y = 20
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Simple dark background
        self.root.configure(bg="black")

        # Internal state text
        self._status = "Idle"
        self._latency = ""

        # Single label displaying everything
        self.label = tk.Label(
            self.root,
            text="Lootmore AI Online\nIdle",
            fg="#00ff66",
            bg="black",
            font=("Consolas", 14, "bold"),
            justify="left"
        )
        self.label.pack(anchor="nw", padx=4, pady=4)

        # Initial draw
        self._render()
        self._pump()

    def _render(self):
        """Update label text from internal state."""
        lines = ["Lootmore AI Online", self._status]
        if self._latency:
            lines.append(self._latency)
        self.label.config(text="\n".join(lines))

    def _pump(self):
        """Process Tk events safely."""
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            # Window has probably been closed
            pass

    def set_stage(self, stage_name: str, stage_index: int = 0):
        """
        stage_index kept for compatibility but only status text is used.
        """
        self._status = stage_name or "Idle"
        self._render()
        self._pump()

    def set_error(self, msg: str):
        msg = (msg or "Unknown error").strip()
        if len(msg) > 50:
            msg = msg[:47] + "..."
        self._status = f"Error: {msg}"
        self._render()
        self._pump()

    def set_latency(self, label: str, seconds: float):
        """Show a single latency line, colour-coded by speed."""
        if seconds is None:
            self._latency = ""
            colour = "#AAAAAA"
        else:
            self._latency = f"{label}: {seconds:.1f}s"
            if seconds < 1.0:
                colour = "#55FF55"
            elif seconds < 3.0:
                colour = "#FFCC33"
            else:
                colour = "#FF5555"
        self.label.config(fg=colour)
        self._render()
        self._pump()

    def update(self, status_text: str, stage_index: int = None):
        """Compatibility helper: existing code calls `overlay.update(...)`.

        This sets the visible status text. `stage_index` is accepted for
        compatibility but not used beyond keeping the signature stable.
        """
        try:
            self._status = status_text or "Idle"
        except Exception:
            # If a non-string (e.g. tuple) is passed accidentally, coerce to str
            self._status = str(status_text)
        self._render()
        self._pump()

    def stop(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass


# Backwards-compatible alias: some code calls `Overlay()` instead of `ArcOverlay()`
Overlay = ArcOverlay

# ---------- OpenAI / Vision / TTS ----------

def get_client():
    return OpenAI()  # uses OPENAI_API_KEY


def take_screenshot():
    """Grab full-screen screenshot and return raw PNG bytes."""
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def extract_text_from_message(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content.strip()

    parts = []
    for part in content or []:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def get_tactical_text(client, image_bytes: bytes, cfg) -> str:
    """
    Vision call with explicit behavior:
      - Enemies + threats first
      - Sometimes environment, not just player/loadout
      - Strict light-source logic (flashlight vs streetlight)
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")
    max_words = cfg.get("max_words", DEFAULT_CONFIG["max_words"])
    focus = cfg.get("focus", DEFAULT_CONFIG["focus"])

    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt(cfg)},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are seeing a single gameplay frame from a third-person shooter.\n\n"
                            "Look at the WHOLE scene, not just the player or their weapon.\n"
                            "\n"
                            f"Focus: {focus}.\n"
                            "Rules:\n"
                            "1) If any enemies, drones, turrets, or visible danger exist, call them out first with direction.\n"
                            "2) If no clear enemies, give useful context about surroundings: cover, high ground, loot, vehicles,\n"
                            "   extraction points, doors, choke points, vantage points.\n"
                            "3) Try to vary your focus: sometimes enemies, sometimes terrain, sometimes loot/objectives.\n"
                            "4) Small concentrated light beams from characters/weapons = flashlights or weapon lights.\n"
                            "   Mounted lamps or tall poles with lights = streetlights/area lights.\n"
                            "\n"
                            "OUTPUT:\n"
                            f"- ONE short tactical callout, max {max_words} words.\n"
                            "- No greetings, no fluff, no second sentence."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            },
        ],
        max_tokens=60,
        timeout=cfg.get("timeout_s"),
    )

    text = extract_text_from_message(resp.choices[0].message)
    return _apply_word_limit(text[:200], max_words)


def _play_mp3_with_winmm(tmp_path: str):
    """Play an MP3 directly through Windows audio without opening a media player."""
    alias = f"guide_audio_{int(time.time() * 1000)}"

    def _mci(cmd: str) -> int:
        return ctypes.windll.winmm.mciSendStringW(cmd, None, 0, None)

    # Open the file as an mpegvideo device and play synchronously.
    open_cmd = f'open "{tmp_path}" type mpegvideo alias {alias}'
    if _mci(open_cmd) != 0:
        raise RuntimeError("winmm could not open MP3")

    try:
        play_err = _mci(f"play {alias} wait")
        if play_err != 0:
            raise RuntimeError("winmm playback error")
    finally:
        _mci(f"close {alias}")


def play_mp3(tmp_path: str):
    if os.name == "nt":
        try:
            _play_mp3_with_winmm(tmp_path)
            return
        except Exception:
            # Fall back to OS default handler if direct playback fails
            pass
        os.startfile(tmp_path)
        return

    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, tmp_path])


def speak_text(client, text: str, speak_enabled: bool = True):
    if not text:
        return

    print(f"AI: {text}")
    if not speak_enabled:
        return

    tmp_path = os.path.join(
        tempfile.gettempdir(),
        "ai_guide_arc_raiders.mp3"
    )

    # Use the streaming API properly to avoid the deprecation warning
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
    ) as response:
        response.stream_to_file(tmp_path)

    play_mp3(tmp_path)


# ---------- Main flow with overlay ----------

def main():
    overlay = None
    try:
        logger.info("Starting ARC Raiders guide")
        try:
            overlay = Overlay()
            overlay.update("Lootmore AI Online\nIdle…")
        except Exception as e:
            logger.warning("Overlay init failed: %s", e)
            overlay = None

        try:
            config = load_user_config()
        except Exception as e:
            logger.error("Config error: %s", e)
            if overlay:
                overlay.set_error("Config error")
            return

        try:
            client = get_client()
        except Exception as e:
            logger.error("Error creating OpenAI client: %s", e)
            if overlay:
                overlay.set_error("OpenAI client error")
            return
        logger.info("Taking screenshot…")
        if overlay:
            overlay.update("Capturing screenshot…",)

        try:
            img_bytes = take_screenshot()
        except Exception as e:
            logger.error("Screenshot failed: %s", e)
            logger.info("If this happens in full-screen, try borderless windowed mode.")
            if overlay:
                overlay.update("Screenshot failed")
            return

        logger.info("Getting tactical guidance from AI…")
        if overlay:
            overlay.set_stage("Contacting AI…",)

        try:
            start_ai = time.time()
            text = get_tactical_text(client, img_bytes, config)
            ai_latency = time.time() - start_ai
            logger.info("AI latency: %.2fs", ai_latency)
            if overlay:
                overlay.set_latency("AI latency", ai_latency)
                overlay.update("AI reply ready",)
        except Exception as e:
            logger.error("Error from GPT: %s", e)
            if overlay:
                overlay.set_error("GPT error")
            return

        logger.info("Speaking response…")
        if overlay:
            overlay.set_stage("Playing TTS…", 4)

        try:
            start_tts = time.time()
            speak_text(client, text, speak_enabled=config.get("speak", True))
            tts_latency = time.time() - start_tts
            logger.info("TTS latency: %.2fs", tts_latency)
            if overlay:
                overlay.set_latency("TTS latency", tts_latency)
        except Exception as e:
            logger.error("Error in TTS playback: %s", e)
            if overlay:
                overlay.set_error("TTS error")
            return

        if overlay:
            time.sleep(2.0)
            overlay.set_stage("Idle", 0)
            time.sleep(0.5)

    except Exception:
        logger.exception("Unhandled error in ARC Raiders guide")
        if overlay:
            overlay.set_error("Crash - see log")
    finally:
        if overlay:
            overlay.stop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Fatal error running ARC Raiders guide")
        raise
