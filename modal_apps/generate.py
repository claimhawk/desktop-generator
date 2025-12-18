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
        "../../cudag/src/cudag",
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
    from transformers import AutoProcessor
    from qwen_vl_utils import process_vision_info

    # System prompt (must match CUDAG/trainer)
    SYSTEM_PROMPT = """# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{
\t"type": "function",
\t"function": {
\t\t"name_for_human": "computer_use",
\t\t"name": "computer_use",
\t\t"description": "Perform computer actions",
\t\t"parameters": {
\t\t\t"properties": {
\t\t\t\t"action": {
\t\t\t\t\t"description": "* `key`: Press keys in order, release in reverse.\\n* `type`: Type a string of text.\\n* `mouse_move`: Move the cursor to (x, y).\\n* `left_click`: Left click at (x, y).\\n* `left_click_drag`: Click and drag from current to (x, y).\\n* `right_click`: Right click at (x, y).\\n* `middle_click`: Middle click at (x, y).\\n* `double_click`: Double-click at (x, y).\\n* `triple_click`: Triple-click at (x, y) (simulated as double-click).\\n* `scroll`: Scroll the mouse wheel.\\n* `hscroll`: Horizontal scroll.\\n* `wait`: Wait N seconds.\\n* `terminate`: End the task with a status.\\n* `answer`: Answer a question.",
\t\t\t\t\t"enum": ["key", "type", "mouse_move", "left_click", "left_click_drag", "right_click", "middle_click", "double_click", "scroll", "wait", "terminate"],
\t\t\t\t\t"type": "string"
\t\t\t\t},
\t\t\t\t"keys": {"description": "Required only by `action=key`.", "type": "array"},
\t\t\t\t"text": {"description": "Required only by `action=type`.", "type": "string"},
\t\t\t\t"coordinate": {"description": "Mouse coordinates (1000x1000 normalized).", "type": "array"},
\t\t\t\t"pixels": {"description": "The amount of scrolling.", "type": "number"},
\t\t\t\t"time": {"description": "The seconds to wait.", "type": "number"},
\t\t\t\t"status": {"description": "The status of the task.", "type": "string", "enum": ["success", "failure"]}
\t\t\t},
\t\t\t"required": ["action"],
\t\t\t"type": "object"
\t\t},
\t\t"args_format": "Format the arguments as a JSON object."
\t}
}
</tools>

For each function call, return a json object with function name and arguments within
<tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>

# Response format

Response format for every step:
1) Action: a short imperative describing what to do in the UI.
2) One or more <tool_call>...</tool_call> blocks, one per line, each containing only the JSON:
\t{"name": <function-name>, "arguments": <args-json-object>}.

Rules:
- Output exactly in the order: Action, <tool_call>(s).
- Be brief: one sentence for Action.
- Multiple tool calls can be output, one per line.
- Do not output anything else outside those parts.
- If finishing, use action=terminate in the tool call."""

    # Load processor - must match trainer (Qwen3-VL-8B-Instruct)
    print("Loading Qwen3-VL-8B processor...")
    processor = AutoProcessor.from_pretrained(
        "Qwen/Qwen3-VL-8B-Instruct",
        trust_remote_code=True,
    )
    print("Processor loaded")
    print()

    # Create preprocessed directory structure
    preprocessed_path = output_dir / "preprocessed"
    preprocessed_path.mkdir(exist_ok=True)
    train_preprocessed = preprocessed_path / "train"
    train_preprocessed.mkdir(exist_ok=True)
    val_preprocessed = preprocessed_path / "val"
    val_preprocessed.mkdir(exist_ok=True)

    def preprocess_split(
        split_file: Path, output_subdir: Path, split_name: str
    ) -> list[dict]:
        """Preprocess a single split (train or val)."""
        if not split_file.exists():
            print(f"Warning: {split_file} not found, skipping {split_name}")
            return []

        print(f"Reading {split_file}...")
        samples = []
        with split_file.open("r") as f:
            for line in f:
                samples.append(json.loads(line))
        print(f"Loaded {len(samples)} {split_name} samples")

        print(f"Processing {split_name} samples...")
        split_metadata = []
        for i, sample in enumerate(tqdm(samples, desc=split_name)):
            img_path = str(output_dir / sample["image"])
            human_value = sample["conversations"][0]["value"]
            gpt_value = sample["conversations"][1]["value"]

            # Strip <image> prefix from human value for text
            human_text = human_value.replace("<image>", "").strip()

            # Step 1: Pre-process image separately (must match CUDAG)
            image_message = [{"role": "user", "content": [{"type": "image", "image": f"file://{img_path}"}]}]
            image_inputs, _ = process_vision_info(image_message, image_patch_size=16)
            pixel_values = image_inputs[0] if image_inputs else None

            # Step 2: Build text template (no image path, just placeholder)
            messages = [
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": human_text},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": gpt_value}],
                },
            ]

            # Step 3: Apply chat template
            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )

            # Step 4: Process with pre-processed pixel values
            model_inputs = processor(
                text=[text],
                images=[pixel_values] if pixel_values is not None else None,
                videos=None,
                padding=False,
                return_tensors="pt",
                do_resize=False,
            )

            # Extract tensors
            input_ids = (
                model_inputs["input_ids"][0]
                if isinstance(model_inputs["input_ids"][0], torch.Tensor)
                else torch.tensor(model_inputs["input_ids"][0])
            )
            attention_mask = (
                model_inputs["attention_mask"][0]
                if isinstance(model_inputs["attention_mask"][0], torch.Tensor)
                else torch.tensor(model_inputs["attention_mask"][0])
            )

            # Create labels: Only train on assistant responses
            IGNORE_INDEX = -100
            labels = torch.full_like(input_ids, IGNORE_INDEX)

            # Find assistant response tokens
            input_ids_list = input_ids.tolist()
            seq_len = len(input_ids_list)
            pos = 0

            while pos < seq_len:
                # <|im_start|>assistant (token ID 77091)
                if input_ids_list[pos] == 77091:
                    ans_start = pos + 2
                    ans_end = ans_start
                    # Find <|im_end|> (token ID 151645)
                    while ans_end < seq_len and input_ids_list[ans_end] != 151645:
                        ans_end += 1
                    if ans_end < seq_len:
                        labels[ans_start : ans_end + 2] = input_ids[ans_start : ans_end + 2]
                        pos = ans_end
                pos += 1

            # Build result
            result = {
                "input_ids": input_ids.cpu(),
                "attention_mask": attention_mask.cpu(),
                "labels": labels.cpu(),
            }
            if "pixel_values" in model_inputs:
                result["pixel_values"] = model_inputs["pixel_values"].cpu()
                result["image_grid_thw"] = model_inputs["image_grid_thw"].cpu()

            # Save preprocessed tensors
            output_file = output_subdir / f"sample_{i:06d}.pt"
            torch.save(result, output_file)

            # Store metadata
            split_metadata.append(
                {
                    "sample_id": i,
                    "original_image": sample["image"],
                    "preprocessed_file": f"preprocessed/{split_name}/sample_{i:06d}.pt",
                    "task_type": sample.get("metadata", {}).get("task_type", "unknown"),
                }
            )

        return split_metadata

    # Process train and val splits
    train_metadata = preprocess_split(
        output_dir / "train.jsonl", train_preprocessed, "train"
    )
    val_metadata = preprocess_split(
        output_dir / "val.jsonl", val_preprocessed, "val"
    )

    # Save metadata with sample counts
    metadata = {
        "train_samples": len(train_metadata),
        "val_samples": len(val_metadata),
        "total_samples": len(train_metadata) + len(val_metadata),
        "train": train_metadata,
        "val": val_metadata,
    }
    metadata_file = preprocessed_path / "metadata.json"
    with metadata_file.open("w") as f:
        json.dump(metadata, f, indent=2)

    print()
    print(f"Preprocessed {len(train_metadata)} train + {len(val_metadata)} val samples")
    print(f"Saved to {preprocessed_path}")
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
