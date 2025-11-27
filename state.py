# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""State definition for test_desktop_generator."""

from dataclasses import dataclass
from cudag.core import BaseState


@dataclass
class TestDesktopGeneratorState(BaseState):
    """Dynamic data that populates the screen.

    Add fields for all the data needed to render your screen.
    """

    # Example fields - replace with your own:
    # selected_item: int = 0
    # items: list[str] = field(default_factory=list)

    pass  # Remove this when you add fields
