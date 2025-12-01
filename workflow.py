# Copyright (c) 2025 Tylt LLC. All rights reserved.

"""Workflow integration for single screen generation.

This module provides functions for the workflow-generator to render
single desktop screens with specific data and get ground truths.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from PIL import Image

from renderer import DesktopRenderer
from state import DesktopState


@dataclass
class WorkflowScreenResult:
    """Result from rendering a workflow screen."""

    image: Image.Image
    """Rendered screenshot."""

    prompt: str
    """Human instruction prompt for this step."""

    ground_truth: dict[str, Any]
    """Ground truth action with coordinates."""

    metadata: dict[str, Any]
    """Additional metadata."""


def render_desktop_click_od(
    rng: Random | None = None,
    datetime_text: str | None = None,
) -> WorkflowScreenResult:
    """Render desktop screen for clicking Open Dental icon.

    Args:
        rng: Random number generator (uses default if None)
        datetime_text: Specific datetime text (random if None)

    Returns:
        WorkflowScreenResult with image, prompt, and ground truth
    """
    if rng is None:
        rng = Random(42)

    # Generate state with OD on desktop
    state = DesktopState.generate(
        rng,
        num_desktop_icons=5,
        num_taskbar_icons=2,
        od_loading_visible=False,
    )

    # Override datetime if provided
    if datetime_text:
        state.datetime_text = datetime_text

    # Render
    renderer = DesktopRenderer()
    image, metadata = renderer.render(state)

    # Get OD icon coordinates
    od_icon = state.get_desktop_icon_by_id("od")
    if od_icon is None:
        raise ValueError("Open Dental icon not found in state")

    click_x, click_y = od_icon.center

    # Normalize to [0, 1000] RU
    img_w, img_h = image.size
    norm_x = int((click_x / img_w) * 1000)
    norm_y = int((click_y / img_h) * 1000)

    return WorkflowScreenResult(
        image=image,
        prompt="Double-click the Open Dental icon on the desktop",
        ground_truth={
            "name": "computer",
            "arguments": {
                "action": "double_click",
                "coordinate": [norm_x, norm_y],
            },
        },
        metadata={
            "task_type": "click-desktop-icon",
            "target_icon": "od",
            "real_coords": [click_x, click_y],
            "icon_bounds": od_icon.bounds,
            "tolerance": [30, 30],
        },
    )


def render_desktop_od_loading(
    rng: Random | None = None,
    datetime_text: str | None = None,
) -> WorkflowScreenResult:
    """Render desktop screen with Open Dental loading splash.

    Args:
        rng: Random number generator
        datetime_text: Specific datetime text

    Returns:
        WorkflowScreenResult for wait action
    """
    if rng is None:
        rng = Random(42)

    # Generate state with OD loading panel visible
    state = DesktopState.generate(
        rng,
        num_desktop_icons=5,
        num_taskbar_icons=2,
        od_loading_visible=True,
    )

    if datetime_text:
        state.datetime_text = datetime_text

    # Render
    renderer = DesktopRenderer()
    image, metadata = renderer.render(state)

    return WorkflowScreenResult(
        image=image,
        prompt="Wait for Open Dental to finish loading",
        ground_truth={
            "name": "computer",
            "arguments": {
                "action": "wait",
                "duration": 2,
            },
        },
        metadata={
            "task_type": "wait-loading",
            "od_loading_visible": True,
        },
    )


def render_desktop_click_taskbar_od(
    rng: Random | None = None,
    datetime_text: str | None = None,
) -> WorkflowScreenResult:
    """Render desktop screen for clicking Open Dental in taskbar.

    Args:
        rng: Random number generator
        datetime_text: Specific datetime text

    Returns:
        WorkflowScreenResult with image, prompt, and ground truth
    """
    if rng is None:
        rng = Random(42)

    # Generate state with OD in taskbar
    state = DesktopState.generate(
        rng,
        num_desktop_icons=4,
        num_taskbar_icons=3,
        od_loading_visible=False,
    )

    if datetime_text:
        state.datetime_text = datetime_text

    # Render
    renderer = DesktopRenderer()
    image, metadata = renderer.render(state)

    # Get OD taskbar icon coordinates
    od_icon = state.get_taskbar_icon_by_id("od")
    if od_icon is None:
        raise ValueError("Open Dental taskbar icon not found in state")

    click_x, click_y = od_icon.center

    # Normalize to [0, 1000] RU
    img_w, img_h = image.size
    norm_x = int((click_x / img_w) * 1000)
    norm_y = int((click_y / img_h) * 1000)

    return WorkflowScreenResult(
        image=image,
        prompt="Click the Open Dental icon in the taskbar",
        ground_truth={
            "name": "computer",
            "arguments": {
                "action": "left_click",
                "coordinate": [norm_x, norm_y],
            },
        },
        metadata={
            "task_type": "click-taskbar-icon",
            "target_icon": "od",
            "real_coords": [click_x, click_y],
            "icon_bounds": od_icon.bounds,
            "tolerance": [15, 15],
        },
    )
