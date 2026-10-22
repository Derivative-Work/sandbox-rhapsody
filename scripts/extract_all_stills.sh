#!/usr/bin/env bash
# Run extract_stills.sh on every Animusic reference, 4 at a time. Slug = the piece's name, lowercased and hyphenated.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
for f in reference/inspiration/*.webm; do
  slug=$(basename "$f" | sed -E 's/ \(Animusic\).*//' | tr 'A-Z ' 'a-z-')
  printf '%s\0%s\0' "$f" "$slug"
done | xargs -0 -n2 -P4 scripts/extract_stills.sh
