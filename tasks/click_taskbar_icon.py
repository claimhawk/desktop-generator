# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Task for clicking taskbar icons.

Generates one screen, then creates click tasks for ALL taskbar icons on it.
"""

from cudag.core import BaseTask, TaskContext, TaskSample, TestCase
from cudag.prompts.tools import ToolCall

from screen import TASKBAR_ICONS
from state import DesktopState


class ClickTaskbarIconTask(BaseTask):
    """Click any taskbar icon.

    Renders a desktop with randomized icons and generates click samples
    for ALL visible taskbar icons (1:N image-to-samples pattern).
    """

    task_type = "click-taskbar-icon"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate click samples for ALL taskbar icons on one screen."""
        # Generate random state with taskbar icons
        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=ctx.rng.randint(3, 7),
            num_taskbar_icons=ctx.rng.randint(2, 3),
        )

        # Render once - this image is shared by all samples
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        samples: list[TaskSample] = []

        # Create a sample for EACH taskbar icon
        for icon in state.taskbar_icons:
            icon_info = TASKBAR_ICONS.get(icon.icon_id, {})
            label = icon_info.get("label", icon.icon_id)

            prompt = f"Double-click on {label} in the taskbar."
            click_x, click_y = icon.center

            # Tolerance based on icon bounds (x, y, width, height)
            tol_x = icon.bounds[2] // 2
            tol_y = icon.bounds[3] // 2

            samples.append(
                TaskSample(
                    id=self.build_id(ctx, f"_tb_{icon.icon_id}"),
                    image_path=image_path,
                    human_prompt=prompt,
                    tool_call=ToolCall.double_click((click_x, click_y)),
                    pixel_coords=(click_x, click_y),
                    metadata={
                        "task_type": self.task_type,
                        "icon_id": icon.icon_id,
                        "icon_label": label,
                        "icon_bounds": icon.bounds,
                        "ground_truth": state.to_ground_truth(),
                        "tolerance": [tol_x, tol_y],
                    },
                    image_size=image.size,
                )
            )

        return samples

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate samples - returns first but typically use generate_samples."""
        return self.generate_samples(ctx)[0]

    def generate_tests(self, ctx: TaskContext) -> list[TestCase]:
        """Generate test cases for ALL taskbar icons on one screen."""
        samples = self.generate_samples(ctx)
        return [
            TestCase(
                test_id=f"test_{ctx.index:04d}_taskbar_{s.metadata['icon_id']}",
                screenshot=s.image_path,
                prompt=s.human_prompt,
                expected_action=s.tool_call.to_dict(),
                tolerance=10,
                metadata=s.metadata,
                pixel_coords=s.pixel_coords,
            )
            for s in samples
        ]

    def generate_test(self, ctx: TaskContext) -> TestCase:
        """Generate a single test case."""
        return self.generate_tests(ctx)[0]
