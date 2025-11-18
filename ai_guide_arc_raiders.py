import os
import io
import base64
import tempfile
import time

from PIL import ImageGrab
from openai import OpenAI

import tkinter as tk
from tkinter import ttk
import threading

# -------- CONFIG --------
VOICE_SYSTEM_PROMPT = (
    "You are a veteran ARC Raiders tactical operator viewing a live gameplay screenshot.\n"
    "\n"
    "Your job is to give ONE short, sharp, actionable voice callout (max 15 words).\n"
    "\n"
    "Priorities for what you describe:\n"
    "1) ENEMIES & THREATS:\n"
    "   - If enemies, drones, turrets or obvious danger are visible, mention them FIRST.\n"
    "   - Call out their direction (left, right, ahead, behind, high ground, low ground).\n"
    "   - Warn if the player is overexposed, in the open, or about to be flanked.\n"
    "\n"
    "2) ENVIRONMENT & OBJECTS AROUND THEM (NOT JUST THE PLAYER):\n"
    "   - Sometimes talk about the surroundings: cover, high ground, buildings, vehicles,\n"
    "     loot crates, ammo boxes, extraction points, doors, choke points, vantage points.\n"
    "   - Don't always focus on the player's gun or HUD; vary between threats and terrain.\n"
    "\n"
    "3) LIGHT SOURCES & VISUAL CLARITY:\n"
    "   - Distinguish between handheld flashlights, weapon lights, and streetlights or mounted lamps.\n"
    "   - Small, focused beams coming from characters or weapons are flashlights/weapon lights,\n"
    "     NOT streetlights.\n"
    "   - Large poles with mounted lights or lamps above roads/structures are streetlights.\n"
    "\n"
    "STYLE:\n"
    "- Tactical, calm, experienced squad leader.\n"
    "- Max 15 words, no filler, no greetings, no explanations, no second sentence.\n"
    "- Sound like a quick in-comms callout, not a narrator.\n"
)
VISION_MODEL = "gpt-4.1"
TTS_MODEL    = "gpt-4o-mini-tts"
TTS_VOICE    = "alloy"
# ------------------------


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

    def set_stage(self, stage_name: str, stage_index: int):
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


def get_tactical_text(client, image_bytes: bytes) -> str:
    """
    Vision call with explicit behavior:
      - Enemies + threats first
      - Sometimes environment, not just player/loadout
      - Strict light-source logic (flashlight vs streetlight)
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")

    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": VOICE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are seeing a single gameplay frame from a third-person shooter.\n\n"
                            "Look at the WHOLE scene, not just the player or their weapon.\n"
                            "\n"
                            "Rules:\n"
                            "1) If any enemies, drones, turrets, or visible danger exist, call them out first with direction.\n"
                            "2) If no clear enemies, give useful context about surroundings: cover, high ground, loot, vehicles,\n"
                            "   extraction points, doors, choke points, vantage points.\n"
                            "3) Try to vary your focus: sometimes enemies, sometimes terrain, sometimes loot/objectives.\n"
                            "4) Small concentrated light beams from characters/weapons = flashlights or weapon lights.\n"
                            "   Mounted lamps or tall poles with lights = streetlights/area lights.\n"
                            "\n"
                            "OUTPUT:\n"
                            "- ONE short tactical callout, max 15 words.\n"
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
    )

    text = extract_text_from_message(resp.choices[0].message)
    return text[:200]


def play_mp3_with_windows(tmp_path: str):
    os.startfile(tmp_path)


def speak_text(client, text: str):
    if not text:
        return

    print(f"AI: {text}")

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

    play_mp3_with_windows(tmp_path)


# ---------- Main flow with overlay ----------

def main():
    overlay = None
    try:
        # Init overlay
        try:
            overlay = Overlay()
            overlay.update("Lootmore AI Online\nIdle…")
        except Exception as e:
            print(f"Overlay init failed: {e}")
            overlay = None


        try:
            client = get_client()
        except Exception as e:
            print(f"Error creating OpenAI client: {e}")
            if overlay:
                overlay.set_error("OpenAI client error")
            return

        print("Taking screenshot…")
        if overlay:
            overlay.update("Capturing screenshot…",)

        try:
            img_bytes = take_screenshot()
        except Exception as e:
            print(f"Screenshot failed: {e}")
            print("If this happens in full-screen, try borderless windowed mode.")
            if overlay:
                overlay.update("Screenshot failed")
            return

        print("Getting tactical guidance from AI…")
        if overlay:
            overlay.set_stage("Contacting AI…",)

        try:
            start_ai = time.time()
            text = get_tactical_text(client, img_bytes)
            ai_latency = time.time() - start_ai
            if overlay:
                overlay.set_latency("AI latency", ai_latency)
                overlay.update("AI reply ready",)
        except Exception as e:
            print(f"Error from GPT: {e}")
            if overlay:
                overlay.set_error("GPT error")
            return

        print("Speaking response…")
        if overlay:
            overlay.set_stage("Playing TTS…", 4)

        try:
            start_tts = time.time()
            speak_text(client, text)
            tts_latency = time.time() - start_tts
            if overlay:
                overlay.set_latency("TTS latency", tts_latency)
        except Exception as e:
            print(f"Error in TTS playback: {e}")
            if overlay:
                overlay.set_error("TTS error")
            return

        # Keep overlay visible for a bit so you actually see it
        if overlay:
            time.sleep(2.0)
            overlay.set_stage("Idle", 0)
            time.sleep(0.5)

    finally:
        if overlay:
            overlay.stop()


if __name__ == "__main__":
    main()
