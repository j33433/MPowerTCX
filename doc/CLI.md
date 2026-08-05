# CLI

`mpowertcx` is the command-line binary that converts indoor-bike CSV files to
Garmin TCX XML or FIT files. It lives in `crates/mpowertcx-cli/` and delegates
all conversion logic to `mpowertcx-core`.

## Installation

Build from source:

```
cargo build --release
```

The binary lands at `target/release/mpowertcx`. Copy it anywhere on `$PATH`.

There is no prebuilt CLI binary distributed at this time. The only release
artifact is the offline web zip (`upload.bike-portable.zip`).

## Modes

The CLI has two modes: **convert** and **lint**.

### Convert mode

Reads a bike CSV (or FIT/TCX) and writes a Garmin TCX and/or FIT file:

```
mpowertcx --csv input.csv --tcx output.tcx [OPTIONS]
mpowertcx --csv input.csv --fit output.fit [OPTIONS]
```

`--csv` is required, and at least one of `--tcx` or `--fit` must be given.

### Lint mode

Checks an existing TCX file for structural problems and implausible values:

```
mpowertcx --lint file.tcx
```

See [Linter](#linter) for the full list of checks.

## Options

| Flag | Value | Description |
|------|-------|-------------|
| `--csv` | `<FILE>` | Input file (CSV, FIT, or TCX) |
| `--tcx` | `<FILE>` | Output TCX file |
| `--fit` | `<FILE>` | Output FIT file (see [Output format](#output-format)) |
| `--time` | `<TIME>` | Workout start time (see [Time formats](#time-formats)) |
| `--interpolate` | *(flag)* | Resample to 1-second intervals (see [Interpolation](#interpolation)) |
| `--model` | `<MASS_KG>` | Recompute speed/distance from power using the physics model |
| `--lint` | `<FILE>` | Lint a TCX file; exit 1 if errors found |
| `--help`, `-h` | *(flag)* | Print usage and exit |

## Time formats

`--time` accepts these formats. If omitted, the CLI tries the file's
embedded date hint, then falls back to the file's modification time.

| Format | Example |
|--------|---------|
| `%Y-%m-%dT%H:%M:%S%.f` | `2025-03-12T08:30:00.000` |
| `%Y-%m-%dT%H:%M:%S` | `2025-03-12T08:30:00` |
| `%Y-%m-%d %H:%M:%S%.f` | `2025-03-12 08:30:00.000` |
| `%Y-%m-%d %H:%M:%S` | `2025-03-12 08:30:00` |
| `%Y-%m-%d %H:%M` | `2025-03-12 08:30` |
| `%Y/%m/%d %H:%M:%S` | `2025/03/12 08:30:00` |
| `%Y/%m/%d %H:%M` | `2025/03/12 08:30` |
| Unix timestamp (integer) | `1736183400` |

All times are treated as local time.

## Input formats

The CLI reads CSV, TSV, FIT, and TCX files. Detection is automatic;
no flag is needed to select the parser. Detection order:

| Priority | Parser | Equipment / app |
|----------|--------|-----------------|
| 1 | FIT | Binary `.fit` from bike computers, smart trainers |
| 2 | TCX | Garmin TCX XML (round-trip re-conversion) |
| 3 | TheSufferfest | The Sufferfest |
| 4 | EchelonV1 | Schwinn MPower Echelon (firmware v1) |
| 5 | EchelonV2 | Schwinn MPower Echelon (firmware v2) |
| 6 | EchelonV3 | Schwinn MPower Echelon (firmware v3) |
| 7 | Systm | Wahoo SYSTM |
| 8 | TrainerRoad | TrainerRoad TSV (.txt from WorkoutRecords) |
| 9 | Stages | Stages Indoor Cycles (also matches NordicTrack, PRO-FORM) |

FIT is detected by FIT header magic. TCX is detected by scanning for the
`<TrainingCenterDatabase` element. CSV and TSV files use the remaining
parsers in order; null bytes are silently stripped and the delimiter
(tab or comma) is auto-detected from the first 20 lines.

## Interpolation

`--interpolate` resamples source data to 1-second intervals using linear
interpolation:

- Power, RPM, HR, and distance are interpolated to exactly one sample per
  second, matching the workout duration.
- Linear interpolation never overshoots the source min/max values.
- Power and RPM are clamped to >= 0.
- HR zeros are forward-filled before interpolation (dropouts carry the last
  non-zero value).
- Distance is kept monotonic (if interpolation produces a backward step, it
  is flattened forward).
- Incline and altitude are also interpolated when present. If the vector
  length does not match power, they are cleared instead of producing
  misaligned output.

## Physics model

`--model <MASS_KG>` recomputes speed and distance from power output using a
simplified bike model (`SimpleBike` in `crates/mpowertcx-core/src/physics.rs`).
Mass is the combined rider+bike weight in kilograms (e.g. `--model 85`).

Applying the model:

- Iterates through each power sample.
- Computes drag, rolling resistance, and gravity.
- Derives speed and cumulative distance via Newtonian acceleration.
- Skips grade if the equipment parser reports `incline_is_simulated`
  (Echelon, Stages, Sufferfest). On those non-smart flywheels, grade is a
  display value only and the power goes entirely into flywheel speed.
- When grade is applied (SYSTM, TrainerRoad, FIT, TCX input), altitude is
  unaffected: absolute altitude from the source file is emitted directly
  into `<AltitudeMeters>`, independent of the recomputed distance.

See `doc/PHYSICS.md` for the full model, constants, and grade/altitude
interaction.

## Output format

The CLI writes a single-file Garmin TCX v2 XML document with one Activity
containing one Lap:

```
<?xml version='1.0' encoding='utf-8'?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" ...>
  <Activities>
    <Activity Sport="Biking">
      <Id>...</Id>
      <Lap StartTime="...">
        <TotalTimeSeconds>...</TotalTimeSeconds>
        <DistanceMeters>...</DistanceMeters>
        <MaximumSpeed>0</MaximumSpeed>
        <Calories>0</Calories>
        <AverageHeartRateBpm>...</AverageHeartRateBpm>
        <MaximumHeartRateBpm>...</MaximumHeartRateBpm>
        <Intensity>Active</Intensity>
        <Cadence>0</Cadence>
        <TriggerMethod>Manual</TriggerMethod>
        <Track>
          <Trackpoint>
            <Time>...</Time>
            <AltitudeMeters>...</AltitudeMeters>
            <HeartRateBpm>
              <Value>...</Value>
            </HeartRateBpm>
            <Cadence>...</Cadence>
            <DistanceMeters>...</DistanceMeters>
            <Extensions>
              <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
                <Watts>...</Watts>
              </TPX>
            </Extensions>
          </Trackpoint>
          ...
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>
```

Each trackpoint carries time, altitude (if available), HR, cadence,
cumulative distance, and watts (via Garmin extension TPX namespace).

### FIT output

`--fit <FILE>` writes a Garmin FIT activity file (protocol v1, little-endian,
CRC-16) using the same underlying ride data as the TCX path:

- `file_id` (type activity, manufacturer Garmin), then `activity`, `session`,
  and `lap` messages with workout totals, then one `record` message per sample.
- Record fields: timestamp, power (watts), cadence (rpm), heart rate (bpm),
  distance (m, 0.01 m resolution), speed derived from distance deltas, and
  altitude when the source carries absolute elevation (0.5 m resolution).
- Elevation policy: only absolute altitude from the source file is emitted.
  The grade x distance fallback that the TCX renderer uses is intentionally
  not written, because FIT altitude resolution (0.5 m) would quantize it into
  noise, and re-parsing that noise as real incline makes the physics model
  produce wild speed/distance on a round trip.
- Grade: when the source incline is real (SYSTM, TrainerRoad, FIT, TCX input),
  it is written verbatim as the record `grade` field (0.01% resolution). When
  the incline is display-only (Echelon, Stages, Sufferfest), neither altitude
  nor grade is emitted.
- Timestamps follow the same convention as the TCX renderer: samples are
  spaced `max(delta, 1)` seconds from the start time. FIT stores UTC epochs
  and the source times carry no timezone, so local time is treated as UTC
  (the same ambiguity the TCX output has).
- Session/lap `total_elapsed_time` / `total_timer_time` carry the source
  header duration (the exact `header.time`, 0.001 s resolution) while record
  timestamps stay integer-spaced, so a re-import recovers the original sample
  delta exactly (`header.time / count`) even for non-1 Hz rides.
- The same options apply: `--interpolate` and `--model <MASS_KG>` shape the
  records exactly as they shape TCX trackpoints.

Because of this, re-importing a downloaded FIT and applying the physics model
reproduces the repair on the original file: simulated-incline rides skip grade
in both passes, and real-incline rides apply the same exact grade in both
passes.

The FIT encoder lives in `crates/mpowertcx-core/src/fit_out.rs` and uses the
[`rustyfit`](https://crates.io/crates/rustyfit) crate (BSD-3-Clause). Note that
rustyfit's README carries an ANT+/Garmin FIT Protocol license notice; the same
regime already applies to reading FIT files with `fitparser`.

## STDERR output

On success the CLI prints to stderr, once per output file written:

```
Converted input.csv -> output.tcx (3600 samples, Stages)
```

Format: `<input path> -> <output path> (<sample count> samples, <equipment name>)`.

## Exit codes

| Code | Condition |
|------|-----------|
| 0 | Conversion succeeded, or lint with no errors |
| 1 | Conversion failed, unrecognized arguments, or lint with errors |

## Linter

`--lint <FILE>` runs structural and data-quality checks on a TCX file.
Results are printed to stdout in tabular format:

```
ERROR  E030  Watts is negative: -5   [Activity #0, Lap #0, Trackpoint #12]
WARN   W022  Irregular time interval: 4s (median 1s) between trackpoints #3 and #4  [Trackpoint #4]
```

Summary (error/warning count) prints to stderr.

### Error codes (exit 1)

| Code | Check |
|------|-------|
| E001 | XML parse failed |
| E002 | Root element is not TrainingCenterDatabase with TCXv2 namespace |
| E003 | No Activity element, or Activity has no Sport attribute |
| E004 | No Lap element, or Lap has no StartTime attribute |
| E005 | Activity Id missing or not a valid ISO 8601 datetime |
| E006 | TotalTimeSeconds missing, not numeric, or negative |
| E007 | Lap DistanceMeters missing, not numeric, or negative |
| E008 | No Track element found in Lap |
| E009 | Trackpoint missing required field (Time, Cadence, DistanceMeters, or Watts) |
| E010 | Trackpoint time went backwards (not monotonically increasing) |
| E012 | Lap StartTime does not match Activity Id |
| E030 | Watts is negative |
| E034 | Power applied (> 0 W) but distance reversed |
| E035 | Distance went backwards between consecutive trackpoints |
| E036 | DistanceMeters is negative |

### Warning codes (exit 0)

| Code | Check |
|------|-------|
| W013 | First trackpoint Time does not match Lap StartTime |
| W014 | TotalTimeSeconds spans more than 1 median-interval from trackpoint times |
| W015 | Lap DistanceMeters differs from final trackpoint distance by > 1% |
| W016 | AverageHeartRateBpm > MaximumHeartRateBpm in lap summary |
| W017 | HeartRate exceeds 220 bpm |
| W018 | Cadence outside 0-200 rpm |
| W019 | Watts exceeds 2500 |
| W020 | All values zero (HR=0, Cadence=0, Watts=0) |
| W022 | Irregular time interval (deviation > 50% from median) |
| W023 | Track is empty but TotalTimeSeconds > 0 |
| W032 | Power whipsaw > 100 W/s between consecutive trackpoints |
| W033 | Power applied (> 0 W) but distance unchanged |
| W037 | DistanceMeters has negative-zero format (e.g. `-0.00`) |
| W038 | Implausible HR change (> 10 bpm/s) between consecutive trackpoints |

## Examples

Basic conversion using the file's timestamp:

```
mpowertcx --csv workout.csv --tcx workout.tcx
```

Specify a time and interpolate to 1-second trackpoints:

```
mpowertcx --csv workout.csv --tcx workout.tcx --time "2025-03-12 08:30" --interpolate
```

Write a FIT file instead of (or alongside) TCX:

```
mpowertcx --csv workout.csv --fit workout.fit
mpowertcx --csv workout.csv --tcx workout.tcx --fit workout.fit --interpolate
```

Recompute distance from power (85 kg rider+bike):

```
mpowertcx --csv workout.csv --tcx workout.tcx --model 85
```

Interpolate with the physics model:

```
mpowertcx --csv workout.csv --tcx workout.tcx --interpolate --model 85
```

Convert a FIT file:

```
mpowertcx --csv ride.fit --tcx ride.tcx
```

Lint a TCX file:

```
mpowertcx --lint output.tcx
```

Re-process an existing TCX (round-trip):

```
mpowertcx --csv original.tcx --tcx reprocessed.tcx --interpolate
```
