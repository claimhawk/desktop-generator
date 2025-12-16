#!/usr/bin/env bash
# Copyright (c) 2025 Tylt LLC. All rights reserved.
# CONFIDENTIAL AND PROPRIETARY. Unauthorized use, copying, or distribution
# is strictly prohibited. For licensing inquiries: hello@claimhawk.app

# Verify dataset for out-of-sample (OOS) leakage
#
# Checks that test/eval samples never overlap with train/val dates
#
# Usage:
#   ./scripts/verify.sh                    # Verify most recent dataset
#   ./scripts/verify.sh datasets/<name>    # Verify specific dataset

set -euo pipefail

echo "========================================"
echo "Dataset OOS Leakage Verification"
echo "========================================"
echo ""

# Check if verify_no_leak.py exists
if [[ ! -f "verify_no_leak.py" ]]; then
    echo "WARNING: verify_no_leak.py not found"
    echo ""
    echo "This generator does not use date-based OOS splits, so verification is skipped."
    echo ""
    echo "If you need OOS verification:"
    echo "  1. Add date-based generation to your dataset"
    echo "  2. Create verify_no_leak.py based on appointment-full/verify_no_leak.py"
    echo ""
    exit 0
fi

# Run verification script with all arguments passed through
uv run python verify_no_leak.py "$@"

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    echo "Verification passed! Dataset is clean."
else
    echo ""
    echo "Verification failed! Please fix OOS leakage before training."
    exit 1
fi
