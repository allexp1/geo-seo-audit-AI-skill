#!/usr/bin/env bash
# Plain installer. No curl-pipe-bash. Reads only this directory; writes only
# to ~/.claude/skills/geo. Re-run safely — it overwrites.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${HOME}/.claude/skills/geo"

echo "Installing geo skill"
echo "  source: ${SRC}"
echo "  dest:   ${DEST}"

mkdir -p "${DEST}"
cp "${SRC}/SKILL.md" "${DEST}/SKILL.md"
cp "${SRC}/sources.md" "${DEST}/sources.md"
cp -R "${SRC}/scripts" "${DEST}/scripts"
cp -R "${SRC}/schema" "${DEST}/schema"

# Knowledge base: seed on first install, but never clobber a copy that the
# installed skill's Refresh Protocol has been keeping current.
if [ ! -f "${DEST}/KNOWLEDGE.md" ]; then
  cp "${SRC}/KNOWLEDGE.md" "${DEST}/KNOWLEDGE.md"
  cp "${SRC}/CHANGELOG.md" "${DEST}/CHANGELOG.md"
else
  echo "Kept existing KNOWLEDGE.md/CHANGELOG.md (refreshed copies may be newer than the repo's)."
fi

if ! python3 -c "import requests, bs4" 2>/dev/null; then
  echo
  echo "Python deps missing. Install with:"
  echo "  python3 -m pip install -r ${SRC}/requirements.txt"
fi

echo
echo "Done. Restart Claude Code so it picks up the skill."
echo "Then run: /geo audit https://example.com"
