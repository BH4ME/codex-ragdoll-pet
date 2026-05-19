#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${CODEX_HOME:-"$HOME/.codex"}/pets/ragdoll-cat"

mkdir -p "$TARGET_DIR"
cp "$ROOT_DIR/pet/ragdoll-cat/pet.json" "$TARGET_DIR/pet.json"
cp "$ROOT_DIR/pet/ragdoll-cat/spritesheet.png" "$TARGET_DIR/spritesheet.png"

echo "Installed Ragdoll Cat pet to $TARGET_DIR"
echo "Open Codex settings and select Ragdoll Cat from the pet/avatar picker."
