#!/usr/bin/env bash
# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Derivative works may be released by researchers,
# but original files may not be redistributed or used beyond research purposes.

# Pipeline: generate.sh -> upload.sh -> preprocess.sh
#
# Usage:
#   ./scripts/preprocess.sh --dataset-name <NAME>

set -euo pipefail

DATASET_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dataset-name)
            DATASET_NAME="${2:-}"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [[ -z "$DATASET_NAME" ]]; then
    echo "Error: --dataset-name <NAME> is required"
    exit 1
fi

echo "========================================"
echo "STAGE 3: Preprocess Dataset"
echo "========================================"
echo ""
echo "Dataset: $DATASET_NAME"
echo ""

# Run preprocessing (customize for your setup)
uvx modal run --detach modal_apps/preprocess.py --dataset-name "$DATASET_NAME"

echo ""
echo "Preprocessing job started for: $DATASET_NAME"
