# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Screen definition for Windows 11 desktop generator.

Icon definitions and task templates are loaded from assets/annotations/annotation.json.
To modify icons or prompts, edit the annotation file and regenerate.
"""

from pathlib import Path
from typing import Any

from cudag.annotation import AnnotationConfig
from cudag.core import Screen, region


# Load annotation config at module level
_ANNOTATIONS_DIR = Path(__file__).parent / "assets" / "annotations"
ANNOTATION_CONFIG: AnnotationConfig | None = None

if _ANNOTATIONS_DIR.exists():
    ANNOTATION_CONFIG = AnnotationConfig.load(_ANNOTATIONS_DIR)


class DesktopScreen(Screen):
    """Windows 11 desktop screen with taskbar.

    Layout:
    - Desktop area: 1920x1032, anchored top-left (icons with labels)
    - Taskbar: 1920x48, anchored bottom-left (icons without labels)
    - DateTime: ~80x30, anchored bottom-right
    """

    class Meta:
        name = "desktop"
        base_image = "annotations/masked.png"  # Use masked image as base
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


def get_desktop_icons() -> dict[str, dict[str, Any]]:
    """Get desktop icons from annotation config.

    Returns dict mapping icon_id to icon metadata including label.
    The 'required' flag comes directly from the annotation.
    """
    if ANNOTATION_CONFIG is None:
        return _FALLBACK_DESKTOP_ICONS

    icons = ANNOTATION_CONFIG.get_labeled_icons("desktop")
    result: dict[str, dict[str, Any]] = {}

    for icon in icons:
        # Create icon_id from label (snake_case)
        icon_id = ANNOTATION_CONFIG.to_snake_case(icon.label)
        result[icon_id] = {
            "label": icon.label,
            "center": icon.absolute_center,
            # Use required flag from annotation
            "required": icon.required,
        }

    return result


def get_taskbar_icons() -> dict[str, dict[str, Any]]:
    """Get taskbar icons from annotation config.

    Returns dict mapping icon_file_id to icon metadata.
    Only includes icons with icon_file_id set (those that map to actual image files).
    Taskbar icons have no text labels - icon_file_id maps to image files (e.g., 'od' -> icon-tb-od.png).
    The 'required' flag comes directly from the annotation.
    """
    if ANNOTATION_CONFIG is None:
        return _FALLBACK_TASKBAR_ICONS

    element = ANNOTATION_CONFIG.get_element_by_label("taskbar")
    if element is None:
        return _FALLBACK_TASKBAR_ICONS

    result: dict[str, dict[str, Any]] = {}
    for icon in element.icons:
        # Only include icons with iconFileId set (maps to actual image files)
        # Icons without iconFileId cannot be rendered
        if icon.icon_file_id:
            result[icon.icon_file_id] = {
                "label": icon.icon_file_id,
                "center": icon.absolute_center,
                "required": icon.required,
                "element_id": icon.element_id,
            }

    # If no icons with iconFileId, use fallback
    if not result:
        return _FALLBACK_TASKBAR_ICONS

    return result


def get_desktop_element() -> Any:
    """Get the desktop iconlist element from annotation."""
    if ANNOTATION_CONFIG is None:
        return None
    return ANNOTATION_CONFIG.get_element_by_label("desktop")


def get_taskbar_element() -> Any:
    """Get the taskbar iconlist element from annotation."""
    if ANNOTATION_CONFIG is None:
        return None
    return ANNOTATION_CONFIG.get_element_by_label("taskbar")


# Fallback icon definitions if annotation not available
_FALLBACK_DESKTOP_ICONS: dict[str, dict[str, Any]] = {
    "open_dental": {"label": "Open Dental", "required": True},
    "pms": {"label": "PMS", "required": True},
    "chrome": {"label": "Chrome"},
    "edge": {"label": "Edge"},
}

_FALLBACK_TASKBAR_ICONS: dict[str, dict[str, Any]] = {
    "explorer": {"label": "File Explorer"},
    "edge": {"label": "Microsoft Edge"},
    "od": {"label": "Open Dental", "required": True},
}

# Layout constants (from annotation if available)
if ANNOTATION_CONFIG:
    _desktop_el = get_desktop_element()
    if _desktop_el and _desktop_el.icon_width:
        DESKTOP_ICON_SIZE = (_desktop_el.icon_width, _desktop_el.icon_height)
    else:
        DESKTOP_ICON_SIZE = (50, 50)
else:
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

# Legacy exports for backwards compatibility
DESKTOP_ICONS = get_desktop_icons()
TASKBAR_ICONS = get_taskbar_icons()


# -----------------------------------------------------------------------------
# Scaling
# -----------------------------------------------------------------------------

# Desktop-generator renders at native annotation size (1920x1080)
_ANNOTATION_SIZE = tuple(ANNOTATION_CONFIG.image_size) if ANNOTATION_CONFIG else (1920, 1080)
_GENERATOR_SIZE = (1920, 1080)  # From DesktopScreen.Meta.size

_SCALE_X = _GENERATOR_SIZE[0] / _ANNOTATION_SIZE[0]
_SCALE_Y = _GENERATOR_SIZE[1] / _ANNOTATION_SIZE[1]

# Export image dimensions for grounding tasks
IMAGE_WIDTH, IMAGE_HEIGHT = _GENERATOR_SIZE


def scale_bbox(bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Scale bbox (x, y, width, height) from annotation to generator space."""
    x, y, w, h = bbox
    return (int(x * _SCALE_X), int(y * _SCALE_Y), int(w * _SCALE_X), int(h * _SCALE_Y))


# -----------------------------------------------------------------------------
# Grounding Task Accessors
# -----------------------------------------------------------------------------

def get_all_groundable_elements() -> list[tuple[str, tuple[int, int, int, int]]]:
    """Get all elements suitable for grounding tasks with scaled bboxes.

    Returns:
        List of (label, scaled_bbox) tuples.
        Bbox is (x, y, width, height) in generator coordinate space.
    """
    results: list[tuple[str, tuple[int, int, int, int]]] = []
    if ANNOTATION_CONFIG is None:
        return results

    for el in ANNOTATION_CONFIG.elements:
        if el.label:
            results.append((el.label, scale_bbox(el.bbox)))
    return results


def get_element_bbox(name: str) -> tuple[int, int, int, int]:
    """Get scaled bounding box for an element by name."""
    if ANNOTATION_CONFIG is None:
        raise ValueError("Annotation config not available")

    el = ANNOTATION_CONFIG.get_element_by_label(name)
    if el is None:
        raise ValueError(f"Element '{name}' not found in annotation")
    return scale_bbox(el.bbox)
