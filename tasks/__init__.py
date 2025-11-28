# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Task definitions for desktop generator."""

from tasks.click_desktop_icon import ClickDesktopIconTask
from tasks.click_taskbar_icon import ClickTaskbarIconTask
from tasks.wait_loading import WaitLoadingTask

__all__ = ["ClickDesktopIconTask", "ClickTaskbarIconTask", "WaitLoadingTask"]
