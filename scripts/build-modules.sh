#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/work"
DIST="$ROOT/dist"
NGINX_VERSION="${NGINX_VERSION:-1.28.0}"

mkdir -p "$WORK" "$DIST" "$WORK/modules"

if [[ "$(dpkg --print-architecture)" != "arm64" ]]; then
    echo "ERROR: ARM64 is required"
    exit 1
fi

apt-get update
apt-get install -y build-essential git curl ca-certificates jq zip python3 libpcre2-dev zlib1g-dev libssl-dev

# Validate before cloning or compiling any module.
python3 "$ROOT/scripts/validate-config.py"

NGINX_SRC="$WORK/nginx-$NGINX_VERSION"
if [[ ! -d "$NGINX_SRC" ]]; then
    curl -fL "https://nginx.org/download/nginx-$NGINX_VERSION.tar.gz" -o "$WORK/nginx.tar.gz"
    tar -xzf "$WORK/nginx.tar.gz" -C "$WORK"
fi

# Prevent stale local artifacts from entering the generated index.
rm -f "$DIST"/*

COUNT=$(jq '.modules | length' "$ROOT/config/modules.json")
for ((i=0; i<COUNT; i++)); do
    ID=$(jq -r ".modules[$i].id" "$ROOT/config/modules.json")
    NAME=$(jq -r ".modules[$i].name" "$ROOT/config/modules.json")
    REPO=$(jq -r ".modules[$i].repository" "$ROOT/config/modules.json")
    REF=$(jq -r ".modules[$i].ref" "$ROOT/config/modules.json")

    if [[ ! "$ID" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        echo "Invalid module ID: $ID"
        exit 1
    fi

    MODULE="$WORK/modules/$ID"
    BUILD="$WORK/build-$ID"
    STAGE="$WORK/stage-$ID"
    rm -rf "$MODULE" "$BUILD" "$STAGE"
    git clone --depth 1 --branch "$REF" "$REPO" "$MODULE"

    mkdir -p "$BUILD" "$STAGE"
    cp -a "$NGINX_SRC/." "$BUILD/"
    cd "$BUILD"

    EXTRA_ARGS=()
    while IFS= read -r ARG; do
        [[ -n "$ARG" ]] && EXTRA_ARGS+=("$ARG")
    done < <(jq -r ".modules[$i].configure_args[]?" "$ROOT/config/modules.json")

    # Preserve the existing headers-more configure flags and output layout.
    ./configure --with-compat "--add-dynamic-module=$MODULE" "${EXTRA_ARGS[@]}"
    make -j"$(nproc)" modules

    FOUND=0
    for SO in objs/*.so; do
        [[ -f "$SO" ]] || continue
        cp "$SO" "$STAGE/"
        FOUND=1
    done
    if [[ "$FOUND" != "1" ]]; then
        echo "ERROR: No .so generated for $ID"
        exit 1
    fi

    SOURCE="$DIST/$ID-source-$REF.tar.gz"
    tar --exclude=.git -czf "$SOURCE" -C "$WORK/modules" "$ID"
    cp "$SOURCE" "$STAGE/"

    python3 - "$STAGE/metadata.json" "$ID" "$NAME" "$REF" "$NGINX_VERSION" <<'PY'
import json
import sys
path, module_id, name, ref, nginx = sys.argv[1:]
data = {
    "id": module_id, "name": name, "version": ref,
    "nginx_version": nginx, "os": "debian", "debian_release": "13",
    "architecture": "arm64", "build_flavor": "nginx.org-upstream-source",
    "type": "dynamic"
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

    ARCHIVE="$DIST/${ID}-debian13-arm64-nginx-${NGINX_VERSION}.zip"
    (
        cd "$STAGE"
        sha256sum *.so *.tar.gz metadata.json > SHA256SUMS
        zip -q -r "$ARCHIVE" .
    )
    sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
    echo "SUCCESS: $NAME"
done

echo "All modules built successfully."
