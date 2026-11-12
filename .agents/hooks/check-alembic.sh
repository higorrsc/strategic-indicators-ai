#!/usr/bin/env bash

COMMAND="${ANTIGRAVITY_COMMAND:-}"

if [[ "$COMMAND" == *"alembic revision"* ]]; then
    echo "Review generated migration before committing." >&2
fi

echo '{"decision": "allow"}'
exit 0
