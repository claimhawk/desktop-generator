# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Dataset generator for Windows 11 desktop screenshots.

Usage:
    ./scripts/generate.sh              # Full pipeline: generate + upload + preprocess
    ./scripts/generate.sh --dry        # Generate only, no upload

DO NOT run generator.py directly - use scripts/generate.sh instead!
"""

from pathlib import Path

from cudag import run_generator

from renderer import DesktopRenderer
from tasks import ClickIconTask, WaitLoadingTask


def main() -> None:
    """Run dataset generation."""
    renderer = DesktopRenderer(assets_dir=Path("assets"))
    renderer.load_assets()

    # ClickIconTask generates samples for ALL icons per image (1:N)
    tasks = [
        ClickIconTask(config={}, renderer=renderer),
        WaitLoadingTask(config={}, renderer=renderer),
    ]

    run_generator(
        renderer,
        tasks,
        description="Generate desktop dataset",
    )


if __name__ == "__main__":
    main()
