#!/bin/bash

FILES=$(git diff --name-only)

if echo "$FILES" | grep -qE "models|entities|schemas"; then
    echo "Database-related files changed." >&2
    echo "Review if an Alembic migration is required." >&2
fi

echo "{}"
exit 0
