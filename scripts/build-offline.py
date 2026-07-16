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
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
OUTDIR = os.path.join(WEB, "downloads")
TMPDIR = os.path.join(ROOT, "target", "offline-build")
PKG = os.path.join(WEB, "pkg")

CDN = {
    "pico.css": "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css",
    "alpine.js": "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
    "chart.js": "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js",
    "chart-zoom.js": "https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.2.0/dist/chartjs-plugin-zoom.min.js",
}


def run(cmd, **kw):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kw)


def download(url):
    print(f"  Downloading {url}")
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def must_replace(html, old, new, label):
    count = html.count(old)
    if count != 1:
        raise SystemExit(
            f"offline build: expected pattern once for {label}, found {count}:\n{old!r}"
        )
    return html.replace(old, new)


def wasm_bytes_init(b64):
    return (
        f"\nvar _wasmBytes = Uint8Array.from(atob('{b64}'),"
        f" function(c) {{ return c.charCodeAt(0); }});\n"
    )


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
        wasm_bytes_init(b64)
        + "wasm_bindgen.initSync(new WebAssembly.Module(_wasmBytes));\n"
    )
    return glue + init_code


def build_wasm_from_pkg():
    """Fallback: embed existing web/pkg (ES module) as a classic script."""
    print("Packaging existing web/pkg WASM (wasm-pack not available)...")
    js_path = os.path.join(PKG, "mpowertcx_wasm.js")
    wasm_path = os.path.join(PKG, "mpowertcx_wasm_bg.wasm")
    if not os.path.isfile(js_path) or not os.path.isfile(wasm_path):
        raise SystemExit(
            "offline build: web/pkg WASM missing and wasm-pack not available"
        )

    with open(js_path, "r") as f:
        glue = f.read()
    with open(wasm_path, "rb") as f:
        wasm_bytes = f.read()

    # Classic script: drop ES module exports and import.meta (illegal outside modules)
    glue = glue.replace("export class ConvertResult", "class ConvertResult")
    glue = glue.replace("export function convert_csv_to_tcx", "function convert_csv_to_tcx")
    glue = glue.replace("export function get_sample_csv", "function get_sample_csv")
    glue = re.sub(r"export\s*\{[^}]+\}\s*;?", "", glue)
    glue = glue.replace(
        "module_or_path = new URL('mpowertcx_wasm_bg.wasm', import.meta.url);",
        "throw new Error('WASM path init is not available in offline build');",
    )
    if "import.meta" in glue or re.search(r"^\s*export\s", glue, re.M):
        raise SystemExit("offline build: web/pkg glue still has module syntax")

    b64 = base64.b64encode(wasm_bytes).decode("ascii")
    init_code = (
        wasm_bytes_init(b64)
        + "initSync({ module: _wasmBytes });\n"
        + "var wasm_bindgen = { convert_csv_to_tcx: convert_csv_to_tcx,"
        + " get_sample_csv: get_sample_csv };\n"
    )
    return glue + init_code


def build_wasm_js():
    if shutil.which("wasm-pack"):
        return build_wasm_no_modules()
    return build_wasm_from_pkg()


def inject_before_converter_script(html, script_sources):
    """Insert classic <script> blocks immediately before the converter app script."""
    marker = "function converter()"
    idx = html.find(marker)
    if idx < 0:
        raise SystemExit("offline build: function converter() not found in index.html")
    script_start = html.rfind("<script>", 0, idx)
    if script_start < 0:
        raise SystemExit("offline build: <script> before converter() not found")
    inject = "".join(f"  <script>\n{src}\n  </script>\n" for src in script_sources)
    return html[:script_start] + inject + html[script_start:]


