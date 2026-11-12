#!/bin/bash

set -e

COMMAND="$ANTIGRAVITY_COMMAND"

if [[ "$COMMAND" == git\ commit* ]]; then
    echo "Running quality checks before commit..." >&2

    make check >&2 || {
        echo "Commit blocked: quality checks failed." >&2
        echo '{"decision": "deny", "reason": "quality checks failed"}'
        exit 0
    }
fi

echo '{"decision": "allow"}'
exit 0
