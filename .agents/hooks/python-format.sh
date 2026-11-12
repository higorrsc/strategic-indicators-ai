#!/usr/bin/env bash

set -e

CHANGED_FILES=$(git diff --name-only -- '*.py')

if [ -z "$CHANGED_FILES" ]; then
    echo "{}"
    exit 0
fi

echo "Formatting changed Python files..." >&2

ruff format $CHANGED_FILES >&2
ruff check $CHANGED_FILES --fix >&2

echo "{}"
exit 0
