# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""State definition for Windows 11 desktop generator."""

from dataclasses import dataclass, field
from typing import Any

from cudag.core import BaseState

from screen import (
    ANNOTATION_CONFIG,
    DESKTOP_CELL_HEIGHT,
    DESKTOP_CELL_WIDTH,
    DESKTOP_ICON_SIZE,
    TASKBAR_ICON_GAP,
    TASKBAR_ICON_SIZE,
    TASKBAR_LEFT_MARGIN,
    TASKBAR_Y_OFFSET,
    get_desktop_element,
    get_desktop_icons,
    get_taskbar_element,
    get_taskbar_icons,
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
        **_kwargs: object,  # Accept and ignore unknown kwargs
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

        # Generate datetime - position from annotation text element
        state.datetime_text = cls._generate_datetime(rng)
        state.datetime_position = cls._get_datetime_position()

        # Place desktop icons
        state.desktop_icons = cls._place_desktop_icons(rng, num_desktop_icons)

        # Place taskbar icons
        state.taskbar_icons = cls._place_taskbar_icons(rng, num_taskbar_icons)

        return state

    @classmethod
    def _get_datetime_position(cls) -> tuple[int, int]:
        """Get datetime position from annotation's text element."""
        if ANNOTATION_CONFIG is None:
            return (1868, 1043)  # Fallback position

        # Find the datetime text element
        datetime_el = ANNOTATION_CONFIG.get_element_by_label("datetime")
        if datetime_el is None:
            return (1868, 1043)

        # Return center of the bbox for text alignment
        x, y, w, h = datetime_el.bbox
        return (x + w // 2, y)

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
        """Place icons on the desktop with layout variation.

        Settings from annotation.json:
        - varyN: if true, show random subset of icons
        - randomOrder: if true, shuffle icon order
        - layout: 'stacked', 'sparse', 'random', or empty for random choice

        Icons with required=true are always included when varyN is enabled.
        """
        placements: list[IconPlacement] = []

        # Get icons and element settings from annotation config
        desktop_icons = get_desktop_icons()
        element = get_desktop_element()

        # Get annotation settings (with defaults)
        vary_n = element.vary_n if element else True
        random_order = element.random_order if element else True
        layout = element.layout if element else ""

        # Get available icons - required ones first
        required = [k for k, v in desktop_icons.items() if v.get("required")]
        optional = [k for k in desktop_icons if k not in required]

        # Build icon list based on varyN setting
        if vary_n:
            # VaryN enabled: required + 60-100% of optional icons
            min_optional = int(len(optional) * 0.6)
            max_optional = len(optional)
            k = rng.randint(min_optional, max_optional)
            selected_optional = rng.sample(optional, k)
            icon_ids = required + selected_optional
        else:
            # VaryN disabled: show all icons up to num_icons
            icon_ids = required + optional[:max(0, num_icons - len(required))]

        # Shuffle the order if randomOrder is enabled
        if random_order:
            rng.shuffle(icon_ids)

        # Choose layout style from annotation or randomly
        if layout and layout in ("stacked", "sparse", "random"):
            layout_style = layout
        else:
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
                icon_info = desktop_icons[icon_id]
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
                icon_info = desktop_icons[icon_id]
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
                icon_info = desktop_icons[icon_id]
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

        Settings from annotation.json:
        - varyN: if true, show random subset of icons
        - randomOrder: if true, shuffle icon order
        - layout: 'stacked' (for taskbar, this means linear left-to-right)

        Icons with required=true are always included when varyN is enabled.
        """
        placements: list[IconPlacement] = []

        # Get taskbar icons and element settings from annotation config
        taskbar_icons = get_taskbar_icons()
        element = get_taskbar_element()

        # Get annotation settings (with defaults)
        vary_n = element.vary_n if element else True
        random_order = element.random_order if element else True

        # Get available taskbar icons - required ones first
        required = [k for k, v in taskbar_icons.items() if v.get("required")]
        optional = [k for k in taskbar_icons if k not in required]

        # Build icon list based on varyN setting
        if vary_n:
            # VaryN enabled: required + 40-100% of optional icons
            min_optional = int(len(optional) * 0.4)
            max_optional = len(optional)
            k = rng.randint(min_optional, max_optional)
            selected_optional = rng.sample(optional, k)
            selected = required + selected_optional
        else:
            # VaryN disabled: show all icons up to num_icons
            selected = required + optional[:max(0, num_icons - len(required))]

        # Shuffle the order if randomOrder is enabled
        if random_order:
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
