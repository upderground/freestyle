#!/usr/bin/env bash
# Apply local-edit/index.html onto repo root (for commit after user says «готово»).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO/local-edit/index.html"
DST="$REPO/index.html"
BASE_REF="${1:-v0.8.0}"

if [[ ! -f "$SRC" ]]; then
  echo "Missing $SRC — start the editor and save first." >&2
  exit 1
fi

cp "$SRC" "$DST"
# Drop editor-only assets from the committed page if they were accidentally saved.
python3 - <<'PY' "$DST"
import re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
text = re.sub(r'\s*<link rel="stylesheet" href="edit-bar\.css">\s*', "\n", text)
text = re.sub(r'\s*<script src="edit-client\.js" defer></script>\s*', "\n", text)
open(path, "w", encoding="utf-8").write(text)
PY

echo "Updated $DST from local-edit."
echo "--- diff vs $BASE_REF (index.html) ---"
git -C "$REPO" diff "$BASE_REF" -- index.html || true
