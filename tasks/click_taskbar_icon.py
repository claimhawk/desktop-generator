# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Task for clicking Open Dental taskbar icon."""

from cudag.core import BaseTask, EvalCase, TaskContext, TaskSample
from cudag.prompts.tools import ToolCall

from state import DesktopState


class ClickTaskbarIconTask(BaseTask):
    """Click Open Dental icon in the taskbar.

    Renders a desktop with randomized taskbar icons (always includes Open Dental)
    and generates a sample to click the OD taskbar icon.
    """

    task_type = "click-taskbar-icon"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate click sample for Open Dental taskbar icon."""
        # Generate random state - must include OD in taskbar
        state = DesktopState.generate(
            rng=ctx.rng,
            num_desktop_icons=ctx.rng.randint(3, 7),
            num_taskbar_icons=ctx.rng.randint(2, 3),
        )

        # Ensure Open Dental is in taskbar (re-generate if needed)
        while state.get_taskbar_icon_by_id("od") is None:
            state = DesktopState.generate(
                rng=ctx.rng,
                num_desktop_icons=ctx.rng.randint(3, 7),
                num_taskbar_icons=ctx.rng.randint(2, 3),
            )

        # Render once
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        # Find the Open Dental taskbar icon
        od_icon = state.get_taskbar_icon_by_id("od")
        if od_icon is None:
            raise ValueError("Open Dental icon not found in taskbar")

        # Build natural language prompt
        prompt = "Click on Open Dental in the taskbar."

        # Click center of icon
        click_x, click_y = od_icon.center

        sample = TaskSample(
            id=self.build_id(ctx, "_tb_od"),
            image_path=image_path,
            human_prompt=prompt,
            tool_call=ToolCall.left_click((click_x, click_y)),
            pixel_coords=(click_x, click_y),
            metadata={
                "task_type": self.task_type,
                "icon_id": "od",
                "icon_label": "Open Dental",
                "icon_bounds": od_icon.bounds,
                "ground_truth": state.to_ground_truth(),
            },
            image_size=image.size,
        )

        return [sample]

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate a single sample for Open Dental taskbar icon."""
        return self.generate_samples(ctx)[0]

    def generate_evals(self, ctx: TaskContext) -> list[EvalCase]:
        """Generate eval case for Open Dental taskbar icon."""
        samples = self.generate_samples(ctx)
        return [
            EvalCase(
                eval_id=f"eval_{ctx.index:04d}_taskbar_od",
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
