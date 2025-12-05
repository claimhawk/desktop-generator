# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Combined task for clicking any icon on screen (desktop or taskbar).

Generates one screen and creates a click sample for EVERY icon present.
This is more efficient than generating separate screens for each icon.
"""

from cudag.core import BaseTask, TaskContext, TaskSample, TestCase
from cudag.prompts.tools import ToolCall

from screen import DESKTOP_ICONS, TASKBAR_ICONS
from state import DesktopState


class ClickIconTask(BaseTask):
    """Click any icon on the desktop or taskbar.

    For each generated screen, creates a sample for every icon present:
    - All desktop icons (3-7 icons)
    - All taskbar icons (1-3 icons)

    This generates 4-10 samples per screen, all sharing the same screenshot.
    """

    task_type = "click-icon"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate click samples for ALL icons on one screen."""
        # Generate random state with desktop and taskbar icons
        num_desktop = ctx.rng.randint(3, 7)
        num_taskbar = ctx.rng.randint(1, 3)

        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=num_taskbar,
        )

        # Render once - this image will be shared by all samples
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        samples: list[TaskSample] = []

        # Create a sample for each DESKTOP icon
        for icon in state.desktop_icons:
            icon_info = DESKTOP_ICONS.get(icon.icon_id, {})
            label = icon_info.get("label", icon.icon_id)

            prompt = f"Double-click on the {label} icon on the desktop."
            click_x, click_y = icon.center

            # Tolerance based on icon bounds (x, y, width, height)
            tol_x = icon.bounds[2] // 2
            tol_y = icon.bounds[3] // 2

            sample = TaskSample(
                id=self.build_id(ctx, f"_desktop_{icon.icon_id}"),
                image_path=image_path,
                human_prompt=prompt,
                tool_call=ToolCall.double_click((click_x, click_y)),
                pixel_coords=(click_x, click_y),
                metadata={
                    "task_type": "click-desktop-icon",
                    "icon_type": "desktop",
                    "icon_id": icon.icon_id,
                    "icon_label": label,
                    "icon_bounds": icon.bounds,
                    "ground_truth": state.to_ground_truth(),
                    "tolerance": [tol_x, tol_y],
                },
                image_size=image.size,
            )
            samples.append(sample)

        # Create a sample for each TASKBAR icon
        for icon in state.taskbar_icons:
            icon_info = TASKBAR_ICONS.get(icon.icon_id, {})
            label = icon_info.get("label", icon.icon_id)

            prompt = f"Double-click on {label} in the taskbar."
            click_x, click_y = icon.center

            # Tolerance based on icon bounds (x, y, width, height)
            tol_x = icon.bounds[2] // 2
            tol_y = icon.bounds[3] // 2

            sample = TaskSample(
                id=self.build_id(ctx, f"_taskbar_{icon.icon_id}"),
                image_path=image_path,
                human_prompt=prompt,
                tool_call=ToolCall.double_click((click_x, click_y)),
                pixel_coords=(click_x, click_y),
                metadata={
                    "task_type": "click-taskbar-icon",
                    "icon_type": "taskbar",
                    "icon_id": icon.icon_id,
                    "icon_label": label,
                    "icon_bounds": icon.bounds,
                    "ground_truth": state.to_ground_truth(),
                    "tolerance": [tol_x, tol_y],
                },
                image_size=image.size,
            )
            samples.append(sample)

        return samples

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate samples - returns first sample but typically use generate_samples."""
        return self.generate_samples(ctx)[0]

    def generate_tests(self, ctx: TaskContext) -> list[TestCase]:
        """Generate test cases for Open Dental icon clicks (desktop and taskbar)."""
        # Generate a fresh random state (independent of training)
        # Tests always have at least 3 icons in each area
        num_desktop = ctx.rng.randint(3, 7)
        num_taskbar = 3  # Always use all 3 taskbar icons for tests

        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=num_taskbar,
        )

        # Render and save - tests go to test/images/ directory automatically
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        tests: list[TestCase] = []

        # Test on Open Dental DESKTOP icon
        for icon in state.desktop_icons:
            if icon.icon_id == "od":
                icon_info = DESKTOP_ICONS.get(icon.icon_id, {})
                label = icon_info.get("label", icon.icon_id)
                prompt = f"Double-click on the {label} icon on the desktop."
                click_x, click_y = icon.center

                tests.append(
                    TestCase(
                        test_id=f"test_{ctx.index:04d}_desktop_{icon.icon_id}",
                        screenshot=image_path,
                        prompt=prompt,
                        expected_action=ToolCall.double_click((click_x, click_y)).to_dict(),
                        tolerance=(20, 20),  # Square icons: same x/y tolerance
                        metadata={
                            "task_type": "click-desktop-icon",
                            "icon_type": "desktop",
                            "icon_id": icon.icon_id,
                            "icon_label": label,
                            "icon_bounds": icon.bounds,
                            "image_size": image.size,
                        },
                        pixel_coords=(click_x, click_y),
                    )
                )
                break

        # Test on Open Dental TASKBAR icon
        for icon in state.taskbar_icons:
            if icon.icon_id == "od":
                icon_info = TASKBAR_ICONS.get(icon.icon_id, {})
                label = icon_info.get("label", "Open Dental")
                prompt = f"Double-click on {label} in the taskbar."
                click_x, click_y = icon.center

                tests.append(
                    TestCase(
                        test_id=f"test_{ctx.index:04d}_taskbar_{icon.icon_id}",
                        screenshot=image_path,
                        prompt=prompt,
                        expected_action=ToolCall.double_click((click_x, click_y)).to_dict(),
                        tolerance=(10, 10),  # Square icons: same x/y tolerance
                        metadata={
                            "task_type": "click-taskbar-icon",
                            "icon_type": "taskbar",
                            "icon_id": icon.icon_id,
                            "icon_label": label,
                            "icon_bounds": icon.bounds,
                            "image_size": image.size,
                        },
                        pixel_coords=(click_x, click_y),
                    )
                )
                break

        return tests

    def generate_test(self, ctx: TaskContext) -> TestCase:
        """Generate test - returns first but typically use generate_tests."""
        return self.generate_tests(ctx)[0]
