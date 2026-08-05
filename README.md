# MPowerTCX

Convert CSV files from indoor cycling bikes to TCX or FIT format for Strava,
Garmin Connect, TrainingPeaks, and Golden Cheetah. All processing runs in the
browser via WebAssembly, no server needed.

Try it live at [upload.bike](https://upload.bike).

If the site is down, download the standalone build from the
[latest release](https://github.com/j33433/MPowerTCX/releases).
Unzip and open `index.html` in any browser.

## Supported equipment

- Schwinn MPower Echelon (3 firmware variants)
- Stages Indoor Cycles
- The Sufferfest
- Wahoo SYSTM
- NordicTrack Studio Cycles
- PRO-FORM iFit

Don't see your bike? Email your CSV to upload.bike@gmail.com.

## Quick start (CLI)

```
cargo build --release
./target/release/mpowertcx --csv workout.csv --tcx workout.tcx
./target/release/mpowertcx --csv workout.csv --fit workout.fit
```

## Documentation

| File | Covers |
|------|--------|
| [doc/CLI.md](doc/CLI.md) | CLI usage, flags, input formats, interpolation, physics model, linter codes, examples |
| [doc/PHYSICS.md](doc/PHYSICS.md) | Physics model equations, grade/altitude handling, simulated incline |
| [doc/CODEMAP.md](doc/CODEMAP.md) | Codebase map, workspace layout, file listing, task guide |

## Tests

```
cargo test -p mpowertcx-core
bash tests/test_samples.sh
bash tests/test_samples_advanced.sh
bash tests/test_samples_fit.sh
```

## License

GPL-3.0
