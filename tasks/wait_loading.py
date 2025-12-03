# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Wait task for when OD Loading panel is visible.

Generates training samples for the "wait" action when the model
sees a loading screen/splash screen.
"""

from cudag.core import BaseTask, TaskContext, TaskSample, TestCase
from cudag.prompts.tools import ToolCall

from state import DesktopState


class WaitLoadingTask(BaseTask):
    """Wait when OD Loading panel is visible.

    Generates samples where the model should wait N seconds
    because a loading/splash screen is visible.
    """

    task_type = "wait-loading"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate wait samples with OD loading panel visible."""
        # Generate random state with OD loading visible
        num_desktop = ctx.rng.randint(3, 7)
        num_taskbar = ctx.rng.randint(1, 3)

        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=num_taskbar,
            od_loading_visible=True,
        )

        # Render once - shows desktop with loading panel overlay
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        # Random wait time between 1-5 seconds
        wait_seconds = ctx.rng.randint(1, 5)

        # Create the wait sample
        sample = TaskSample(
            id=self.build_id(ctx, "_wait"),
            image_path=image_path,
            human_prompt=f"Wait for {wait_seconds} seconds.",
            tool_call=ToolCall.wait(wait_seconds),
            pixel_coords=(0, 0),  # No specific coords for wait action
            metadata={
                "task_type": "wait-loading",
                "wait_seconds": wait_seconds,
                "loading_panel": "od-loading",
                "ground_truth": state.to_ground_truth(),
                "tolerance": [0, 0],
            },
            image_size=image.size,
        )

        return [sample]

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate one wait sample."""
        return self.generate_samples(ctx)[0]

    def generate_tests(self, ctx: TaskContext) -> list[TestCase]:
        """Generate test cases for wait action when loading panel visible."""
        num_desktop = ctx.rng.randint(3, 7)
        num_taskbar = 3

        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=num_taskbar,
            od_loading_visible=True,
        )

        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        # For tests, use a fixed wait time
        wait_seconds = 3

        test = TestCase(
            test_id=f"test_{ctx.index:04d}_wait",
            screenshot=image_path,
            prompt=f"Wait for {wait_seconds} seconds.",
            expected_action=ToolCall.wait(wait_seconds).to_dict(),
            tolerance=(0, 0),  # No coordinate tolerance for wait
            metadata={
                "task_type": "wait-loading",
                "wait_seconds": wait_seconds,
                "loading_panel": "od-loading",
                "image_size": image.size,
            },
            pixel_coords=(0, 0),
        )

        return [test]

    def generate_test(self, ctx: TaskContext) -> TestCase:
        """Generate one test case."""
        return self.generate_tests(ctx)[0]
