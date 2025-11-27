# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Task for clicking Open Dental desktop icon."""

from cudag.core import BaseTask, EvalCase, TaskContext, TaskSample
from cudag.prompts.tools import ToolCall

from screen import DESKTOP_ICONS
from state import DesktopState


class ClickDesktopIconTask(BaseTask):
    """Click Open Dental icon on the desktop.

    Renders a desktop with randomized icons (always includes Open Dental)
    and generates a sample to click the OD icon.
    """

    task_type = "click-desktop-icon"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate click sample for Open Dental desktop icon."""
        # Generate random state with desktop icons (OD always included)
        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=ctx.rng.randint(3, 7),
            num_taskbar_icons=ctx.rng.randint(1, 3),
        )

        # Render once
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        # Find the Open Dental icon
        od_icon = state.get_desktop_icon_by_id("od")
        if od_icon is None:
            raise ValueError("Open Dental icon not found in state")

        icon_info = DESKTOP_ICONS.get("od", {})
        label = icon_info.get("label", "Open Dental")

        # Build natural language prompt
        prompt = f"Click on the {label} icon on the desktop."

        # Click center of icon
        click_x, click_y = od_icon.center

        sample = TaskSample(
            id=self.build_id(ctx, "_od"),
            image_path=image_path,
            human_prompt=prompt,
            tool_call=ToolCall.left_click((click_x, click_y)),
            pixel_coords=(click_x, click_y),
            metadata={
                "task_type": self.task_type,
                "icon_id": "od",
                "icon_label": label,
                "icon_bounds": od_icon.bounds,
                "ground_truth": state.to_ground_truth(),
            },
            image_size=image.size,
        )

        return [sample]

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate a single sample for Open Dental desktop icon."""
        return self.generate_samples(ctx)[0]

    def generate_evals(self, ctx: TaskContext) -> list[EvalCase]:
        """Generate eval case for Open Dental desktop icon."""
        samples = self.generate_samples(ctx)
        return [
            EvalCase(
                eval_id=f"eval_{ctx.index:04d}_desktop_od",
                screenshot=s.image_path,
                prompt=s.human_prompt,
                expected_action=s.tool_call.to_dict(),
                tolerance=10,
                metadata=s.metadata,
                pixel_coords=s.pixel_coords,
            )
            for s in samples
        ]

    def generate_eval(self, ctx: TaskContext) -> EvalCase:
        """Generate a single eval case."""
        return self.generate_evals(ctx)[0]
