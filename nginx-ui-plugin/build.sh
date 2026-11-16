#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="$ROOT/dist/linux-arm64"

mkdir -p "$OUT"
install -m 0755 "$ROOT/server/main.py" "$OUT/nginx-module-manager"

echo "Built linux-arm64 plugin launcher: $OUT/nginx-module-manager"
