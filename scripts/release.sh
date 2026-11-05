#!/usr/bin/env bash
# Release helper for the pipeline: `current [REF]` prints X.Y.Z; `set OLD NEW ENTRY` bumps version files and prints their paths.
set -euo pipefail
cd "$(dirname "$0")/.."
case "${1:-}" in
current)
  ref="${2:-}"
  if [ -n "$ref" ]; then src=$(git show "$ref:pyproject.toml" 2>/dev/null || true); else src=$(cat pyproject.toml); fi  # a REF without the file predates versioning: 0.0.0
  [ -n "$src" ] || { echo 0.0.0; exit 0; }
  printf '%s\n' "$src" | sed -n 's/^version = "\([0-9]*\.[0-9]*\.[0-9]*\)"$/\1/p' | head -1
  ;;
set)
  old="$2"; new="$3"; entry="$4"
  sed -i "s/^version = \"$old\"\$/version = \"$new\"/" pyproject.toml
  { printf '# Changelog\n\n## [%s] - %s\n\n%s\n' "$new" "$(date -u +%F)" "$entry"; tail -n +3 CHANGELOG.md | sed '/^## \[Unreleased\]$/,$!b' | sed '1{/^## \[Unreleased\]$/d}'; } > CHANGELOG.md.new
  mv CHANGELOG.md.new CHANGELOG.md
  printf 'pyproject.toml\nCHANGELOG.md\n'
  ;;
*) echo "usage: release.sh current [REF] | set OLD NEW ENTRY" >&2; exit 2 ;;
esac
