# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Example task - demonstrates 1-image-to-many-samples pattern.

Key insight: One rendered image can produce MULTIPLE training samples.
This is more efficient than generating a new image for each sample.
"""

from cudag.core import BaseTask, EvalCase, TaskContext, TaskSample
from cudag.prompts.tools import ToolCall

from state import TestDesktopGeneratorState


class ExampleTask(BaseTask):
    """Example task demonstrating 1:N image-to-samples pattern.

    One Screen can have many Tasks. Each Task:
    - Belongs to a Screen
    - Has a task_type identifier
    - Can generate multiple samples from one rendered image

    Example use cases:
    - Same claim window -> "click code" + "click fee" + "scroll"
    - Same calendar -> "click day 1" + "click day 15"
    """

    task_type = "example-click"

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate MULTIPLE samples from ONE rendered image."""
        # 1. Create state and render ONCE
        state = TestDesktopGeneratorState()
        image, metadata = self.renderer.render(state)
        image_path = self.save_image(image, ctx)

        samples = []

        # 2. Derive multiple samples from this one image
        # Sample 1: Click first target
        samples.append(TaskSample(
            id=self.build_id(ctx, "_target1"),
            image_path=image_path,
            human_prompt="Click the first item",
            tool_call=ToolCall.left_click((400, 300)),
            pixel_coords=(400, 300),
            metadata={"task_type": self.task_type, "target": "first"},
            image_size=image.size,
        ))

        # Sample 2: Click second target (SAME IMAGE)
        samples.append(TaskSample(
            id=self.build_id(ctx, "_target2"),
            image_path=image_path,
            human_prompt="Click the second item",
            tool_call=ToolCall.left_click((500, 400)),
            pixel_coords=(500, 400),
            metadata={"task_type": self.task_type, "target": "second"},
            image_size=image.size,
        ))

        return samples

    def generate_sample(self, ctx: TaskContext) -> TaskSample:
        """Generate one training sample (fallback)."""
        return self.generate_samples(ctx)[0]

    def generate_evals(self, ctx: TaskContext) -> list[EvalCase]:
        """Generate eval cases from ONE rendered image."""
        samples = self.generate_samples(ctx)
        return [
            EvalCase(
                eval_id=f"eval_{ctx.index:04d}_{i}",
                screenshot=s.image_path,
                prompt=s.human_prompt,
                expected_action=s.tool_call.to_dict(),
                tolerance=10,
                metadata=s.metadata,
                pixel_coords=s.pixel_coords,
            )
            for i, s in enumerate(samples)
        ]

    def generate_eval(self, ctx: TaskContext) -> EvalCase:
        """Generate one eval case (fallback)."""
        return self.generate_evals(ctx)[0]
