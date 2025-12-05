# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""State definition for Windows 11 desktop generator."""

from dataclasses import dataclass, field
from typing import Any

from cudag.core import BaseState

from screen import (
    DESKTOP_CELL_HEIGHT,
    DESKTOP_CELL_WIDTH,
    DESKTOP_ICON_SIZE,
    DESKTOP_ICONS,
    TASKBAR_ICON_GAP,
    TASKBAR_ICON_SIZE,
    TASKBAR_ICONS,
    TASKBAR_LEFT_MARGIN,
    TASKBAR_Y_OFFSET,
)


@dataclass
class IconPlacement:
    """Placement info for a single icon."""

    icon_id: str
    """Icon identifier (e.g., 'od', 'chrome')."""

    x: int
    """X coordinate of icon top-left."""

    y: int
    """Y coordinate of icon top-left."""

    width: int
    """Icon width in pixels."""

    height: int
    """Icon height in pixels."""

    label: str = ""
    """Optional label text (for desktop icons)."""

    @property
    def center(self) -> tuple[int, int]:
        """Center point of the icon (click target)."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """Bounding box as (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class DesktopState(BaseState):
    """State for a single desktop screenshot.

    Tracks ground truth for all composite pieces:
    - Desktop icons with their positions and labels
    - Taskbar icons with their positions
    - DateTime text and position
    - OD Loading panel visibility
    """

    desktop_icons: list[IconPlacement] = field(default_factory=list)
    """Icons placed on the desktop area."""

    taskbar_icons: list[IconPlacement] = field(default_factory=list)
    """Icons placed on the taskbar."""

    datetime_text: str = ""
    """DateTime string shown in bottom-right."""

    datetime_position: tuple[int, int] = (0, 0)
    """Position of datetime text (x, y)."""

    od_loading_visible: bool = False
    """Whether the OD Loading splash panel is visible."""

    @classmethod
    def generate(
        cls,
        rng: Any,
        num_desktop_icons: int = 5,
        num_taskbar_icons: int = 3,
        od_loading_visible: bool = False,
    ) -> "DesktopState":
        """Generate a random desktop state.

        Args:
            rng: Random number generator
            num_desktop_icons: Number of icons to place on desktop (min 2 for od/pms)
            num_taskbar_icons: Number of icons to place on taskbar
            od_loading_visible: Whether the OD Loading splash panel is visible

        Returns:
            DesktopState with randomized icon placement
        """
        state = cls()
        state.od_loading_visible = od_loading_visible

        # Generate datetime
        state.datetime_text = cls._generate_datetime(rng)
        state.datetime_position = (1868, 1043)  # Bottom-right of taskbar (+25px right total)

        # Place desktop icons
        state.desktop_icons = cls._place_desktop_icons(rng, num_desktop_icons)

        # Place taskbar icons
        state.taskbar_icons = cls._place_taskbar_icons(rng, num_taskbar_icons)

        return state

    @classmethod
    def _generate_datetime(cls, rng: Any) -> str:
        """Generate a random datetime string in Windows 11 format."""
        # Random hour (1-12), minute, AM/PM
        hour = rng.randint(1, 12)
        minute = rng.randint(0, 59)
        am_pm = rng.choice(["AM", "PM"])

        # Random date
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)  # Safe for all months
        year = rng.randint(2024, 2025)

        return f"{hour}:{minute:02d} {am_pm}\n{month}/{day}/{year}"

    @classmethod
    def _place_desktop_icons(
        cls,
        rng: Any,
        num_icons: int,
    ) -> list[IconPlacement]:
        """Place icons on the desktop with random layout variation.

        Layout styles:
        - stacked: tight grid, column-first
        - sparse: scattered positions with gaps
        - random: random positions within desktop area

        Open Dental and PMS are always included.
        """
        placements: list[IconPlacement] = []

        # Get available icons - required ones first
        required = [k for k, v in DESKTOP_ICONS.items() if v.get("required")]
        optional = [k for k in DESKTOP_ICONS if k not in required]

        # Build icon list: required + random selection from optional
        num_optional = max(0, num_icons - len(required))
        selected_optional = rng.sample(optional, min(num_optional, len(optional)))
        icon_ids = required + selected_optional

        # Shuffle the order (so required icons aren't always first)
        rng.shuffle(icon_ids)

        # Choose layout style randomly
        layout_style = rng.choice(["stacked", "sparse", "random"])

        # Base positions
        start_x = 20
        start_y = 20
        max_rows = 8

        if layout_style == "stacked":
            # Tight grid layout - columns top to bottom
            for i, icon_id in enumerate(icon_ids):
                col = i // max_rows
                row = i % max_rows
                x = start_x + col * DESKTOP_CELL_WIDTH
                y = start_y + row * DESKTOP_CELL_HEIGHT
                icon_info = DESKTOP_ICONS[icon_id]
                placements.append(
                    IconPlacement(
                        icon_id=icon_id,
                        x=x,
                        y=y,
                        width=DESKTOP_ICON_SIZE[0],
                        height=DESKTOP_ICON_SIZE[1],
                        label=icon_info.get("label", ""),
                    )
                )

        elif layout_style == "sparse":
            # Spread out with gaps - skip some grid cells
            cell_positions = []
            for col in range(6):  # 6 columns
                for row in range(max_rows):
                    cell_positions.append((col, row))
            rng.shuffle(cell_positions)
            selected_cells = cell_positions[: len(icon_ids)]
            # Sort to maintain some visual order
            selected_cells.sort(key=lambda c: (c[0], c[1]))

            for (col, row), icon_id in zip(selected_cells, icon_ids):
                x = int(start_x + col * DESKTOP_CELL_WIDTH * 1.5)  # Extra spacing
                y = start_y + row * DESKTOP_CELL_HEIGHT
                icon_info = DESKTOP_ICONS[icon_id]
                placements.append(
                    IconPlacement(
                        icon_id=icon_id,
                        x=int(x),
                        y=int(y),
                        width=DESKTOP_ICON_SIZE[0],
                        height=DESKTOP_ICON_SIZE[1],
                        label=icon_info.get("label", ""),
                    )
                )

        else:  # random
            # Random positions within desktop area (avoid overlap)
            max_x = 1920 - DESKTOP_CELL_WIDTH - 100  # Leave margin
            max_y = 1032 - DESKTOP_CELL_HEIGHT - 50  # Above taskbar
            used_positions: list[tuple[int, int]] = []

            for icon_id in icon_ids:
                # Try to find non-overlapping position
                for _ in range(50):
                    x = rng.randint(start_x, max_x)
                    y = rng.randint(start_y, max_y)
                    # Check for overlap with existing icons
                    overlaps = False
                    for px, py in used_positions:
                        if abs(x - px) < DESKTOP_CELL_WIDTH and abs(y - py) < DESKTOP_CELL_HEIGHT:
                            overlaps = True
                            break
                    if not overlaps:
                        break

                used_positions.append((x, y))
                icon_info = DESKTOP_ICONS[icon_id]
                placements.append(
                    IconPlacement(
                        icon_id=icon_id,
                        x=x,
                        y=y,
                        width=DESKTOP_ICON_SIZE[0],
                        height=DESKTOP_ICON_SIZE[1],
                        label=icon_info.get("label", ""),
                    )
                )

        return placements

    @classmethod
    def _place_taskbar_icons(
        cls,
        rng: Any,
        num_icons: int,
    ) -> list[IconPlacement]:
        """Place icons on the taskbar.

        Icons are placed left to right with consistent gaps.
        Open Dental is always included.
        """
        placements: list[IconPlacement] = []

        # Get available taskbar icons - required ones first
        required = [k for k, v in TASKBAR_ICONS.items() if v.get("required")]
        optional = [k for k in TASKBAR_ICONS if k not in required]

        # Build icon list: required + random selection from optional
        num_optional = max(0, num_icons - len(required))
        selected_optional = rng.sample(optional, min(num_optional, len(optional)))
        selected = required + selected_optional

        # Shuffle the order
        rng.shuffle(selected)

        # Calculate positions - left to right at specified y offset
        x = TASKBAR_LEFT_MARGIN
        y = TASKBAR_Y_OFFSET

        for icon_id in selected:
            placements.append(
                IconPlacement(
                    icon_id=icon_id,
                    x=x,
                    y=y,
                    width=TASKBAR_ICON_SIZE[0],
                    height=TASKBAR_ICON_SIZE[1],
                )
            )
            x += TASKBAR_ICON_SIZE[0] + TASKBAR_ICON_GAP

        return placements

    def get_icon_by_id(self, icon_id: str) -> IconPlacement | None:
        """Find an icon by its ID across desktop and taskbar."""
        for icon in self.desktop_icons:
            if icon.icon_id == icon_id:
                return icon
        for icon in self.taskbar_icons:
            if icon.icon_id == icon_id:
                return icon
        return None

    def get_desktop_icon_by_id(self, icon_id: str) -> IconPlacement | None:
        """Find a desktop icon by its ID."""
        for icon in self.desktop_icons:
            if icon.icon_id == icon_id:
                return icon
        return None

    def get_taskbar_icon_by_id(self, icon_id: str) -> IconPlacement | None:
        """Find a taskbar icon by its ID."""
        for icon in self.taskbar_icons:
            if icon.icon_id == icon_id:
                return icon
        return None

    def to_ground_truth(self) -> dict[str, Any]:
        """Export all placement data as ground truth dict."""
        return {
            "desktop_icons": [
                {
                    "id": icon.icon_id,
                    "label": icon.label,
                    "bounds": icon.bounds,
                    "center": icon.center,
                }
                for icon in self.desktop_icons
            ],
            "taskbar_icons": [
                {
                    "id": icon.icon_id,
                    "bounds": icon.bounds,
                    "center": icon.center,
                }
                for icon in self.taskbar_icons
            ],
            "datetime": {
                "text": self.datetime_text,
                "position": self.datetime_position,
            },
            "od_loading_visible": self.od_loading_visible,
        }
