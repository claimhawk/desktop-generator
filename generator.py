# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

"""Dataset generator for Windows 11 desktop screenshots.

Usage:
    python -m generator
    python -m generator --config config/dataset.yaml
"""

import argparse
from datetime import datetime
from pathlib import Path

from cudag.core import DatasetBuilder, DatasetConfig

from renderer import DesktopRenderer
from tasks import ClickDesktopIconTask, ClickTaskbarIconTask


def get_researcher_name() -> str | None:
    """Get researcher name from .researcher file if it exists."""
    researcher_file = Path(".researcher")
    if researcher_file.exists():
        content = researcher_file.read_text().strip()
        for line in content.split("\n"):
            if line.startswith("Name:"):
                return line.split(":", 1)[1].strip().lower()
    return None


def main() -> None:
    """Run dataset generation."""
    parser = argparse.ArgumentParser(description="Generate desktop dataset")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/dataset.yaml"),
        help="Path to dataset config YAML",
    )
    args = parser.parse_args()

    # Load config
    config = DatasetConfig.from_yaml(args.config)

    # Build dataset name: desktop-researcher-timestamp
    researcher = get_researcher_name()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if researcher:
        dataset_name = f"{config.name_prefix}-{researcher}-{timestamp}"
    else:
        dataset_name = f"{config.name_prefix}_{timestamp}"

    # Override output_dir with new naming
    config.output_dir = Path("datasets") / dataset_name

    print(f"Loaded config: {config.name_prefix}")
    print(f"Tasks: {config.task_counts}")

    # Initialize renderer
    renderer = DesktopRenderer(assets_dir=Path("assets"))
    renderer.load_assets()

    # Create tasks
    tasks = [
        ClickDesktopIconTask(config=config, renderer=renderer),
        ClickTaskbarIconTask(config=config, renderer=renderer),
    ]

    # Build dataset
    builder = DatasetBuilder(config=config, tasks=tasks)
    output_dir = builder.build()

    # Build evals
    builder.build_evals()

    print(f"\nDataset generated at: {output_dir}")


if __name__ == "__main__":
    main()
