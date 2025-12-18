# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""IconList task for desktop generator.

Uses CUDAG's IconListTaskBase to generate samples for tasks targeting
desktop iconlist elements only.

Images are cropped to the desktop bbox (0, 0, 1914, 1032) to exclude the taskbar.
"""

from random import Random
from typing import Any

from PIL import Image

from cudag.annotation.config import AnnotatedElement, AnnotationConfig
from cudag.core import IconListTaskBase, TaskContext, TaskSample, TestCase
from cudag.core.iconlist_task import make_tool_call

from screen import ANNOTATION_CONFIG, get_desktop_icons
from state import DesktopState


class IconListTask(IconListTaskBase):
    """Generate samples for desktop icon tasks.

    Images are cropped to the desktop bbox region (1914x1032) to exclude
    the taskbar. Both training and test use the same cropped images.
    """

    task_type = "iconlist"

    def get_annotation_config(self) -> AnnotationConfig | None:
        """Return the desktop annotation config."""
        return ANNOTATION_CONFIG

    def get_icons_for_element(
        self, element: AnnotatedElement, state: Any
    ) -> tuple[list[Any], dict[str, dict[str, Any]]]:
        """Get icons for desktop element only."""
        if element.label == "desktop":
            return state.desktop_icons, get_desktop_icons()
        return [], {}

    def generate_state(self, rng: Random, **kwargs: Any) -> DesktopState:
        """Generate desktop state with random icon counts."""
        num_desktop = rng.randint(3, 7)
        return DesktopState.generate(
            rng=rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=0,
            **kwargs,
        )

    def _get_desktop_element(self) -> AnnotatedElement | None:
        """Get the desktop element from annotation config."""
        config = self.get_annotation_config()
        if config is None:
            return None
        return config.get_element_by_label("desktop")

    def _crop_to_desktop(
        self, full_image: Image.Image, ctx: TaskContext
    ) -> tuple[Image.Image, str, tuple[int, int, int, int]]:
        """Crop full image to desktop bbox and save.

        Returns:
            Tuple of (cropped_image, image_path, bbox)
        """
        element = self._get_desktop_element()
        if element is None:
            raise ValueError("Desktop element not found in annotation")

        bbox = element.bbox  # (x, y, width, height)
        crop_box = (bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3])
        cropped = full_image.crop(crop_box)
        path = self.save_image(cropped, ctx, prefix="desktop")
        return cropped, path, bbox

    def generate_samples(self, ctx: TaskContext) -> list[TaskSample]:
        """Generate samples with desktop-only cropping.

        Crops images to the desktop bbox to exclude the taskbar.
        Coordinates are relative to the cropped region.
        """
        config = self.get_annotation_config()
        if config is None:
            return []

        desktop_element = self._get_desktop_element()
        if desktop_element is None:
            return []

        state = self.generate_state(ctx.rng)
        full_image, metadata = self.renderer.render(state)

        # Crop to desktop region
        cropped_img, image_path, bbox = self._crop_to_desktop(full_image, ctx)
        crop_x, crop_y = bbox[0], bbox[1]

        samples: list[TaskSample] = []
        icons_in_state = state.desktop_icons
        icons_info = get_desktop_icons()
        tolerance = (desktop_element.tolerance_x, desktop_element.tolerance_y)

        for task in config.tasks:
            if task.action in ("wait", "grounding"):
                continue

            element = config.get_element(task.target_element_id)
            if element is None or element.label != "desktop":
                continue

            for icon in icons_in_state:
                icon_info = icons_info.get(icon.icon_id, {})
                label = icon_info.get("label", icon.icon_id)
                prompt = task.prompt_template.replace("[icon_label]", label)

                # Coordinates relative to crop region
                abs_x, abs_y = icon.center
                rel_x = abs_x - crop_x
                rel_y = abs_y - crop_y

                tool_call = make_tool_call(task.action, (rel_x, rel_y))

                ground_truth = {
                    "icons": [
                        {
                            "id": i.icon_id,
                            "label": icons_info.get(i.icon_id, {}).get("label", i.icon_id),
                            "center": (i.center[0] - crop_x, i.center[1] - crop_y),
                        }
                        for i in icons_in_state
                    ],
                }

                samples.append(
                    TaskSample(
                        id=self.build_id(ctx, f"_desktop_{icon.icon_id}"),
                        image_path=image_path,
                        human_prompt=prompt,
                        tool_call=tool_call,
                        pixel_coords=(rel_x, rel_y),
                        metadata={
                            "task_type": task.task_type,
                            "element_type": desktop_element.element_type,
                            "element_label": "desktop",
                            "icon_id": icon.icon_id,
                            "icon_label": label,
                            "icon_bounds": icon.bounds,
                            "crop_region": bbox,
                            "ground_truth": ground_truth,
                            "tolerance": list(tolerance),
                        },
                        image_size=cropped_img.size,
                    )
                )

        return samples

    def generate_tests(self, ctx: TaskContext) -> list[TestCase]:
        """Generate test cases with desktop-only cropping.

        Uses the same cropping as training to ensure consistency.
        Only tests required icons.
        """
        config = self.get_annotation_config()
        if config is None:
            return []

        desktop_element = self._get_desktop_element()
        if desktop_element is None:
            return []

        state = self.generate_state(ctx.rng)
        full_image, metadata = self.renderer.render(state)

        # Crop to desktop region (same as training)
        cropped_img, image_path, bbox = self._crop_to_desktop(full_image, ctx)
        crop_x, crop_y = bbox[0], bbox[1]

        tests: list[TestCase] = []
        icons_in_state = state.desktop_icons
        icons_info = get_desktop_icons()
        tolerance = (desktop_element.tolerance_x, desktop_element.tolerance_y)

        for task in config.tasks:
            if task.action in ("wait", "grounding"):
                continue

            element = config.get_element(task.target_element_id)
            if element is None or element.label != "desktop":
                continue

            for icon in icons_in_state:
                icon_info = icons_info.get(icon.icon_id, {})
                if not icon_info.get("required", False):
                    continue

                label = icon_info.get("label", icon.icon_id)
                prompt = task.prompt_template.replace("[icon_label]", label)

                # Coordinates relative to crop region
                abs_x, abs_y = icon.center
                rel_x = abs_x - crop_x
                rel_y = abs_y - crop_y

                tool_call = make_tool_call(task.action, (rel_x, rel_y))

                tests.append(
                    TestCase(
                        test_id=f"test_{ctx.index:04d}_desktop_{icon.icon_id}",
                        screenshot=image_path,
                        prompt=prompt,
                        expected_action=tool_call.to_dict(),
                        tolerance=tolerance,
                        metadata={
                            "task_type": task.task_type,
                            "element_type": desktop_element.element_type,
                            "element_label": "desktop",
                            "icon_id": icon.icon_id,
                            "icon_label": label,
                            "icon_bounds": icon.bounds,
                            "crop_region": bbox,
                            "image_size": cropped_img.size,
                        },
                        pixel_coords=(rel_x, rel_y),
                    )
                )

        return tests
