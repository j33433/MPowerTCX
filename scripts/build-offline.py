#!/usr/bin/env python3
"""Build a portable offline zip of upload.bike.

Produces web/downloads/upload.bike-portable.zip containing a single
self-contained index.html with all CSS, JS, and WASM inlined.
Works from file://, inside a zip without extracting, or anywhere.

Usage:
    python3 scripts/build-offline.py
"""

import base64
import os
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
OUTDIR = os.path.join(WEB, "downloads")
TMPDIR = os.path.join(ROOT, "target", "offline-build")

CDN = {
    "pico.css": "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css",
    "alpine.js": "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
}


def run(cmd, **kw):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kw)


def download(url):
    print(f"  Downloading {url}")
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def build_wasm_no_modules():
    print("Building WASM (--target no-modules)...")
    shutil.rmtree(TMPDIR, ignore_errors=True)
    os.makedirs(TMPDIR, exist_ok=True)
    run([
        "wasm-pack", "build",
        "crates/mpowertcx-wasm",
        "--target", "no-modules",
        "--out-dir", TMPDIR,
    ], cwd=ROOT)

    with open(os.path.join(TMPDIR, "mpowertcx_wasm.js"), "r") as f:
        glue = f.read()
    with open(os.path.join(TMPDIR, "mpowertcx_wasm_bg.wasm"), "rb") as f:
        wasm_bytes = f.read()

    b64 = base64.b64encode(wasm_bytes).decode("ascii")
    init_code = (
        f"\nvar _wasmBytes = Uint8Array.from(atob('{b64}'),"
        f" function(c) {{ return c.charCodeAt(0); }});\n"
        f"wasm_bindgen.initSync(new WebAssembly.Module(_wasmBytes));\n"
    )
    return glue + init_code


def build_offline_html(wasm_js, pico_css, alpine_js, custom_css, theme_js):
    with open(os.path.join(WEB, "index.html"), "r") as f:
        html = f.read()

    # Inline Pico CSS
    html = html.replace(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">',
        f'<style>\n{pico_css}\n</style>'
    )

    # Inline custom.css
    html = html.replace(
        '<link rel="stylesheet" href="./custom.css">',
        f'<style>\n{custom_css}\n</style>'
    )

    # Replace nav: remove converter/download/how-it-works links,
    # point brand to GitHub
    html = html.replace(
        '        <li class="active"><a href="./index.html">Converter</a></li>\n'
        '        <li><a href="./how-it-works.html">How It Works</a></li>\n'
        '        <li><a href="./download.html">Download</a></li>\n',
        ''
    )
    html = html.replace(
        '<a href="./index.html"><strong>upload.bike</strong></a>',
        '<a href="https://github.com/j33433/MPowerTCX"><strong>upload.bike</strong></a>'
    )

    # Replace dynamic import with wasm_bindgen global
    html = html.replace(
        "const { default: init, convert_csv_to_tcx } = await import('./pkg/mpowertcx_wasm.js');\n"
        "            await init('./pkg/mpowertcx_wasm_bg.wasm');\n"
        "            convert = convert_csv_to_tcx;",
        "convert = wasm_bindgen.convert_csv_to_tcx;"
    )

    # Inline WASM glue + base64 before the converter script
    html = html.replace(
        '  <script>\n    function converter() {',
        f'  <script>\n{wasm_js}\n  </script>\n  <script>\n    function converter() {{'
    )

    # Inline theme.js
    html = html.replace(
        '  <script src="./theme.js"></script>\n',
        f'  <script>\n{theme_js}\n  </script>\n'
    )

    # Inline Alpine.js (replace the CDN script tag at end of body)
    html = html.replace(
        '  <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>',
        f'  <script>\n{alpine_js}\n  </script>'
    )

    return html


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    print("Downloading CDN assets...")
    pico_css = download(CDN["pico.css"]).decode()
    alpine_js = download(CDN["alpine.js"]).decode()

    wasm_js = build_wasm_no_modules()

    print("Reading source files...")
    with open(os.path.join(WEB, "custom.css"), "r") as f:
        custom_css = f.read()
    with open(os.path.join(WEB, "theme.js"), "r") as f:
        theme_js = f.read()

    print("Building self-contained index.html...")
    index_html = build_offline_html(wasm_js, pico_css, alpine_js, custom_css, theme_js)

    readme = (
        "upload.bike - Offline Edition\n"
        "=============================\n\n"
        "Double-click index.html to open the converter.\n\n"
        "Everything runs in your browser. No internet, installation, or server required.\n"
        "For the full guide with interactive physics chart, visit:\n"
        "https://upload.bike/how-it-works.html\n\n"
        "Source code: https://github.com/j33433/MPowerTCX\n"
    )

    print("Creating zip...")
    zip_path = os.path.join(OUTDIR, "upload.bike-portable.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", index_html)
        zf.writestr("README.txt", readme)

    size_kb = os.path.getsize(zip_path) / 1024
    html_kb = len(index_html.encode()) / 1024
    print(f"\nDone: {zip_path} ({size_kb:.0f} KB)")
    print(f"  index.html: {html_kb:.0f} KB (self-contained)")

    shutil.rmtree(TMPDIR, ignore_errors=True)


if __name__ == "__main__":
    main()
