#!/usr/bin/env bash
# Installs:
#   - geo (this skill) → ~/.claude/skills/geo/
#   - business-idea-validator (companion, separate repo) → ~/.claude/skills/business-idea-validator/
# Re-run safely — it overwrites.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${HOME}/.claude/skills"
BIV_REPO="https://github.com/allexp1/business-idea-validator-AI-skill.git"

mkdir -p "${SKILLS_DIR}"

# --- 1) geo (this skill) ---
GEO_DEST="${SKILLS_DIR}/geo"
echo "Installing geo skill"
echo "  source: ${SRC}"
echo "  dest:   ${GEO_DEST}"

mkdir -p "${GEO_DEST}"
cp "${SRC}/SKILL.md" "${GEO_DEST}/SKILL.md"
cp -R "${SRC}/scripts" "${GEO_DEST}/scripts"
cp -R "${SRC}/schema" "${GEO_DEST}/schema"

if ! python3 -c "import requests, bs4" 2>/dev/null; then
  echo
  echo "Python deps missing. Install with:"
  echo "  python3 -m pip install -r ${SRC}/requirements.txt"
fi

# --- 2) business-idea-validator (companion skill from separate repo) ---
echo
echo "Installing companion skill: business-idea-validator (from ${BIV_REPO})"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required to install the companion skill. Install git and re-run."
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

git clone --depth 1 "${BIV_REPO}" "${TMP_DIR}/biv-repo" >/dev/null 2>&1

BIV_DEST="${SKILLS_DIR}/business-idea-validator"
echo "  dest:   ${BIV_DEST}"
mkdir -p "${BIV_DEST}"
cp "${TMP_DIR}/biv-repo/SKILL.md" "${BIV_DEST}/SKILL.md"
cp -R "${TMP_DIR}/biv-repo/references" "${BIV_DEST}/references"

echo
echo "Done. Restart Claude Code so it picks up the skills."
echo "Slash commands: /geo audit https://example.com  and  /business-idea-validator"
