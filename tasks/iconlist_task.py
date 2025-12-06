# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""IconList task for desktop generator.

Uses CUDAG's IconListTaskBase to generate samples for tasks targeting
iconlist elements (desktop icons, taskbar icons).
"""

from random import Random
from typing import Any

from cudag.annotation.config import AnnotatedElement, AnnotationConfig
from cudag.core import IconListTaskBase

from screen import ANNOTATION_CONFIG, get_desktop_icons, get_taskbar_icons
from state import DesktopState


class IconListTask(IconListTaskBase):
    """Generate samples for iconlist tasks in desktop generator.

    Handles both desktop and taskbar iconlist elements based on
    what's defined in annotation.json.
    """

    task_type = "iconlist"

    def get_annotation_config(self) -> AnnotationConfig | None:
        """Return the desktop annotation config."""
        return ANNOTATION_CONFIG

    def get_icons_for_element(
        self, element: AnnotatedElement, state: Any
    ) -> tuple[list[Any], dict[str, dict[str, Any]]]:
        """Get icons based on element label (desktop or taskbar)."""
        if element.label == "desktop":
            return state.desktop_icons, get_desktop_icons()
        elif element.label == "taskbar":
            return state.taskbar_icons, get_taskbar_icons()
        return [], {}

    def generate_state(self, rng: Random, **kwargs: Any) -> DesktopState:
        """Generate desktop state with random icon counts."""
        num_desktop = rng.randint(3, 7)
        num_taskbar = rng.randint(1, 3)
        return DesktopState.generate(
            rng=rng,
            num_desktop_icons=num_desktop,
            num_taskbar_icons=num_taskbar,
            **kwargs,
        )
