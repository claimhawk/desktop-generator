# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Renderer for Windows 11 desktop generator.

Uses masked.png from assets/annotations as the base image.
Icon positions and labels come from annotation.json.
"""

import base64
import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

from cudag.core import BaseRenderer

from screen import (
    ANNOTATION_CONFIG,
    DATETIME_FONT_SIZE,
    DesktopScreen,
    OD_LOADING_PANEL,
)
from state import DesktopState, IconPlacement


class DesktopRenderer(BaseRenderer[DesktopState]):
    """Renders the Windows 11 desktop screen.

    Composites:
    - Base masked image (from annotations/masked.png)
    - Desktop icons with labels
    - Taskbar icons (no labels)
    - DateTime text in bottom-right

    Icon images are loaded from assets/icons/ directory.
    """

    screen_class = DesktopScreen

    def __init__(self, assets_dir: Path | str = "assets") -> None:
        """Initialize the renderer.

        Args:
            assets_dir: Path to assets directory
        """
        # Initialize attributes BEFORE super().__init__() since it calls load_assets()
        self._icon_cache: dict[str, Image.Image] = {}
        self._font: FreeTypeFont | ImageFont.ImageFont | None = None
        self._datetime_font: FreeTypeFont | ImageFont.ImageFont | None = None
        self._loading_panel: Image.Image | None = None
        self._loading_position: tuple[int, int] = (0, 0)
        super().__init__(assets_dir)

    def load_assets(self) -> None:
        """Load fonts and icon images."""
        # Load fonts
        font_path = self.asset_path("fonts", "segoeui.ttf")
        if font_path.exists():
            self._font = ImageFont.truetype(str(font_path), 11)
            self._datetime_font = ImageFont.truetype(str(font_path), DATETIME_FONT_SIZE)
        else:
            # Fallback to default font
            self._font = ImageFont.load_default()
            self._datetime_font = ImageFont.load_default()

        # Pre-load all icon images from icons directory
        # Icons are named by their snake_case id (matching annotation labels)
        icons_dir = self.asset_path("icons")
        if icons_dir.exists():
            # Load all desktop icons
            desktop_dir = icons_dir / "desktop"
            if desktop_dir.exists():
                for icon_path in desktop_dir.glob("*.png"):
                    # Extract icon_id from filename (e.g., icon-od-clean.png -> od)
                    icon_id = self._extract_icon_id(icon_path.stem)
                    self._icon_cache[f"desktop_{icon_id}"] = (
                        Image.open(icon_path).convert("RGBA")
                    )

            # Load all taskbar icons
            taskbar_dir = icons_dir / "taskbar"
            if taskbar_dir.exists():
                for icon_path in taskbar_dir.glob("*.png"):
                    icon_id = self._extract_icon_id(icon_path.stem)
                    self._icon_cache[f"taskbar_{icon_id}"] = (
                        Image.open(icon_path).convert("RGBA")
                    )

        # Load loading panel from annotation base64 image
        self._load_loading_panel_from_annotation()

    def _load_loading_panel_from_annotation(self) -> None:
        """Load loading panel from annotation's base64 image data."""
        if ANNOTATION_CONFIG is None:
            return

        loading_el = ANNOTATION_CONFIG.get_loading_element()
        if loading_el is None or not loading_el.loading_image:
            # Fallback to file-based loading panel
            panel_path = self.asset_path(OD_LOADING_PANEL["file"])
            if panel_path.exists():
                self._loading_panel = Image.open(panel_path).convert("RGBA")
                self._loading_position = OD_LOADING_PANEL["position"]
            return

        # Parse base64 image data (format: data:image/png;base64,...)
        base64_data = loading_el.loading_image
        if base64_data.startswith("data:"):
            # Strip data URL prefix
            base64_data = base64_data.split(",", 1)[1]

        image_bytes = base64.b64decode(base64_data)
        self._loading_panel = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        self._loading_position = (loading_el.bbox[0], loading_el.bbox[1])

    def _extract_icon_id(self, filename: str) -> str:
        """Extract icon ID from filename.

        Examples:
            icon-od-clean -> od
            icon-chrome-clean -> chrome
            icon-tb-od -> od
        """
        # Remove common prefixes/suffixes
        name = filename.lower()
        for prefix in ("icon-", "icon_", "tb-", "tb_"):
            if name.startswith(prefix):
                name = name[len(prefix):]
        for suffix in ("-clean", "_clean"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name

    # Map annotation labels to file-based icon IDs
    _ICON_ALIASES: dict[str, str] = {
        # Desktop icons: annotation label -> file ID
        "open_dental": "od",
        "google_chrome": "chrome",
        "microsoft_edge": "edge",
        "recycle_bin": "trash",
        "acrobat_reader": "acrobat",
        "od_zapata": "od",  # fallback to OD icon
        "office_shsre": "office",
        "brother_iprint": "brother",
        "brother_utilities": "brother",
        "brother_creative": "brother",
        "pms_dental": "pms",
        # Taskbar icons
        "file_explorer": "explorer",
    }

    def _resolve_icon_key(self, prefix: str, icon_id: str) -> str | None:
        """Resolve an icon_id to a cache key, trying aliases if needed.

        Args:
            prefix: 'desktop' or 'taskbar'
            icon_id: The icon ID from state (may be annotation-based or file-based)

        Returns:
            Cache key if found, None otherwise
        """
        # Try direct lookup first
        cache_key = f"{prefix}_{icon_id}"
        if cache_key in self._icon_cache:
            return cache_key

        # Try alias mapping
        alias = self._ICON_ALIASES.get(icon_id)
        if alias:
            cache_key = f"{prefix}_{alias}"
            if cache_key in self._icon_cache:
                return cache_key

        return None

    def load_base_image(self) -> Image.Image:
        """Load the base image for rendering.

        Uses masked.png from annotations if available, otherwise falls back
        to the blank desktop image.
        """
        # Try to use masked image from annotations
        if ANNOTATION_CONFIG and ANNOTATION_CONFIG.masked_image_path:
            masked_path = ANNOTATION_CONFIG.masked_image_path
            if masked_path.exists():
                return Image.open(masked_path).convert("RGBA")

        # Fallback to configured base image
        return super().load_base_image()

    def render(self, state: DesktopState) -> tuple[Image.Image, dict[str, Any]]:
        """Render the desktop with icons and datetime.

        Args:
            state: Current desktop state with icon placements

        Returns:
            (PIL Image, metadata dict with ground truth)
        """
        # Load base image
        image = self.load_base_image().convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Draw desktop icons with labels
        for icon in state.desktop_icons:
            self._draw_desktop_icon(image, draw, icon)

        # Draw taskbar icons (no labels)
        for icon in state.taskbar_icons:
            self._draw_taskbar_icon(image, icon)

        # Draw datetime
        self._draw_datetime(draw, state)

        # Draw loading panel if visible (overlays everything)
        if state.od_loading_visible:
            self._draw_loading_panel(image)

        # Convert back to RGB for saving
        final_image = image.convert("RGB")

        # Build metadata with ground truth
        metadata = self.build_metadata(state)
        metadata["ground_truth"] = state.to_ground_truth()

        return final_image, metadata

    def _draw_desktop_icon(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        icon: IconPlacement,
    ) -> None:
        """Draw a desktop icon with its label."""
        cache_key = self._resolve_icon_key("desktop", icon.icon_id)
        if cache_key is None:
            return

        icon_img = self._icon_cache[cache_key]

        # Paste icon at position
        image.paste(icon_img, (icon.x, icon.y), icon_img)

        # Draw label below icon, centered
        if icon.label and self._font:
            # Calculate text position (centered below icon)
            bbox = draw.textbbox((0, 0), icon.label, font=self._font)
            text_width = bbox[2] - bbox[0]
            text_x = icon.x + (icon.width - text_width) // 2
            text_y = icon.y + icon.height + 2  # Small gap below icon

            # Draw text with shadow for readability
            draw.text((text_x + 1, text_y + 1), icon.label, fill="black", font=self._font)
            draw.text((text_x, text_y), icon.label, fill="white", font=self._font)

    def _draw_taskbar_icon(
        self,
        image: Image.Image,
        icon: IconPlacement,
    ) -> None:
        """Draw a taskbar icon (no label)."""
        cache_key = self._resolve_icon_key("taskbar", icon.icon_id)
        if cache_key is None:
            return

        icon_img = self._icon_cache[cache_key]

        # Paste icon at position
        image.paste(icon_img, (icon.x, icon.y), icon_img)

    def _draw_datetime(
        self,
        draw: ImageDraw.ImageDraw,
        state: DesktopState,
    ) -> None:
        """Draw the datetime in the bottom-right of taskbar."""
        if not state.datetime_text or not self._datetime_font:
            return

        x, y = state.datetime_position

        # Split into time and date lines - black text, center-aligned on taskbar
        lines = state.datetime_text.split("\n")
        for i, line in enumerate(lines):
            line_y = y + i * (DATETIME_FONT_SIZE + 2)
            # Center align text
            bbox = draw.textbbox((0, 0), line, font=self._datetime_font)
            text_width = bbox[2] - bbox[0]
            text_x = x - text_width // 2
            draw.text((text_x, line_y), line, fill="black", font=self._datetime_font)

    def _draw_loading_panel(self, image: Image.Image) -> None:
        """Draw the loading splash panel from annotation."""
        if self._loading_panel is None:
            return

        # Paste panel with alpha channel at position from annotation
        x, y = self._loading_position
        image.paste(self._loading_panel, (x, y), self._loading_panel)
