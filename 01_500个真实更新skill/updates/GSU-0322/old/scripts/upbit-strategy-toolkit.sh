#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_upbit_strategy_toolkit_root() {
  local dir="$SCRIPT_DIR"

  while [ "$dir" != "/" ]; do
    if [ -f "$dir/pyproject.toml" ] \
      && [ -d "$dir/upbit_strategy_toolkit" ] \
      && grep -q 'name = "upbit-strategy-toolkit"' "$dir/pyproject.toml"; then
      printf '%s\n' "$dir"
      return 0
    fi

    dir="$(dirname "$dir")"
  done

  return 1
}

if ROOT="$(find_upbit_strategy_toolkit_root)"; then
  # Pin the data root to the repo root; --project only fixes the code location, so
  # without this get_data_path() falls back to cwd and writes the cache there.
  exec env UPBIT_TOOLKIT_DATA_DIR="$ROOT" uv run --project "$ROOT" upbit-strategy-toolkit "$@"
fi

mkdir -p "$HOME/.upbit-strategy-toolkit"
UPBIT_TOOLKIT_DATA_DIR="$HOME/.upbit-strategy-toolkit" exec \
  uvx --from git+https://github.com/upbit-official/upbit-strategy-toolkit.git \
  upbit-strategy-toolkit "$@"
