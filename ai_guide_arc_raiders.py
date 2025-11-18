"""Command line helper for Arc Raiders tactical overlays."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


SCREENSHOT_NAME = "arc_raiders_screenshot.txt"


@dataclass
class ArcOverlay:
    """Tracks overlay stages and prints updates to stdout."""

    stages: List[str] = field(
        default_factory=lambda: [
            "Taking screenshot…",
            "Contacting AI…",
            "Receiving tactical intel…",
            "Overlay ready",
        ]
    )
    current_stage: int = 0

    def set_stage(self, stage_index: int, label: str | None = None) -> None:
        """Advance overlay state while allowing optional label overrides.

        The original tool expected callers to supply both the stage index and the
        text that should be displayed for that stage. Accidentally calling the
        method with only the text resulted in a ``TypeError`` because the
        required ``stage_index`` positional argument was missing. By always
        providing the index first we avoid that runtime failure and keep the
        overlay timeline accurate.
        """

        if not 0 <= stage_index < len(self.stages):
            raise ValueError("stage_index out of range")

        if label is not None:
            self.stages[stage_index] = label

        self.current_stage = stage_index
        print(f"[Overlay] Stage {stage_index + 1}/{len(self.stages)}: {self.stages[stage_index]}")

    def display_guidance(self, guidance: str) -> None:
        """Render the final overlay guidance."""

        print("\n=== Tactical Guidance ===")
        print(guidance)
        print("========================\n")


def capture_screenshot(path: Path) -> None:
    """Simulate a screenshot capture by writing to ``path``."""

    path.write_text("Simulated screenshot data for Arc Raiders.")


def query_ai(screenshot_path: Path) -> str:
    """Pretend to query an AI model using the captured screenshot."""

    _ = screenshot_path.read_text()
    return "Focus fire on the Arc Fighter's exposed radiator fins."


def main() -> None:
    overlay = ArcOverlay()

    screenshot_path = Path(SCREENSHOT_NAME)
    print("Taking screenshot…")
    overlay.set_stage(0, "Taking screenshot…")
    capture_screenshot(screenshot_path)

    print("Getting tactical guidance from AI…")
    overlay.set_stage(1, "Contacting AI…")
    guidance = query_ai(screenshot_path)

    overlay.set_stage(2, "AI guidance received.")
    overlay.set_stage(3, "Overlay ready")
    overlay.display_guidance(guidance)


if __name__ == "__main__":
    main()
