#!/usr/bin/env bash

set -e

LOG_FILE="hooks/debug.log"

{
    echo "=========="
    date
    echo "Command:"
    echo "${ANTIGRAVITY_COMMAND:-unknown}"

    echo "Arguments:"
    echo "$@"

    echo "Environment:"
    env | sort

} >> "$LOG_FILE"

echo '{"decision": "allow"}'
exit 0
