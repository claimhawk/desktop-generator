# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Wait task for when loading panel is visible - driven by annotation.json.

When loading is visible, uses click task prompts but expects wait action.
All config comes from annotation: prompt templates, wait time, task types.
"""

from cudag.core import BaseTask, TaskContext, TaskSample, TestCase
from cudag.prompts.tools import ToolCall

from screen import ANNOTATION_CONFIG, get_desktop_icons, get_taskbar_icons
from state import DesktopState


class WaitLoadingTask(BaseTask):
    """Wait when loading panel is visible.

    Uses click prompts from annotation but expects wait action.
    Teaches the model: when loading indicator visible → wait, don't click.
    """

    task_type = "wait-loading"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate wait samples with loading panel visible."""
        if ANNOTATION_CONFIG is None:
            return []

        # Get wait task from annotation
        wait_task = ANNOTATION_CONFIG.get_wait_task()
        if wait_task is None:
            return []

        wait_time = wait_task.wait_time if wait_task.wait_time > 0 else 3.0

        # Generate state with loading visible
        num_desktop = ctx.rng.randint(3, 7)
        num_taskbar = ctx.rng.randint(1, 3)

        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=num_taskbar,
            od_loading_visible=True,
        )

        # Render once
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        samples: list[TaskSample] = []

        desktop_icons = get_desktop_icons()
        taskbar_icons = get_taskbar_icons()

        # Iterate over click tasks from annotation - use their prompts but wait action
        for task in ANNOTATION_CONFIG.tasks:
            if task.action == "wait":
                continue  # Skip the wait task itself

            element = ANNOTATION_CONFIG.get_element(task.target_element_id)
            if element is None:
                continue

            # Only handle iconlist elements for wait samples
            if element.element_type != "iconlist":
                continue

            if element.label == "desktop":
                icons_in_state = state.desktop_icons
                icons_info = desktop_icons
            elif element.label == "taskbar":
                icons_in_state = state.taskbar_icons
                icons_info = taskbar_icons
            else:
                continue

            # Generate wait samples using click prompts
            for icon in icons_in_state:
                icon_info = icons_info.get(icon.icon_id, {})
                label = icon_info.get("label", icon.icon_id)

                # Use click prompt but expect wait action
                prompt = task.prompt_template.replace("[icon_label]", label)

                samples.append(
                    TaskSample(
                        id=self.build_id(ctx, f"_wait_{element.label}_{icon.icon_id}"),
                        image_path=image_path,
                        human_prompt=prompt,
                        tool_call=ToolCall.wait(wait_time),
                        pixel_coords=(0, 0),
                        metadata={
                            "task_type": wait_task.task_type,
                            "wait_seconds": wait_time,
                            "original_task_type": task.task_type,
                            "element_type": element.element_type,
                            "element_label": element.label,
                            "icon_id": icon.icon_id,
                            "icon_label": label,
                            "ground_truth": state.to_ground_truth(),
                            "tolerance": [0, 0],
                        },
                        image_size=image.size,
                    )
                )

        return samples

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate one wait sample."""
        return self.generate_samples(ctx)[0]

    def generate_tests(self, ctx: TaskContext) -> list[TestCase]:
        """Generate test cases for wait action."""
        samples = self.generate_samples(ctx)
        return [
            TestCase(
                test_id=f"test_{ctx.index:04d}_wait_{s.metadata['icon_id']}",
                screenshot=s.image_path,
                prompt=s.human_prompt,
                expected_action=s.tool_call.to_dict(),
                tolerance=(0, 0),
                metadata=s.metadata,
                pixel_coords=(0, 0),
            )
            for s in samples
        ]

    def generate_test(self, ctx: TaskContext) -> TestCase:
        """Generate one test case."""
        return self.generate_tests(ctx)[0]
