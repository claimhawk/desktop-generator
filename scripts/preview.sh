#!/usr/bin/env bash
# Copyright (c) 2025 Tylt LLC. All rights reserved.
# CONFIDENTIAL AND PROPRIETARY. Unauthorized use, copying, or distribution
# is strictly prohibited. For licensing inquiries: hello@claimhawk.app

# Preview dataset distribution before generating
#
# Shows estimated task counts and total samples based on dataset.yaml config
#
# Usage:
#   ./scripts/preview.sh                  # Use default config
#   ./scripts/preview.sh --config <path>  # Use custom config

set -euo pipefail

echo "========================================"
echo "Dataset Distribution Preview"
echo "========================================"
echo ""

# Check if preview_dataset.py exists
if [[ ! -f "preview_dataset.py" ]]; then
    echo "ERROR: preview_dataset.py not found"
    echo ""
    echo "This script requires preview_dataset.py to be present in the project root."
    echo "Please create it based on appointment-full/preview_dataset.py"
    exit 1
fi

# Run preview script with all arguments passed through
uv run python preview_dataset.py "$@"

echo ""
echo "Next steps:"
echo "  # Generate test dataset (1%)"
echo "  ./scripts/test.sh"
echo ""
echo "  # Generate full dataset on Modal"
echo "  ./scripts/production.sh"
echo ""
