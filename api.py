# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Public API for generating desktop samples.

This module provides the entry points for other projects to generate
Windows 11 desktop screenshots and training samples.

All images are cropped to the desktop bbox (no taskbar).

Usage:
    from api import generate_sample, generate_tasks
    from state import DesktopState

    # Generate one grounding sample
    state = DesktopState.generate(rng)
    sample = generate_sample("grounding", state)

    # Generate iconlist samples (returns multiple per image)
    samples = generate_sample("iconlist", state)

    # Generate wait samples when loading visible
    state_loading = DesktopState.generate(rng, od_loading_visible=True)
    samples = generate_sample("wait-loading", state_loading)
"""

from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any

from PIL import Image

from renderer import DesktopRenderer
from state import DesktopState


@dataclass
class GeneratedSample:
    """A generated sample with image and task data."""

    task_type: str
    image: Image.Image
    prompt: str
    action: dict[str, Any]
    pixel_coords: tuple[int, int]
    tolerance: tuple[float, float]
    metadata: dict[str, Any]


# Module-level renderer (lazy initialized)
_renderer: DesktopRenderer | None = None


def _get_renderer() -> DesktopRenderer:
    """Get or create the renderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = DesktopRenderer(assets_dir=Path("assets"))
        _renderer.load_assets()
    return _renderer


def _get_desktop_bbox() -> tuple[int, int, int, int]:
    """Get the desktop element bbox from annotation."""
    from screen import ANNOTATION_CONFIG
    if ANNOTATION_CONFIG is None:
        return (0, 0, 1914, 1032)  # Default
    element = ANNOTATION_CONFIG.get_element_by_label("desktop")
    if element is None:
        return (0, 0, 1914, 1032)
    return element.bbox


def _crop_to_desktop(image: Image.Image) -> Image.Image:
    """Crop image to desktop bbox."""
    bbox = _get_desktop_bbox()
    crop_box = (bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3])
    return image.crop(crop_box)


def generate_sample(
    task_type: str,
    state: DesktopState | None = None,
    *,
    rng: Random | None = None,
    element_label: str | None = None,
) -> GeneratedSample | list[GeneratedSample]:
    """Generate sample(s) for a task type given state.

    Args:
        task_type: One of "iconlist", "wait-loading", "grounding"
        state: The desktop state to render (generated if None)
        rng: Random number generator (created if None)
        element_label: For grounding task, specific element to locate

    Returns:
        GeneratedSample for grounding task, or list[GeneratedSample] for
        iconlist and wait-loading tasks (which produce multiple samples
        per image).
    """
    renderer = _get_renderer()
    if rng is None:
        rng = Random()

    # Generate state if not provided
    if state is None:
        od_loading = task_type == "wait-loading"
        state = DesktopState.generate(
            rng, od_loading_visible=od_loading, num_taskbar_icons=0
        )

    # Render the image once
    image, metadata = renderer.render(state)

    if task_type == "iconlist":
        return _generate_iconlist_samples(renderer, state, image, rng)

    elif task_type == "wait-loading":
        return _generate_wait_samples(renderer, state, image, rng)

    elif task_type == "grounding":
        return _generate_grounding_sample(
            renderer, state, image, rng, element_label
        )

    else:
        raise ValueError(f"Unknown task type: {task_type}")


def _generate_iconlist_samples(
    renderer: DesktopRenderer,
    state: DesktopState,
    image: Image.Image,
    rng: Random,
) -> list[GeneratedSample]:
    """Generate iconlist samples with desktop cropping."""
    from screen import ANNOTATION_CONFIG, get_desktop_icons

    if ANNOTATION_CONFIG is None:
        return []

    desktop_element = ANNOTATION_CONFIG.get_element_by_label("desktop")
    if desktop_element is None:
        return []

    # Crop to desktop bbox
    cropped_img = _crop_to_desktop(image)
    crop_x, crop_y = desktop_element.bbox[0], desktop_element.bbox[1]

    samples: list[GeneratedSample] = []
    icons_in_state = state.desktop_icons
    icons_info = get_desktop_icons()

    # Get click tasks for desktop element
    for ann_task in ANNOTATION_CONFIG.tasks:
        if ann_task.target_element_id != desktop_element.element_id:
            continue
        if ann_task.action not in ("left_click", "double_click"):
            continue

        # Generate sample for each icon
        for icon in icons_in_state:
            icon_info = icons_info.get(icon.icon_id, {})
            label = icon_info.get("label", icon.icon_id)

            prompt = ann_task.prompt_template.replace("[icon_label]", label)

            # Coordinates relative to crop region
            abs_x, abs_y = icon.center
            rel_x = abs_x - crop_x
            rel_y = abs_y - crop_y

            # Convert to RU based on cropped image size
            ru_x = int((rel_x / cropped_img.width) * 1000)
            ru_y = int((rel_y / cropped_img.height) * 1000)

            action = {
                "name": "computer_use",
                "arguments": {
                    "action": ann_task.action,
                    "coordinate": [ru_x, ru_y],
                },
            }

            samples.append(
                GeneratedSample(
                    task_type=ann_task.task_type,
                    image=cropped_img,
                    prompt=prompt,
                    action=action,
                    pixel_coords=(rel_x, rel_y),
                    tolerance=(30.0, 30.0),
                    metadata={
                        "element_type": desktop_element.element_type,
                        "element_label": "desktop",
                        "icon_id": icon.icon_id,
                        "icon_label": label,
                        "crop_region": desktop_element.bbox,
                    },
                )
            )

    return samples


