# PLAN: Outstanding-bug fixes (batch 2)

Agreed scope after the FIT export work. Goal: 29/29 on `test_samples.sh`,
valid FIT timestamps for files without embedded dates, and round-trip repair
parity for non-1 Hz rides.

## 1. Black.fit stale golden (DONE, committed with batch 1? no - done now)

`samples/Black.fit.tcx` was generated without `--time`, so it carries the
file's embedded hint (`2026-07-22T15:15:21Z`) while the harness forces
`TEST_TIME`. The `_model` / `_interp` goldens for the same file were already
consistent.

- [x] Regenerate `samples/Black.fit.tcx` with `--time "2010-10-19T20:56:35.450686"`
- [x] Verify `bash tests/test_samples.sh` -> 29 passed, 0 failed

## 2. Hint-less files: valid FIT timestamps (and TCX dates)

Files with no embedded date hint (e.g. the web sample `sample.csv`) currently
fall back to epoch 0 in the wasm. FIT epoch math then drops every timestamp
field, producing a FIT with zero timestamps (likely rejected by
Strava/Garmin). The TCX path shows the same root cause as 1970-01-01 dates.
The CLI is unaffected (mtime fallback).

- [x] `crates/mpowertcx-wasm/src/lib.rs`: fall back to
      `chrono::Local::now().naive_local()` instead of
      `DateTime::from_timestamp(0, 0)` (wasmbind feature already enabled)
- [x] `web/index.html`: remember `file.lastModified` on file read; if
      `result.date_hint` is null, re-run the conversion once with that time
      as `start_time_str` (matches `%Y-%m-%dT%H:%M:%S%.f` parser and the
      CLI's mtime behavior). Sample button keeps the wasm default.
- [x] No goldens affected (tests always pass `--time`)

## 3. Non-1 Hz rides: true session duration in FIT

`fit_out` writes `total_timer_time = (count - 1) * trunc(delta)` (integer
seconds). For 1122.csv (delta 3.218 s -> 3 s) the session timer is 4086 s
instead of 4382.8 s; re-import + repair then integrates physics at delta
2.998 s vs the original 3.218 s, making repaired distance ~7% shorter than
the original repair.

- [x] `fit_out.rs`: keep integer-second record timestamps and `end_secs`, but
      write the source header duration (`header.time`, exact delta recovery
      on re-import) into session/lap `total_elapsed_time` / `total_timer_time`
      (0.001 s resolution in FIT)
- [x] `load_fit` already prefers the session timer; re-import recovers the
      exact delta (header.time / count, error 0% for the session duration)
- [x] Extend `test_fit_roundtrip_repair_parity` with `1122.csv` (non-1 Hz,
      no elevation) at ~1% tolerance
- [x] Regenerate affected `.fit` goldens (fractional-delta sources:
      1122.csv, 1122.csv.tcx, trainerroad_outdoor.txt, Stages; 1 Hz sources
      unchanged)
- [x] `doc/CLI.md`: note session/lap timers carry the true duration while
      record timestamps stay integer-spaced

## 4. Minor: power clamp

- [x] `fit_out.rs`: clamp power to u16 range (`clamp(0.0, 65535.0)`) in
      records and in the avg/max power summary instead of wrapping

## Verification

- [x] `cargo test -p mpowertcx-core` (incl. extended parity test) - 42 passed
- [x] `bash tests/test_samples.sh` -> 40/40 (round-trip goldens added for
      the committed `.fit` sources)
- [x] `bash tests/test_samples_advanced.sh` -> 80/80
- [x] `bash tests/test_samples_fit.sh` -> 10/10
- [x] `wasm-pack build crates/mpowertcx-wasm --target web --out-dir ../../web/pkg`
- [x] clippy clean on touched files (only pre-existing warnings elsewhere)
