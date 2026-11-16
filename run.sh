#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Ensure user developer paths (NVM node/npm, local bin, cargo) are available for desktop launches
if [ -d "$HOME/.nvm/versions/node" ]; then
    NODE_BIN="$(find "$HOME/.nvm/versions/node" -maxdepth 2 -type d -name "bin" 2>/dev/null | sort -V | tail -n 1)"
    if [ -n "$NODE_BIN" ]; then
        export PATH="$NODE_BIN:$PATH"
    fi
fi
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PYTHONPATH="$DIR/src:$PYTHONPATH"

exec python3 "$DIR/src/main.py" "$@"

