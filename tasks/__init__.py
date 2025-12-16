# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Task definitions for desktop generator.

Tasks are driven by annotation.json:
- IconListTask: generates samples for tasks targeting iconlist elements
- WaitLoadingTask: generates wait samples when loading element is visible
- GroundingTask: generates grounding samples for element bounding box detection
"""

from tasks.grounding_task import GroundingTask
from tasks.iconlist_task import IconListTask
from tasks.wait_loading import WaitLoadingTask

__all__ = [
    "GroundingTask",
    "IconListTask",
    "WaitLoadingTask",
]
