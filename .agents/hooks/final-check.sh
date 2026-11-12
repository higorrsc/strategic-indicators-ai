#!/bin/bash

STATUS=$(git status --short)

if [ -n "$STATUS" ]; then
    echo "Repository has uncommitted changes:" >&2
    echo "$STATUS" >&2
else
    echo "Repository clean." >&2
fi

echo '{"decision": "stop"}'
exit 0
