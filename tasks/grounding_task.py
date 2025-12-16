# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Grounding task for desktop-generator.

Generates samples for element bounding box detection (grounding).
"""

from __future__ import annotations

from typing import Any

from cudag.core import BaseTask, TaskContext, TaskSample, TestCase
from cudag.core.grounding_task import bbox_to_ru
from cudag.prompts.tools import BboxCall

from screen import get_all_groundable_elements
from state import DesktopState


# Grounding prompt templates
GROUNDING_PROMPTS = [
    "Locate the {element}",
    "Find the bounding box of the {element}",
    "Where is the {element}?",
    "Identify the {element} region",
]


class GroundingTask(BaseTask):
    """Task that generates grounding samples for element detection."""

    task_type = "grounding"

    def __init__(self, config: dict[str, Any], renderer: Any) -> None:
        """Initialize the grounding task."""
        super().__init__(config, renderer)
        self._groundable_elements = get_all_groundable_elements()

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate a grounding training sample."""
        # Generate and render state
        state = DesktopState.generate(ctx.rng)
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        # Pick a random element
        element_label, element_bbox = ctx.rng.choice(self._groundable_elements)

        # Convert bbox to RU coordinates [x1, y1, x2, y2]
        bbox_ru = bbox_to_ru(element_bbox, image.size)

        # Random prompt
        prompt_template = ctx.rng.choice(GROUNDING_PROMPTS)
        prompt = prompt_template.format(element=element_label)

        # Create BboxCall
        bbox_call = BboxCall.create(label=element_label, bbox_2d=bbox_ru)

        # Center point for metadata
        center_x = element_bbox[0] + element_bbox[2] // 2
        center_y = element_bbox[1] + element_bbox[3] // 2

        return TaskSample(
            id=self.build_id(ctx),
            image_path=image_path,
            human_prompt=prompt,
            tool_call=bbox_call,  # type: ignore[arg-type]
            pixel_coords=(center_x, center_y),
            metadata={
                "task_type": self.task_type,
                "element_label": element_label,
                "bbox_pixels": list(element_bbox),
                "bbox_ru": list(bbox_ru),
            },
            image_size=image.size,
        )

    def generate_test(self, ctx: TaskContext) -> TestCase:
        """Generate a grounding test case."""
        # Generate and render state
        state = DesktopState.generate(ctx.rng)
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx, prefix="test")

        # Pick a random element
        element_label, element_bbox = ctx.rng.choice(self._groundable_elements)

        # Convert bbox to RU coordinates [x1, y1, x2, y2]
        bbox_ru = bbox_to_ru(element_bbox, image.size)

        # Random prompt
        prompt_template = ctx.rng.choice(GROUNDING_PROMPTS)
        prompt = prompt_template.format(element=element_label)

        # Expected action as dict
        expected_action = {
            "name": "get_bbox",
            "arguments": {
                "element": element_label,
                "bbox_2d": list(bbox_ru),
            },
        }

        # Center point
        center_x = element_bbox[0] + element_bbox[2] // 2
        center_y = element_bbox[1] + element_bbox[3] // 2

        return TestCase(
            test_id=f"test_{ctx.index:04d}",
            screenshot=image_path,
            prompt=prompt,
            expected_action=expected_action,
            tolerance=(50, 50),  # Generous tolerance for bbox matching
            metadata={
                "task_type": self.task_type,
                "element_label": element_label,
                "bbox_pixels": list(element_bbox),
                "image_size": image.size,
            },
            pixel_coords=(center_x, center_y),
        )
