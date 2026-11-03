#!/usr/bin/env bash
# Regenerate hero image derivatives from source/performance-master.jpg
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MASTER="$ROOT/source/performance-master.jpg"
OUT="$ROOT/assets"

if [[ ! -f "$MASTER" ]]; then
  echo "Missing $MASTER — restore from backup or git history." >&2
  exit 1
fi

command -v sips >/dev/null && command -v cwebp >/dev/null || {
  echo "Need macOS sips and cwebp (brew install webp)." >&2
  exit 1
}

for W in 180 230 260 360 460 520; do
  sips -Z "$W" "$MASTER" --out "$OUT/performance-${W}.jpg" >/dev/null
  cwebp -q 82 "$OUT/performance-${W}.jpg" -o "$OUT/performance-${W}.webp" >/dev/null
  echo "performance-${W} OK"
done

echo "Done. Deploy assets/performance-*.jpg|webp only (not the 2560 master)."
