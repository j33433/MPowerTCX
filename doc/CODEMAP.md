# CODEMAP

Map of the MPowerTCX codebase: indoor-bike CSV &rarr; TCX for Strava/Garmin/etc.
Rust workspace (v2.1.0), browser WASM frontend at [upload.bike](https://upload.bike).

```
CSV / FIT / TCX bytes
  &rarr; equipment parsers (BikeParser trait) + FIT/TCX readers
  &rarr; Ride (samples + header)
  &rarr; optional interpolate / physics model
  &rarr; TCX XML (render_tcx) or FIT bytes (render_fit)
  &rarr; optional lint_tcx
```

## Workspace layout

| Path | Role |
|------|------|
| [`Cargo.toml`](../Cargo.toml) | Workspace: core, cli, wasm; version/edition/license |
| [`crates/mpowertcx-core/`](../crates/mpowertcx-core/) | Conversion library (no I/O, WASM-safe) |
| [`crates/mpowertcx-cli/`](../crates/mpowertcx-cli/) | CLI binary `mpowertcx` |
| [`crates/mpowertcx-wasm/`](../crates/mpowertcx-wasm/) | `wasm-bindgen` bindings for the web UI |
| [`web/`](../web/) | Static site (converter, docs, offline zip) |
| [`samples/`](../samples/) | Fixture CSVs + expected TCX (plain / `_interp` / `_model`) |
| [`tests/`](../tests/) | Shell + Python golden-file comparison |
| [`scripts/`](../scripts/) | Offline build, release helpers |
| [`.github/workflows/`](../.github/workflows/) | CI (offline zip / releases) |

---

## crates/mpowertcx-core

Library: parse CSV, build ride, interpolate, physics model, emit TCX, lint TCX.

| File | Purpose |
|------|---------|
| [`src/lib.rs`](../crates/mpowertcx-core/src/lib.rs) | Module exports; `VERSION` |
| [`src/converter.rs`](../crates/mpowertcx-core/src/converter.rs) | Orchestration: detect parser, convert with options |
| [`src/ride.rs`](../crates/mpowertcx-core/src/ride.rs) | `Ride` / `RideHeader`; interpolate; physics distance |
| [`src/tcx.rs`](../crates/mpowertcx-core/src/tcx.rs) | `render_tcx` &rarr; Garmin TCX XML |
| [`src/fit_out.rs`](../crates/mpowertcx-core/src/fit_out.rs) | `render_fit` &rarr; Garmin FIT activity file (absolute altitude only; exact `grade` for real-incline equipment) |
| [`src/physics.rs`](../crates/mpowertcx-core/src/physics.rs) | `SimpleBike` power &rarr; speed/distance model |
| [`src/linter.rs`](../crates/mpowertcx-core/src/linter.rs) | TCX structural + plausibility checks (E/W codes) |
| [`src/equipment/mod.rs`](../crates/mpowertcx-core/src/equipment/mod.rs) | `BikeParser`, `CsvRows`, `all_parsers()`, unit helpers |
| [`src/equipment/echelon.rs`](../crates/mpowertcx-core/src/equipment/echelon.rs) | Schwinn MPower Echelon V1/V2/V3 |
| [`src/equipment/stages.rs`](../crates/mpowertcx-core/src/equipment/stages.rs) | Stages Indoor Cycles |
| [`src/equipment/systm.rs`](../crates/mpowertcx-core/src/equipment/systm.rs) | Wahoo SYSTM |
| [`src/equipment/thesufferfest.rs`](../crates/mpowertcx-core/src/equipment/thesufferfest.rs) | The Sufferfest |
| [`src/equipment/trainerroad.rs`](../crates/mpowertcx-core/src/equipment/trainerroad.rs) | TrainerRoad TSV `.txt` from WorkoutRecords |
| [`src/equipment/fit.rs`](../crates/mpowertcx-core/src/equipment/fit.rs) | FIT file reader (binary .fit from bike computers) |
| [`src/equipment/tcx_in.rs`](../crates/mpowertcx-core/src/equipment/tcx_in.rs) | TCX file reader (round-trip re-conversion) |
| [`tests/integration.rs`](../crates/mpowertcx-core/tests/integration.rs) | Sample-based conversion tests |
| [`tests/linter_tests.rs`](../crates/mpowertcx-core/tests/linter_tests.rs) | Linter unit tests |

### Data flow (core)

1. `Converter::from_csv(bytes)` &rarr; `CsvRows` + try each `BikeParser` in order
2. Parser fills `Ride` (power/rpm/hr/distance series + header)
3. `Converter::convert(start_time, ConvertOptions)`:
   - optional `Ride::interpolate()` (1 Hz linear)
   - optional `Ride::model_distance(mass)` via `SimpleBike`
   - `render_tcx` with optional power adjust, or `convert_fit` &rarr; `render_fit`
4. Callers may run `lint_tcx` on the XML

### Parser order (`all_parsers`)

1. TheSufferfest
2. EchelonV1, EchelonV2, EchelonV3
3. Systm
4. TrainerRoad
5. Stages (fallback / broad CSV shapes)

### Key types

| Symbol | Location | Notes |
|--------|----------|--------|
| `ConvertOptions` | [`converter.rs`](../crates/mpowertcx-core/src/converter.rs) | `interpolate`, `physics`, `physics_mass_kg`, `power_adjust_percent` |
| `Converter` | [`converter.rs`](../crates/mpowertcx-core/src/converter.rs) | `from_csv`, `convert`, `convert_fit`, `date_hint`, `equipment_name` |
| `Ride` / `RideHeader` | [`ride.rs`](../crates/mpowertcx-core/src/ride.rs) | Sample vectors as strings (legacy float formatting) |
| `BikeParser` | [`equipment/mod.rs`](../crates/mpowertcx-core/src/equipment/mod.rs) | `try_load`, `name` |
| `CsvRows` | [`equipment/mod.rs`](../crates/mpowertcx-core/src/equipment/mod.rs) | Null-stripped, line-normalized CSV walk |
| `SimpleBike` | [`physics.rs`](../crates/mpowertcx-core/src/physics.rs) | `next_sample(power) &rarr; (speed, distance, time)` |
| `render_fit` | [`fit_out.rs`](../crates/mpowertcx-core/src/fit_out.rs) | Ride &rarr; FIT bytes (file_id/activity/session/lap/records) |
| `lint_tcx` / `has_errors` | [`linter.rs`](../crates/mpowertcx-core/src/linter.rs) | Errors E001&ndash;E036 fail; warnings W013&ndash;W038 informational |

Deps: `csv`, `chrono`, `quick-xml`, `rustyfit` + `embedded-io` (FIT read and write), `tcx` (TCX read).

---

## crates/mpowertcx-cli

Thin CLI over core. Binary name: `mpowertcx`.

| File | Purpose |
|------|---------|
| [`src/main.rs`](../crates/mpowertcx-cli/src/main.rs) | Arg parse; convert CSV&rarr;TCX or `--lint` TCX |

Flags: `--csv`, `--tcx`, `--fit`, `--time`, `--interpolate`, `--model <MASS_KG>`, `--lint`.

For the full CLI reference see [CLI.md](CLI.md).

---

## crates/mpowertcx-wasm

Browser API over core.

| File | Purpose |
|------|---------|
| [`src/lib.rs`](../crates/mpowertcx-wasm/src/lib.rs) | `convert_csv_to_tcx`, `get_sample_csv`, `ConvertResult` |

- Embeds `web/samples/1122.csv` for chart demos
- Returns TCX string, FIT bytes, equipment name, sample count, date hint, debug, lint error count
- Built with:  
  `wasm-pack build crates/mpowertcx-wasm --target web --out-dir ../../web/pkg`

---

## web/

Client-only site. Processing is WASM in the browser.

| File | Purpose |
|------|---------|
| [`index.html`](../web/index.html) | Converter UI |
| [`how-it-works.html`](../web/how-it-works.html) | About + interactive physics chart |
| [`download.html`](../web/download.html) | Offline zip download page |
| [`custom.css`](../web/custom.css) | Pico CSS extensions |
| [`theme.js`](../web/theme.js) | Light/dark toggle |
| [`preview-chart.js`](../web/preview-chart.js) | Workout preview chart (ES module) |
| [`chart-demo.js`](../web/chart-demo.js) | Physics model chart engine (ES module) |
| [`icon.svg`](../web/icon.svg), [`favicon.ico`](../web/favicon.ico) | Branding |
| `pkg/` | Generated wasm-pack output (do not hand-edit) |
| [`samples/`](../web/samples/) | CSVs bundled for demos |
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
| `.fit` / `_interp.fit` | FIT output (byte-exact, plain / interpolated) |

Covers Echelon, Stages, Sufferfest, SYSTM, edge cases (nulls, missing headers, empty).

---

## tests/

| File | Purpose |
|------|---------|
| [`test_samples.sh`](../tests/test_samples.sh) | Byte-exact plain conversion vs samples |
| [`test_samples_advanced.sh`](../tests/test_samples_advanced.sh) | Model / advanced comparison |
| [`test_samples_fit.sh`](../tests/test_samples_fit.sh) | Byte-exact FIT output vs samples |
| [`compare_tcx.py`](../tests/compare_tcx.py) | TCX comparison helper |

Also: `cargo test -p mpowertcx-core`

---

## scripts/ and CI

| File | Purpose |
|------|---------|
| [`scripts/build-offline.py`](../scripts/build-offline.py) | Inlines CSS/JS/WASM &rarr; portable zip in `web/downloads/` |
| [`scripts/release.sh`](../scripts/release.sh) | Release helper |
| [`.github/workflows/build-offline.yml`](../.github/workflows/build-offline.yml) | Tag/manual offline build + release asset |
| [`.github/dependabot.yml`](../.github/dependabot.yml) | Dependency updates |

---

## Where to change what

| Task | Start here |
|------|------------|
| New bike CSV format | [`equipment/`](../crates/mpowertcx-core/src/equipment/) + register in `all_parsers()` |
| Interpolation rules | [`ride.rs`](../crates/mpowertcx-core/src/ride.rs) (`interpolate`, helpers) |
| Speed/distance physics | [`physics.rs`](../crates/mpowertcx-core/src/physics.rs), `Ride::model_distance` |
| TCX XML shape | [`tcx.rs`](../crates/mpowertcx-core/src/tcx.rs) |
| FIT output | [`fit_out.rs`](../crates/mpowertcx-core/src/fit_out.rs) |
| Lint rules / codes | [`linter.rs`](../crates/mpowertcx-core/src/linter.rs) |
| CLI flags | [`mpowertcx-cli/src/main.rs`](../crates/mpowertcx-cli/src/main.rs) |
| Browser API surface | [`mpowertcx-wasm/src/lib.rs`](../crates/mpowertcx-wasm/src/lib.rs) |
| Converter UX | [`web/index.html`](../web/index.html), [`preview-chart.js`](../web/preview-chart.js) |
| Offline portable build | [`scripts/build-offline.py`](../scripts/build-offline.py) |
| New golden samples | [`samples/`](../samples/) + core integration tests |

---

## Skipped from this map

Trivial/config noise (`.gitignore`, lockfile-only noise), individual sample filenames, generated `web/pkg/*`, and untracked local install scripts.

Historical Python/PySide2 desktop app: tag `legacy-python` at
<https://github.com/j33433/MPowerTCX/tree/legacy-python/legacy>
