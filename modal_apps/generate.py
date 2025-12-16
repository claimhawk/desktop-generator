# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Run dataset generation directly on Modal with inline preprocessing.

Generates dataset and preprocesses it in a single step on Modal.
Output goes straight to /data/datasets/{name}/ on the volume.

Usage:
    # Run generation on Modal (production)
    modal run modal_apps/generate.py

    # Test mode (1% of data)
    modal run modal_apps/generate.py --test

    # With custom name
    modal run modal_apps/generate.py --name desktop--mike--test
"""
from __future__ import annotations

import modal

# =============================================================================
# Modal Configuration
# =============================================================================

VOLUME_NAME = "claimhawk-lora-training"
VOLUME_MOUNT = "/data"
DATASETS_PATH = "/data/datasets"

# Create Modal app and volume
app = modal.App("desktop-generate")
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

# Image with dependencies + local code baked in
# Using add_local_dir to include generator code and assets in the image
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "pillow>=10.0.0",
        "pyyaml>=6.0",
        "faker>=18.0.0",
        "torch==2.4.0",
        "torchvision==0.19.0",
        "transformers>=4.57.0",
        "qwen-vl-utils",
        "numpy>=1.24.0",
        "tqdm>=4.65.0",
    )
    # Add generator code
    .add_local_dir(
        ".",
        remote_path="/app",
        ignore=[
            "__pycache__",
            "*.pyc",
            ".venv",
            ".git",
            "datasets/",
            "modal_apps/",
        ],
    )
    # Add CUDAG source
    .add_local_dir(
        "../cudag/src/cudag",
        remote_path="/app/cudag",
        ignore=["__pycache__", "*.pyc"],
    )
)


@app.function(
    image=image,
    volumes={VOLUME_MOUNT: volume},
    timeout=3600 * 4,  # 4 hours for large datasets
    cpu=4.0,
    memory=16384,  # 16GB
    retries=modal.Retries(
        max_retries=3,
        backoff_coefficient=1.0,
        initial_delay=1.0,
    ),
)
def generate_dataset(
    dataset_name: str | None = None,
    test_mode: bool = False,
    researcher: str = "modal",
) -> str:
    """Generate dataset and write directly to Modal volume.

    Handles preemption via checkpointing:
    - Progress saved to volume every 1000 samples
    - On restart, resumes from last checkpoint
    - Retries up to 3 times on preemption

    Args:
        dataset_name: Optional custom name (auto-generated if None)
        test_mode: If True, generate 1% test dataset
        researcher: Researcher name for dataset naming

    Returns:
        Dataset name that was generated
    """
    import json
    import os
    import sys
    from datetime import datetime
    from pathlib import Path

    # Setup Python path
    sys.path.insert(0, "/app")
    os.chdir("/app")

    print("=" * 70)
    print("MODAL DATASET GENERATION")
    print("=" * 70)
    print()

    # Import after path setup
    from renderer import DesktopRenderer
    from state import DesktopState
    from cudag.core.dataset import DatasetConfig, DatasetBuilder
    from tasks import IconListTask, WaitLoadingTask, GroundingTask

    # Build dataset name
    if dataset_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_name = f"desktop--{researcher}--{timestamp}"

    print(f"Dataset name: {dataset_name}")
    print(f"Test mode:    {test_mode}")
    print()

    # Set output directly to volume
    output_dir = Path(f"{DATASETS_PATH}/{dataset_name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = output_dir / ".checkpoint.json"

    # Check for existing checkpoint (resume after preemption)
    checkpoint = None
    if checkpoint_file.exists():
        try:
            checkpoint = json.loads(checkpoint_file.read_text())
            print(f"RESUMING from checkpoint: {checkpoint['samples_generated']} samples done")
            print()
        except Exception as e:
            print(f"Warning: Could not load checkpoint: {e}")
            checkpoint = None

    # Load config
    config_path = Path("/app/config/dataset.yaml")
    config = DatasetConfig.from_yaml(config_path)
    config.output_dir = output_dir

    # Apply test mode scaling if requested
    if test_mode:
        # Scale task counts to 1% for testing
        for task_type in config.task_counts:
            config.task_counts[task_type] = max(1, int(config.task_counts[task_type] * 0.01))

    print(f"Output dir:   {output_dir}")
    print()

    # If resuming, adjust start index
    start_index = 0
    if checkpoint:
        start_index = checkpoint.get("samples_generated", 0)
        print(f"Resuming from sample {start_index}")

    print()
    print("Task counts:")
    for task_type, count in sorted(config.task_counts.items()):
        print(f"  {task_type}: {count:,}")
    total = sum(config.task_counts.values())
    print(f"  TOTAL: {total:,}")
    print()

    # Initialize renderer
    assets_dir = Path("/app/assets")
    print(f"Assets dir:   {assets_dir}")
    renderer = DesktopRenderer(assets_dir=assets_dir)
    renderer.load_assets()
    print("Assets loaded successfully")
    print()

    # Build task list
    tasks = []

    # IconList task
    tasks.append(IconListTask(config={}, renderer=renderer))

    # WaitLoading task
    tasks.append(WaitLoadingTask(config={}, renderer=renderer))

    # Grounding task
    tasks.append(GroundingTask(config={}, renderer=renderer))

    print(f"Registered {len(tasks)} tasks")
    print()
    print("=" * 70)
    print("STARTING GENERATION")
    print("=" * 70)
    print()

    # Build dataset with checkpointing
    builder = DatasetBuilder(config=config, tasks=tasks)

    # Custom build with checkpointing every 1000 samples
    def checkpoint_callback(samples_done: int) -> None:
        """Save checkpoint and commit volume."""
        checkpoint_data = {
            "dataset_name": dataset_name,
            "samples_generated": samples_done,
            "timestamp": datetime.now().isoformat(),
        }
        checkpoint_file.write_text(json.dumps(checkpoint_data))
        volume.commit()
        print(f"  [Checkpoint saved: {samples_done} samples]")

    result_dir = builder.build(
        start_index=start_index,
        checkpoint_callback=checkpoint_callback,
        checkpoint_interval=1000,
    )

    print()
    print("=" * 70)
    print("BUILDING TEST CASES")
    print("=" * 70)
    print()

    # Build tests
    builder.build_tests()

    # Remove checkpoint file (generation complete)
    if checkpoint_file.exists():
        checkpoint_file.unlink()

    # Commit volume changes after generation
    volume.commit()

    print()
    print("=" * 70)
    print("PREPROCESSING DATASET")
    print("=" * 70)
    print()

    # Import preprocessing dependencies
    import torch
    from tqdm import tqdm
    from transformers import Qwen2_5_VLProcessor

    # Load processor
    print("Loading Qwen2_5_VLProcessor...")
    processor = Qwen2_5_VLProcessor.from_pretrained(
        "Qwen/Qwen2.5-VL-3B-Instruct",
        min_pixels=256 * 28 * 28,
        max_pixels=1280 * 28 * 28,
    )
    print("Processor loaded")
    print()

    # Read training samples
    train_file = output_dir / "train.jsonl"
    print(f"Reading {train_file}...")
    samples = []
    with train_file.open("r") as f:
        for line in f:
            samples.append(json.loads(line))
    print(f"Loaded {len(samples)} samples")
    print()

    # Create preprocessed directory
    preprocessed_path = output_dir / "preprocessed"
    preprocessed_path.mkdir(exist_ok=True)

    # Process each sample
    print("Processing samples...")
    metadata = []
    for i, sample in enumerate(tqdm(samples)):
        # Build messages for processor
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": str(output_dir / sample["image"])},
                    {"type": "text", "text": sample["conversations"][0]["value"]},
                ],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": sample["conversations"][1]["value"]}],
            },
        ]

        # Apply chat template
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )

        # Process with processor
        from qwen_vl_utils import process_vision_info

        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        # Save preprocessed tensors
        output_file = preprocessed_path / f"sample_{i:06d}.pt"
        torch.save(inputs, output_file)

        # Store metadata
        metadata.append(
            {
                "sample_id": i,
                "original_image": sample["image"],
                "preprocessed_file": f"preprocessed/sample_{i:06d}.pt",
                "task_type": sample.get("metadata", {}).get("task_type", "unknown"),
            }
        )

    # Save metadata
    metadata_file = preprocessed_path / "metadata.json"
    with metadata_file.open("w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved {len(metadata)} preprocessed samples to {preprocessed_path}")
    print()

    # Commit final volume changes
    volume.commit()

    print()
    print("=" * 70)
    print("GENERATION + PREPROCESSING COMPLETE")
    print("=" * 70)
    print()
    print(f"Dataset:      {dataset_name}")
    print(f"Location:     {DATASETS_PATH}/{dataset_name}/")
    print(f"Preprocessed: {DATASETS_PATH}/{dataset_name}/preprocessed/")
    print()

    return dataset_name


@app.local_entrypoint()
def main(
    name: str | None = None,
    test: bool = False,
    researcher: str = "modal",
):
    """Local entrypoint for Modal CLI.

    Args:
        name: Optional dataset name (auto-generated if not provided)
        test: Generate 1% test dataset
        researcher: Researcher name for dataset naming
    """
    print("Launching Modal generation...")
    print()

    dataset_name = generate_dataset.remote(
        dataset_name=name,
        test_mode=test,
        researcher=researcher,
    )

    print()
    print("=" * 70)
    print(f"SUCCESS: {dataset_name}")
    print("=" * 70)
    print()
    print("Dataset ready for training!")
