# LootMore – AI Game Helper

LootMore is an AI assistant for PC games.

Press a hotkey, it grabs a screenshot, sends it to an AI backend, and plays back a short tactical callout in your headset so you can loot more, die less, and climb faster.

This repo contains:

- The **Windows client** (overlay + hotkey + launcher)
- The **FastAPI backend** (tokens, rate-limits, OpenAI calls)
- The **website** (landing + early-access pages)
- **Test assets** for safety / NSFW handling

---

## What LootMore does

High level:

1. You run LootMore alongside your game on Windows.
2. You hit a hotkey (`]` by default).
3. The client:
   - takes a screenshot of your current screen,
   - (optionally) downscales it for speed,
   - sends it + your selected game/focus to the backend.
4. The backend calls OpenAI with a vision + text prompt and returns:
   - a **short tactical callout** string, and
   - pre-generated **TTS audio** (mp3) or instructions for the client to call TTS.
5. The client plays the callout in your headset and shows a tiny overlay with status/latency.

No memory reading, no injection, no game file tampering. It’s built to behave like a friend watching your screen, not a cheat.

---

## Repo structure

Rough layout (omitting some files for brevity):

```text
LootMore/
├── client/                    # Client-side helpers (onboarding, logging, etc.)
├── installer/                 # NSIS / packaging bits for Windows installer
├── lootmore-backend/          # FastAPI backend (tokens, auth, callout pipeline)
│   ├── app/                   # Main backend app (routes, auth, models, etc.)
│   └── alembic/               # Database migrations
├── scripts/                   # Build scripts (e.g. installer build)
├── test_assets/
│   └── nsfw/                  # Synthetic test images for safety testing
├── .env.example               # Example backend environment config
├── .gitignore
├── PACKAGING.md               # Detailed packaging instructions for Windows EXE
├── VERSION                    # Client/launcher version string
├── ai_guide_arc_raiders.py    # Main ARC Raiders client guide/overlay
├── arc_guide.py               # Legacy shim pointing to the updated guide
├── config.py                  # Shared client config helpers
├── early-access.html          # Early access landing page
├── index.html                 # Main lootmore.ai marketing page
├── lootmore_config.json       # Example local client config
├── lootmore_launcher.py       # Windows launcher UI for configuring & running client
├── roadmap.html               # Roadmap/“where this is going” page
├── requirements.txt           # Backend + shared Python deps
└── README.md                  # You are here
