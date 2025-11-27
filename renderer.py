# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Renderer for Windows 11 desktop generator."""

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from cudag.core import BaseRenderer

from screen import (
    DATETIME_FONT_SIZE,
    DESKTOP_ICONS,
    DesktopScreen,
    TASKBAR_ICONS,
)
from state import DesktopState, IconPlacement


class DesktopRenderer(BaseRenderer[DesktopState]):
    """Renders the Windows 11 desktop screen.

    Composites:
    - Base blank desktop image
    - Desktop icons with labels
    - Taskbar icons (no labels)
    - DateTime text in bottom-right
    """

    screen_class = DesktopScreen

    def __init__(self, assets_dir: Path | str = "assets") -> None:
        """Initialize the renderer.

        Args:
            assets_dir: Path to assets directory
        """
        # Initialize attributes BEFORE super().__init__() since it calls load_assets()
        self._icon_cache: dict[str, Image.Image] = {}
        self._font: ImageFont.FreeTypeFont | None = None
        self._datetime_font: ImageFont.FreeTypeFont | None = None
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

        # Pre-load all icon images
        icons_dir = self.asset_path("icons")
        if icons_dir.exists():
            # Load desktop icons
            for icon_id, info in DESKTOP_ICONS.items():
                icon_path = icons_dir / info["file"]
                if icon_path.exists():
                    self._icon_cache[f"desktop_{icon_id}"] = Image.open(icon_path).convert("RGBA")

            # Load taskbar icons
            for icon_id, info in TASKBAR_ICONS.items():
                icon_path = icons_dir / info["file"]
                if icon_path.exists():
                    self._icon_cache[f"taskbar_{icon_id}"] = Image.open(icon_path).convert("RGBA")

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
        cache_key = f"desktop_{icon.icon_id}"
        if cache_key not in self._icon_cache:
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
        cache_key = f"taskbar_{icon.icon_id}"
        if cache_key not in self._icon_cache:
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
