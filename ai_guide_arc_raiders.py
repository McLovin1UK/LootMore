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
    current_stage: int = -1

    def set_stage(self, stage_index: int | str | None = None, label: str | None = None) -> None:
        """Advance overlay state while allowing optional label overrides.

        The original tool sometimes called ``set_stage`` with only a label
        (e.g. ``overlay.set_stage("Contacting AI…")``), which previously raised
        a ``TypeError`` because the ``stage_index`` positional argument was
        missing. The method now accepts either:

        * an explicit ``stage_index`` (optionally followed by a replacement
          ``label``), or
        * just a label, in which case the overlay automatically advances to the
          next stage.
        """

        resolved_index: int

        if isinstance(stage_index, str):
            if label is not None:
                raise TypeError(
                    "When supplying the stage label as the first argument, do not "
                    "also supply a second label argument."
                )
            label = stage_index
            resolved_index = min(self.current_stage + 1, len(self.stages) - 1)
        elif stage_index is None:
            if label is None:
                raise TypeError("set_stage requires either a stage index or a label.")
            resolved_index = min(self.current_stage + 1, len(self.stages) - 1)
        else:
            if not 0 <= stage_index < len(self.stages):
                raise ValueError("stage_index out of range")
            resolved_index = stage_index

        if label is not None:
            self.stages[resolved_index] = label

        self.current_stage = resolved_index
        print(
            f"[Overlay] Stage {resolved_index + 1}/{len(self.stages)}: "
            f"{self.stages[resolved_index]}"
        )

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