def build_offline_html(wasm_js, pico_css, alpine_js, custom_css, theme_js, icon_svg,
                       chart_js, chart_zoom_js, preview_chart_js):
    with open(os.path.join(WEB, "index.html"), "r") as f:
        html = f.read()

    # Inline Pico CSS
    html = must_replace(
        html,
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">',
        f'<style>\n{pico_css}\n</style>',
        "pico.css link",
    )

    # Inline custom.css
    html = must_replace(
        html,
        '<link rel="stylesheet" href="./custom.css">',
        f'<style>\n{custom_css}\n</style>',
        "custom.css link",
    )

    # Replace nav: remove converter/download/how-it-works links,
    # point brand to GitHub
    html = must_replace(
        html,
        '        <li class="active"><a href="./">Converter</a></li>\n'
        '        <li><a href="./how-it-works.html">About</a></li>\n'
        '        <li><a href="./download.html">Download</a></li>\n',
        '',
        "nav links",
    )
    html = must_replace(
        html,
        '    <div class="container">\n      <a href="./" class="brand-icon"><img src="./icon.svg" alt="upload.bike"></a>\n      <ul>',
        f'    <div class="container">\n      <a href="https://github.com/j33433/MPowerTCX" class="brand-icon"><img src="data:image/svg+xml,{icon_svg}" alt="upload.bike"></a>\n      <ul>',
        "brand icon",
    )

    # Remove the [?] help links. They point at how-it-works.html, which
    # doesn't exist in the single-file offline build.
    html = must_replace(
        html,
        ' <a class="help-link" href="./how-it-works.html#interpolation">[?]</a>',
        '',
        "interpolation help link",
    )
    html = must_replace(
        html,
        ' <a class="help-link" href="./how-it-works.html#physics">[?]</a>',
        '',
        "physics help link",
    )

    # Sample CSV is not bundled offline (fetch would fail under file://).
    html = must_replace(
        html,
        '\n        <p class="sample-link center"><span class="muted small">No file? <a href="#" @click.prevent="loadSample()">Try a sample</a>.</span></p>\n',
        '\n',
        "try a sample link",
    )

    # Replace dynamic import with wasm_bindgen global
    html = must_replace(
        html,
        "const { default: init, convert_csv_to_tcx } = await import('./pkg/mpowertcx_wasm.js');\n"
        "            await init('./pkg/mpowertcx_wasm_bg.wasm');\n"
        "            convert = convert_csv_to_tcx;",
        "convert = wasm_bindgen.convert_csv_to_tcx;",
        "wasm import",
    )

    # Inline preview-chart.js (strip export so it's a plain script, not a module)
    preview_js = preview_chart_js.replace(
        'export function createPreviewChart',
        'function createPreviewChart',
    )
    if preview_js == preview_chart_js:
        raise SystemExit("offline build: export function createPreviewChart not found")

    # WASM + Chart.js + zoom + preview, before the converter app script
    html = inject_before_converter_script(html, [
        wasm_js,
        chart_js,
        chart_zoom_js,
        preview_js,
    ])

    # Replace dynamic import of preview-chart.js with the now-global function
    html = must_replace(
        html,
        "const { createPreviewChart } = await import('./preview-chart.js');\n"
        "              preview = createPreviewChart('previewChart');",
        "preview = createPreviewChart('previewChart');",
        "preview-chart import",
    )

    # Inline theme.js
    html = must_replace(
        html,
        '  <script src="./theme.js"></script>\n',
        f'  <script>\n{theme_js}\n  </script>\n',
        "theme.js",
    )

    # Inline Alpine.js (replace the CDN script tag at end of body)
    html = must_replace(
        html,
        '  <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>',
        f'  <script>\n{alpine_js}\n  </script>',
        "alpine.js",
    )

    # Sanity checks so silent breakage is harder next time
    for needle, label in (
        ("wasm_bindgen", "wasm_bindgen global"),
        ("_wasmBytes", "inlined WASM bytes"),
        ("createPreviewChart", "preview chart"),
        ("function converter()", "converter app"),
    ):
        if needle not in html:
            raise SystemExit(f"offline build: missing {label} in output HTML")
    if "import('./pkg/" in html or "import('./preview-chart" in html:
        raise SystemExit("offline build: dynamic imports still present in output HTML")

    return html


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    print("Downloading CDN assets...")
    pico_css = download(CDN["pico.css"]).decode()
    alpine_js = download(CDN["alpine.js"]).decode()
    chart_js = download(CDN["chart.js"]).decode()
    chart_zoom_js = download(CDN["chart-zoom.js"]).decode()

    wasm_js = build_wasm_js()

    print("Reading source files...")
    with open(os.path.join(WEB, "custom.css"), "r") as f:
        custom_css = f.read()
    with open(os.path.join(WEB, "theme.js"), "r") as f:
        theme_js = f.read()
    with open(os.path.join(WEB, "icon.svg"), "r") as f:
        icon_svg = urllib.parse.quote(f.read().strip(), safe="")
    with open(os.path.join(WEB, "preview-chart.js"), "r") as f:
        preview_chart_js = f.read()

    print("Building self-contained index.html...")
    index_html = build_offline_html(wasm_js, pico_css, alpine_js, custom_css, theme_js, icon_svg,
                                    chart_js, chart_zoom_js, preview_chart_js)

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
