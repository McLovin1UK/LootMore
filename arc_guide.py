"""
Compatibility shim: legacy arc_guide entrypoint forwarding to the updated
ARC Raiders guide implementation.

Importers can continue to `import arc_guide` while the actual logic lives
in `ai_guide_arc_raiders.py` (or `ai_arc_raiders_guide.py` if present).
"""

# Prefer the updated filename, but support the alternate spelling if present
try:  # pragma: no cover - simple import fallback
    import ai_arc_raiders_guide as guide_impl  # type: ignore
except ImportError:  # pragma: no cover
    import ai_guide_arc_raiders as guide_impl

ArcOverlay = guide_impl.ArcOverlay
Overlay = guide_impl.Overlay
get_client = guide_impl.get_client
get_tactical_text = guide_impl.get_tactical_text
extract_text_from_message = guide_impl.extract_text_from_message
take_screenshot = guide_impl.take_screenshot
play_mp3_with_windows = guide_impl.play_mp3_with_windows
speak_text = guide_impl.speak_text


def main():
    """Run the latest ARC Raiders guide implementation."""
    return guide_impl.main()


if __name__ == "__main__":
    main()
