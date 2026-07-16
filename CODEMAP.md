# CODEMAP

Map of the MPowerTCX codebase: indoor-bike CSV → TCX for Strava/Garmin/etc.
Rust workspace (v2.1.0), browser WASM frontend at [upload.bike](https://upload.bike).

```
CSV bytes
  → equipment parsers (BikeParser trait)
  → Ride (samples + header)
  → optional interpolate / physics model
  → TCX XML (render_tcx)
  → optional lint_tcx
```

## Workspace layout

| Path | Role |
|------|------|
| `Cargo.toml` | Workspace: core, cli, wasm; version/edition/license |
| `crates/mpowertcx-core/` | Conversion library (no I/O, WASM-safe) |
| `crates/mpowertcx-cli/` | CLI binary `mpowertcx` |
| `crates/mpowertcx-wasm/` | `wasm-bindgen` bindings for the web UI |
| `web/` | Static site (converter, docs, offline zip) |
| `samples/` | Fixture CSVs + expected TCX (plain / `_interp` / `_model`) |
| `tests/` | Shell + Python golden-file comparison |
| `scripts/` | Offline build, release helpers |
| `.github/workflows/` | CI (offline zip / releases) |
| `legacy/` | Unmaintained Python/PySide2 desktop app |

---

## crates/mpowertcx-core

Library: parse CSV, build ride, interpolate, physics model, emit TCX, lint TCX.

| File | Lines | Purpose |
|------|------:|---------|
| `src/lib.rs` | 12 | Module exports; `VERSION` |
| `src/converter.rs` | 150 | Orchestration: detect parser, convert with options |
| `src/ride.rs` | 320 | `Ride` / `RideHeader`; interpolate; physics distance |
| `src/tcx.rs` | 109 | `render_tcx` → Garmin TCX XML |
| `src/physics.rs` | 76 | `SimpleBike` power → speed/distance model |
| `src/linter.rs` | 906 | TCX structural + plausibility checks (E/W codes) |
| `src/equipment/mod.rs` | 71 | `BikeParser`, `CsvRows`, `all_parsers()`, unit helpers |
| `src/equipment/echelon.rs` | 240 | Schwinn MPower Echelon V1/V2/V3 |
| `src/equipment/stages.rs` | 146 | Stages Indoor Cycles |
| `src/equipment/systm.rs` | 82 | Wahoo SYSTM |
| `src/equipment/thesufferfest.rs` | 54 | The Sufferfest |
| `tests/integration.rs` | — | Sample-based conversion tests |
| `tests/linter_tests.rs` | — | Linter unit tests |

### Data flow (core)

1. `Converter::from_csv(bytes)` → `CsvRows` + try each `BikeParser` in order
2. Parser fills `Ride` (power/rpm/hr/distance series + header)
3. `Converter::convert(start_time, ConvertOptions)`:
   - optional `Ride::interpolate()` (1 Hz linear)
   - optional `Ride::model_distance(mass)` via `SimpleBike`
   - `render_tcx` with optional power adjust
4. Callers may run `lint_tcx` on the XML

### Parser order (`all_parsers`)

1. TheSufferfest  
2. EchelonV1, EchelonV2, EchelonV3  
3. Systm  
4. Stages (fallback / broad CSV shapes)

### Key types

| Symbol | Location | Notes |
|--------|----------|--------|
| `ConvertOptions` | converter.rs | `interpolate`, `physics`, `physics_mass_kg`, `power_adjust_percent` |
| `Converter` | converter.rs | `from_csv`, `convert`, `date_hint`, `equipment_name` |
| `Ride` / `RideHeader` | ride.rs | Sample vectors as strings (legacy float formatting) |
| `BikeParser` | equipment/mod.rs | `try_load`, `name` |
| `CsvRows` | equipment/mod.rs | Null-stripped, line-normalized CSV walk |
| `SimpleBike` | physics.rs | `next_sample(power) → (speed, distance, time)` |
| `lint_tcx` / `has_errors` | linter.rs | Errors E001–E036 fail; warnings W013–W038 informational |

Deps: `csv`, `chrono`, `quick-xml`.

---

## crates/mpowertcx-cli

Thin CLI over core. Binary name: `mpowertcx`.

| File | Purpose |
|------|---------|
| `src/main.rs` | Arg parse; convert CSV→TCX or `--lint` TCX |

Flags: `--csv`, `--tcx`, `--time`, `--interpolate`, `--model <MASS_KG>`, `--lint`.

---

## crates/mpowertcx-wasm

Browser API over core.

| File | Purpose |
|------|---------|
| `src/lib.rs` | `convert_csv_to_tcx`, `get_sample_csv`, `ConvertResult` |

- Embeds `web/samples/1122.csv` for chart demos  
- Returns TCX string, equipment name, sample count, date hint, debug, lint error count  
- Built with:  
  `wasm-pack build crates/mpowertcx-wasm --target web --out-dir ../../web/pkg`

---

## web/

Client-only site. Processing is WASM in the browser.

| File | Purpose |
|------|---------|
| `index.html` | Converter UI |
| `how-it-works.html` | About + interactive physics chart |
| `download.html` | Offline zip download page |
| `custom.css` | Pico CSS extensions |
| `theme.js` | Light/dark toggle |
| `preview-chart.js` | Workout preview chart (ES module) |
| `chart-demo.js` | Physics model chart engine (ES module) |
| `icon.svg`, `favicon.ico` | Branding |
| `pkg/` | Generated wasm-pack output (do not hand-edit) |
| `samples/` | CSVs bundled for demos |
| `downloads/` | Offline zip output (built artifact) |

Local preview: `cd web && python3 -m http.server`

---

## samples/

Golden fixtures: `*.csv` inputs and expected TCX for three modes:

| Suffix | Mode |
|--------|------|
| `.tcx` | Plain conversion |
| `_interp.tcx` | 1-second interpolation |
| `_model.tcx` | Physics speed/distance model |

Covers Echelon, Stages, Sufferfest, SYSTM, edge cases (nulls, missing headers, empty).

---

## tests/

| File | Purpose |
|------|---------|
| `test_samples.sh` | Byte-exact plain conversion vs samples |
| `test_samples_advanced.sh` | Model / advanced comparison |
| `compare_tcx.py` | TCX comparison helper |

Also: `cargo test -p mpowertcx-core`

---

## scripts/ and CI

| File | Purpose |
|------|---------|
| `scripts/build-offline.py` | Inlines CSS/JS/WASM → portable zip in `web/downloads/` |
| `scripts/release.sh` | Release helper |
| `.github/workflows/build-offline.yml` | Tag/manual offline build + release asset |
| `.github/dependabot.yml` | Dependency updates |

---

## legacy/

Unmaintained Python desktop app (reference only).

| Path | Purpose |
|------|---------|
| `source/mpowertcx.py`, `mpower.py` | Conversion entrypoints |
| `source/equipment/` | Original bike parsers (Python) |
| `source/physics/` | Physics model (+ optional Cython) |
| `source/ui/`, `mpowertcxui.py` | PySide2 GUI |
| `source/xml_templates.py` | TCX templates |
| `images/` | Icons/screenshots |
| `INSTRUCTIONS.md` | Old desktop docs |

---

## Where to change what

| Task | Start here |
|------|------------|
| New bike CSV format | `equipment/` + register in `all_parsers()` |
| Interpolation rules | `ride.rs` (`interpolate`, helpers) |
| Speed/distance physics | `physics.rs`, `Ride::model_distance` |
| TCX XML shape | `tcx.rs` |
| Lint rules / codes | `linter.rs` |
| CLI flags | `mpowertcx-cli/src/main.rs` |
| Browser API surface | `mpowertcx-wasm/src/lib.rs` |
| Converter UX | `web/index.html`, `preview-chart.js` |
| Offline portable build | `scripts/build-offline.py` |
| New golden samples | `samples/` + core integration tests |

---

## Skipped from this map

Trivial/config noise (`.gitignore`, lockfile-only noise), binary assets under `legacy/images/`, individual sample filenames, generated `web/pkg/*`, and untracked local install scripts.
