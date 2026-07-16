#!/usr/bin/env python3
"""Build a portable offline zip of upload.bike.

Produces web/downloads/upload.bike-portable.zip containing a single
self-contained index.html with all CSS, JS, and WASM inlined.
Works from file://, inside a zip without extracting, or anywhere.

The source page (web/index.html) marks differences with attributes:
  data-online-only     removed in the offline build
  data-offline-href    applied to href when building offline
  data-inline="id"     replaced with inlined asset contents
  <!-- offline-inject -->  injection point for wasm/chart/preview scripts

Runtime dual-boot uses window.MPOWERTCX_OFFLINE (set by this builder).

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

OFFLINE_INJECT_MARKER = "<!-- offline-inject: wasm, chart.js, zoom, preview-chart -->"


def run(cmd, **kw):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kw)


def download(url):
    print(f"  Downloading {url}")
    with urllib.request.urlopen(url) as resp:
        return resp.read()


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


def strip_online_only(html):
    """Remove elements that carry data-online-only (simple nesting, no same-tag nest)."""
    pattern = re.compile(
        r"<([a-zA-Z][\w:-]*)([^>]*\bdata-online-only\b[^>]*)>(.*?)</\1\s*>",
        re.S,
    )
    prev = None
    while prev != html:
        prev = html
        html = pattern.sub("", html)
    if re.search(r"\bdata-online-only\b", html):
        raise SystemExit("offline build: unstripped data-online-only remains")
    return html


def apply_offline_href(html):
    """Copy data-offline-href into href and drop the marker attribute."""
    tag_pat = re.compile(
        r"<([a-zA-Z][\w:-]*)([^>]*\bdata-offline-href=\"([^\"]*)\"[^>]*)>",
    )

    def tag_repl(m):
        tag, attrs, href = m.group(1), m.group(2), m.group(3)
        attrs = re.sub(r'\s*data-offline-href="[^"]*"', "", attrs)
        if re.search(r'\bhref="', attrs):
            attrs = re.sub(r'\bhref="[^"]*"', f'href="{href}"', attrs, count=1)
        else:
            attrs = f' href="{href}"' + attrs
        return f"<{tag}{attrs}>"

    html2, n = tag_pat.subn(tag_repl, html)
    if n == 0 and "data-offline-href" in html:
        raise SystemExit("offline build: data-offline-href present but not applied")
    return html2


def inline_marked_assets(html, assets):
    """Replace tags with data-inline="id" using assets[id] -> replacement HTML."""
    tag_pat = re.compile(
        r"<([a-zA-Z][\w:-]*)([^>]*\bdata-inline=\"([^\"]+)\"[^>]*)\s*>"
        r"(?:</\1\s*>)?",
        re.S,
    )
    missing = set()

    def repl(m):
        key = m.group(3)
        if key not in assets:
            missing.add(key)
            return m.group(0)
        return assets[key]

    html2, n = tag_pat.subn(repl, html)
    if missing:
        raise SystemExit(f"offline build: unknown data-inline ids: {sorted(missing)}")
    if "data-inline=" in html2:
        raise SystemExit("offline build: unreplaced data-inline remains")
    if n == 0:
        raise SystemExit("offline build: no data-inline tags found")
    return html2


def inject_offline_bundle(html, scripts):
    if OFFLINE_INJECT_MARKER not in html:
        raise SystemExit(f"offline build: missing marker {OFFLINE_INJECT_MARKER!r}")
    inject = (
        '  <script>window.MPOWERTCX_OFFLINE = true;</script>\n'
        + "".join(f"  <script>\n{src}\n  </script>\n" for src in scripts)
    )
    return html.replace(OFFLINE_INJECT_MARKER, inject.rstrip("\n"), 1)


def build_offline_html(wasm_js, pico_css, alpine_js, custom_css, theme_js, icon_svg,
                       chart_js, chart_zoom_js, preview_chart_js):
    with open(os.path.join(WEB, "index.html"), "r") as f:
        html = f.read()

    preview_js = preview_chart_js.replace(
        "export function createPreviewChart",
        "function createPreviewChart",
    )
    if preview_js == preview_chart_js:
        raise SystemExit("offline build: export function createPreviewChart not found")

    assets = {
        "pico.css": f"<style>\n{pico_css}\n</style>",
        "custom.css": f"<style>\n{custom_css}\n</style>",
        "theme.js": f"<script>\n{theme_js}\n</script>",
        "alpine.js": f"<script>\n{alpine_js}\n</script>",
        "icon.svg": f'<img src="data:image/svg+xml,{icon_svg}" alt="upload.bike">',
    }

    html = strip_online_only(html)
    html = apply_offline_href(html)
    html = inline_marked_assets(html, assets)
    html = inject_offline_bundle(html, [
        wasm_js,
        chart_js,
        chart_zoom_js,
        preview_js,
    ])

    for needle, label in (
        ("MPOWERTCX_OFFLINE", "offline flag"),
        ("wasm_bindgen", "wasm_bindgen global"),
        ("_wasmBytes", "inlined WASM bytes"),
        ("createPreviewChart", "preview chart"),
        ("function converter()", "converter app"),
    ):
        if needle not in html:
            raise SystemExit(f"offline build: missing {label} in output HTML")
    if re.search(r"\bdata-online-only\b|\bdata-inline=|\bdata-offline-href\b", html):
        raise SystemExit("offline build: leftover offline-build attributes in output")

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
    index_html = build_offline_html(
        wasm_js, pico_css, alpine_js, custom_css, theme_js, icon_svg,
        chart_js, chart_zoom_js, preview_chart_js,
    )

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
