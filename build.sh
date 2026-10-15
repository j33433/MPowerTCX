#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v cargo >/dev/null 2>&1; then
    printf 'error: cargo is required; install Rust first\n' >&2
    exit 1
fi

if ! command -v wasm-pack >/dev/null 2>&1; then
    printf 'error: wasm-pack is required; install it with cargo install wasm-pack\n' >&2
    exit 1
fi

printf 'Building native release...\n'
cargo build --manifest-path "$ROOT_DIR/Cargo.toml" --release

printf 'Building browser WASM release...\n'
wasm-pack build "$ROOT_DIR/crates/mpowertcx-wasm" \
    --target web \
    --out-dir "$ROOT_DIR/web/pkg" \
    --release

printf 'Build complete.\n'
printf '  Native binary: %s\n' "$ROOT_DIR/target/release/mpowertcx"
printf '  Browser package: %s\n' "$ROOT_DIR/web/pkg"
