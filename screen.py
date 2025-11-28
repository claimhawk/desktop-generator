# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Screen definition for Windows 11 desktop generator."""

from typing import Any

from cudag.core import Screen, region


class DesktopScreen(Screen):
    """Windows 11 desktop screen with taskbar.

    Layout:
    - Desktop area: 1920x1032, anchored top-left (icons with labels)
    - Taskbar: 1920x48, anchored bottom-left (icons without labels)
    - DateTime: ~80x30, anchored bottom-right
    """

    class Meta:
        name = "desktop"
        base_image = "blanks/desktop-blank.png"
        size = (1920, 1080)
        task_types = ["click-desktop-icon", "click-taskbar-icon"]

    # Desktop icon area (top portion, leaving room for taskbar)
    desktop_area = region((0, 0, 1920, 1032))

    # Taskbar at bottom
    taskbar = region((0, 1032, 1920, 48))

    # Date/time area in bottom-right of taskbar
    datetime_area = region((1840, 1050, 80, 30))

    # OD Loading panel (centered on screen when visible)
    od_loading_panel = region((708, 365, 502, 304))

    def render(self, state: Any) -> tuple[Any, dict[str, Any]]:
        """Render is handled by the Renderer class."""
        raise NotImplementedError("Use DesktopRenderer instead")


# Icon metadata - desktop icons with labels
DESKTOP_ICONS: dict[str, dict[str, Any]] = {
    "od": {"file": "desktop/icon-od-clean.png", "label": "Open Dental", "required": True},
    "pms": {"file": "desktop/icon-pms-clean.png", "label": "PMS", "required": True},
    "chrome": {"file": "desktop/icon-chrome-clean.png", "label": "Chrome"},
    "edge": {"file": "desktop/icon-edge-clean.png", "label": "Edge"},
    "ezdent": {"file": "desktop/icon-ezdent-clean.png", "label": "EZDent"},
    "brother": {"file": "desktop/icon-brother-clean.png", "label": "Brother"},
    "trash": {"file": "desktop/icon-trash-clean.png", "label": "Recycle Bin"},
}

# Taskbar icons - no labels
TASKBAR_ICONS: dict[str, dict[str, Any]] = {
    "explorer": {"file": "taskbar/icon-tb-explorer.png"},
    "edge": {"file": "taskbar/icon-tb-edge.png"},
    "od": {"file": "taskbar/icon-tb-od.png", "required": True},
}

# Layout constants
DESKTOP_ICON_SIZE = (54, 54)
DESKTOP_ICON_PADDING = 20
DESKTOP_LABEL_HEIGHT = 20
DESKTOP_CELL_WIDTH = DESKTOP_ICON_SIZE[0] + DESKTOP_ICON_PADDING
DESKTOP_CELL_HEIGHT = DESKTOP_ICON_SIZE[1] + DESKTOP_LABEL_HEIGHT + DESKTOP_ICON_PADDING

TASKBAR_ICON_SIZE = (27, 28)
TASKBAR_ICON_GAP = 8
TASKBAR_LEFT_MARGIN = 946  # After start button and search bar (946px from left)
TASKBAR_Y_OFFSET = 1042  # Top of taskbar icons (1039+3px)

DATETIME_FONT_SIZE = 9

# OD Loading panel (centered overlay when visible)
OD_LOADING_PANEL: dict[str, Any] = {
    "file": "panels/od-loading.png",
    "position": (708, 365),  # Centered on 1920x1080 desktop
    "size": (502, 304),
}
