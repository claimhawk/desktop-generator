# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Dataset generator for Windows 11 desktop screenshots.

Usage:
    ./scripts/generate.sh              # Full pipeline: generate + upload + preprocess
    ./scripts/generate.sh --dry        # Generate only, no upload

DO NOT run generator.py directly - use scripts/generate.sh instead!
"""

from pathlib import Path

from cudag import run_generator

from renderer import DesktopRenderer
from tasks import GroundingTask, IconListTask, WaitLoadingTask


def main() -> None:
    """Run dataset generation."""
    renderer = DesktopRenderer(assets_dir=Path("assets"))
    renderer.load_assets()

    # IconListTask generates samples for ALL icons per image (1:N)
    tasks = [
        IconListTask(config={}, renderer=renderer),
        WaitLoadingTask(config={}, renderer=renderer),
        GroundingTask(config={}, renderer=renderer),
    ]

    run_generator(
        renderer,
        tasks,
        description="Generate desktop dataset",
    )


if __name__ == "__main__":
    main()