# Wait-specific prompts for API
_WAIT_PROMPTS = [
    "A loading screen is visible. What action should you take?",
    "The application is loading. What should you do?",
    "Open Dental is starting up. What action is appropriate?",
]


def _generate_wait_samples(
    renderer: DesktopRenderer,
    state: DesktopState,
    image: Image.Image,
    rng: Random,
) -> list[GeneratedSample]:
    """Generate wait samples with desktop cropping when loading visible."""
    from screen import ANNOTATION_CONFIG

    if ANNOTATION_CONFIG is None:
        return []

    wait_task = ANNOTATION_CONFIG.get_wait_task()
    if wait_task is None:
        return []

    wait_time = wait_task.wait_time if wait_task.wait_time > 0 else 3.0

    desktop_element = ANNOTATION_CONFIG.get_element_by_label("desktop")
    if desktop_element is None:
        return []

    # Crop to desktop bbox
    cropped_img = _crop_to_desktop(image)

    samples: list[GeneratedSample] = []

    # Generate one sample per prompt
    for prompt in _WAIT_PROMPTS:
        action = {
            "name": "computer_use",
            "arguments": {
                "action": "wait",
                "duration": wait_time,
            },
        }

        samples.append(
            GeneratedSample(
                task_type=wait_task.task_type,
                image=cropped_img,
                prompt=prompt,
                action=action,
                pixel_coords=(0, 0),
                tolerance=(0.0, 0.0),
                metadata={
                    "wait_seconds": wait_time,
                    "element_label": "desktop",
                    "crop_region": desktop_element.bbox,
                },
            )
        )

    return samples


def _generate_grounding_sample(
    renderer: DesktopRenderer,
    state: DesktopState,
    image: Image.Image,
    rng: Random,
    element_label: str | None = None,
) -> GeneratedSample:
    """Generate a grounding sample for element detection."""
    from screen import get_all_groundable_elements
    from cudag.core.grounding_task import bbox_to_ru

    groundable = get_all_groundable_elements()
    if not groundable:
        raise ValueError("No groundable elements found in annotation")

    # Select element
    if element_label:
        matches = [(lbl, b) for lbl, b in groundable if lbl == element_label]
        if not matches:
            raise ValueError(f"Element '{element_label}' not found")
        label, bbox = matches[0]
    else:
        label, bbox = rng.choice(groundable)

    # Convert bbox to RU [x1, y1, x2, y2]
    bbox_ru = bbox_to_ru(bbox, image.size)

    # Random prompt
    prompts = [
        f"Locate the {label}",
        f"Find the bounding box of the {label}",
        f"Where is the {label}?",
        f"Identify the {label} region",
    ]
    prompt = rng.choice(prompts)

    action = {
        "name": "get_bbox",
        "arguments": {
            "element": label,
            "bbox_2d": list(bbox_ru),
        },
    }

    # Center point
    center_x = bbox[0] + bbox[2] // 2
    center_y = bbox[1] + bbox[3] // 2

    return GeneratedSample(
        task_type="grounding",
        image=image,
        prompt=prompt,
        action=action,
        pixel_coords=(center_x, center_y),
        tolerance=(50.0, 50.0),
        metadata={
            "element_label": label,
            "bbox_pixels": list(bbox),
            "bbox_ru": list(bbox_ru),
        },
    )


def generate_tasks(
    task_types: list[str],
    state_map: dict[str, tuple[DesktopState, dict[str, Any]]] | None = None,
    *,
    rng: Random | None = None,
) -> list[GeneratedSample]:
    """Generate samples for multiple task types.

    Args:
        task_types: List of task types to generate
        state_map: Optional dict mapping task_type -> (state, kwargs)
            If not provided, states are generated automatically.
        rng: Random number generator

    Returns:
        Flat list of GeneratedSample objects (iconlist and wait-loading
        tasks produce multiple samples per call).
    """
    if rng is None:
        rng = Random()

    all_samples: list[GeneratedSample] = []

    for task_type in task_types:
        if state_map and task_type in state_map:
            state, kwargs = state_map[task_type]
        else:
            state = None
            kwargs = {}

        result = generate_sample(task_type, state, rng=rng, **kwargs)

        if isinstance(result, list):
            all_samples.extend(result)
        else:
            all_samples.append(result)

    return all_samples
