# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Wait task for when loading panel is visible.

When loading is visible, the model should output a wait action instead of clicking.
Images are cropped to the desktop bbox (same as IconListTask).

Prompts explicitly mention the loading state to provide clear training signal.
"""

from PIL import Image

from cudag.core import BaseTask, TaskContext, TaskSample, TestCase
from cudag.prompts.tools import ToolCall

from screen import ANNOTATION_CONFIG, get_desktop_icons
from state import DesktopState


# Wait-specific prompts that clearly indicate loading state
WAIT_PROMPTS = [
    "A loading screen is visible. What action should you take?",
    "The application is loading. What should you do?",
    "Open Dental is starting up. What action is appropriate?",
    "A loading indicator is displayed. What is the correct action?",
    "The software is initializing. What should you do next?",
]


class WaitLoadingTask(BaseTask):
    """Wait when loading panel is visible.

    When the loading panel is visible, the model should output wait action.
    Uses clear wait-specific prompts to provide unambiguous training signal.

    Images are cropped to desktop bbox (no taskbar).
    """

    task_type = "wait-loading"

    def _get_desktop_element(self):
        """Get the desktop element from annotation config."""
        if ANNOTATION_CONFIG is None:
            return None
        return ANNOTATION_CONFIG.get_element_by_label("desktop")

    def _crop_to_desktop(
        self, full_image: Image.Image, ctx: TaskContext
    ) -> tuple[Image.Image, str, tuple[int, int, int, int]]:
        """Crop full image to desktop bbox and save."""
        element = self._get_desktop_element()
        if element is None:
            raise ValueError("Desktop element not found in annotation")

        bbox = element.bbox
        crop_box = (bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3])
        cropped = full_image.crop(crop_box)
        path = self.save_image(cropped, ctx, prefix="wait_desktop")
        return cropped, path, bbox

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate wait samples with loading panel visible.

        Uses wait-specific prompts and crops to desktop bbox.
        """
        if ANNOTATION_CONFIG is None:
            return []

        wait_task = ANNOTATION_CONFIG.get_wait_task()
        if wait_task is None:
            return []

        wait_time = wait_task.wait_time if wait_task.wait_time > 0 else 3.0

        desktop_element = self._get_desktop_element()
        if desktop_element is None:
            return []

        # Generate state with loading visible
        num_desktop = ctx.rng.randint(3, 7)
        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=0,
            od_loading_visible=True,
        )

        # Render and crop to desktop
        full_image, metadata = self.renderer.render(state)
        cropped_img, image_path, bbox = self._crop_to_desktop(full_image, ctx)
        crop_x, crop_y = bbox[0], bbox[1]

        desktop_icons = get_desktop_icons()
        icons_in_state = state.desktop_icons

        # Build ground truth with adjusted coordinates
        ground_truth = {
            "icons": [
                {
                    "id": i.icon_id,
                    "label": desktop_icons.get(i.icon_id, {}).get("label", i.icon_id),
                    "center": (i.center[0] - crop_x, i.center[1] - crop_y),
                }
                for i in icons_in_state
            ],
            "od_loading_visible": True,
        }

        samples: list[TaskSample] = []

        # Generate one sample per wait prompt (not per icon)
        for prompt in WAIT_PROMPTS:
            samples.append(
                TaskSample(
                    id=self.build_id(ctx, f"_wait"),
                    image_path=image_path,
                    human_prompt=prompt,
                    tool_call=ToolCall.wait(wait_time),
                    pixel_coords=(0, 0),
                    metadata={
                        "task_type": wait_task.task_type,
                        "wait_seconds": wait_time,
                        "element_label": "desktop",
                        "crop_region": bbox,
                        "ground_truth": ground_truth,
                        "tolerance": [0, 0],
                    },
                    image_size=cropped_img.size,
                )
            )

        return samples

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate one wait sample."""
        samples = self.generate_samples(ctx)
        if not samples:
            raise ValueError("No wait samples generated")
        return samples[0]

    def generate_tests(self, ctx: TaskContext) -> list[TestCase]:
        """Generate test cases for wait action.

        Uses the same cropped images as training.
        """
        if ANNOTATION_CONFIG is None:
            return []

        wait_task = ANNOTATION_CONFIG.get_wait_task()
        if wait_task is None:
            return []

        wait_time = wait_task.wait_time if wait_task.wait_time > 0 else 3.0

        desktop_element = self._get_desktop_element()
        if desktop_element is None:
            return []

        # Generate state with loading visible
        num_desktop = ctx.rng.randint(3, 7)
        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=0,
            od_loading_visible=True,
        )

        # Render and crop to desktop
        full_image, metadata = self.renderer.render(state)
        cropped_img, image_path, bbox = self._crop_to_desktop(full_image, ctx)

        # Pick a random prompt for test
        prompt = ctx.rng.choice(WAIT_PROMPTS)

        expected_action = {
            "name": "computer_use",
            "arguments": {
                "action": "wait",
                "duration": wait_time,
            },
        }

        return [
            TestCase(
                test_id=f"test_{ctx.index:04d}_wait",
                screenshot=image_path,
                prompt=prompt,
                expected_action=expected_action,
                tolerance=(0, 0),
                metadata={
                    "task_type": wait_task.task_type,
                    "wait_seconds": wait_time,
                    "element_label": "desktop",
                    "crop_region": bbox,
                    "image_size": cropped_img.size,
                },
                pixel_coords=(0, 0),
            )
        ]

    def generate_test(self, ctx: TaskContext) -> TestCase:
        """Generate one test case."""
        tests = self.generate_tests(ctx)
        if not tests:
            raise ValueError("No wait tests generated")
        return tests[0]
