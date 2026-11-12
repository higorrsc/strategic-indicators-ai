#!/usr/bin/env bash

set -e

for file in .agents/hooks/*.sh
do
    bash -n "$file" >&2
done

echo "All agent hooks are valid." >&2
echo "{}"
exit 0
