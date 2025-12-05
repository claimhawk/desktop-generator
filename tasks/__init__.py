# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Task definitions for desktop generator."""

from tasks.click_desktop_icon import ClickDesktopIconTask
from tasks.click_icon import ClickIconTask
from tasks.click_taskbar_icon import ClickTaskbarIconTask
from tasks.wait_loading import WaitLoadingTask

__all__ = [
    "ClickDesktopIconTask",
    "ClickTaskbarIconTask",
    "ClickIconTask",
    "WaitLoadingTask",
]
