# Physics model

The physics model recalculates speed and distance from power output using a
simplified bike model. It is enabled with `--model <MASS_KG>` in the CLI or the
"Repair speed and distance" checkbox in the web UI.

## Model

`SimpleBike` in `crates/mpowertcx-core/src/physics.rs` iterates through each
power sample and updates velocity and distance using:

```
drag = 0.5 × Cd × A × ρ × v²
rolling = g × cos(atan(grade)) × mass × Crr
gravity = g × sin(atan(grade)) × mass
total_force = drag + rolling + gravity
power_needed = total_force × v / η
net_power = power - power_needed
v_new = sqrt(v² + 2 × net_power × Δt × η / mass)
distance += v_new × Δt
```

With constants:

| Symbol | Value | Description |
|---|---|---|
| Cd | 0.88 | Drag coefficient |
| A | 0.32 m² | Frontal area |
| ρ | 1.2 kg/m³ | Air density |
| Crr | 0.005 | Rolling resistance |
| η | 0.97 | Drivetrain efficiency |
| g | 9.81 m/s² | Gravity |

## Grade and elevation

### Two representations

The `Ride` struct carries elevation data in two parallel vectors:

| Field | Content | Populated by |
|---|---|---|
| `incline` | Grade % per sample | All parsers |
| `altitude` | Absolute altitude in meters | FIT, TCX, TrainerRoad |

`incline` is used by the physics model to compute the force needed for climbing.
`altitude` is emitted directly into `<AltitudeMeters>` in the output TCX,
completely independent of the distance values.

This split avoids a circular dependency: if altitude were derived from grade
and distance (as the TCX renderer's fallback path does), then recomputing
distance via the physics model would change the altitude profile. By storing
absolute elevation from the source file, the altitude trace is immune to
distance corrections.

### Fallback

When `altitude` is not available (Stages, Wahoo SYSTM — these formats provide
grade percentages but not absolute elevations), the renderer computes altitude
from the grade and distance data:

```
elev[i] = elev[i-1] + (grade[i] / 100) × (dist[i] - dist[i-1])
```

The FIT output (`render_fit`) deliberately does **not** use this fallback.
FIT altitude resolution is 0.5 m, so the fallback trace would be quantized
into noise. If that noise were re-parsed as real incline on a round trip, the
physics model would apply it and produce wild speed/distance. FIT output
instead writes absolute altitude when present, writes the exact `grade` field
when the source incline is real, and emits neither when the incline is
display-only (simulated). See `doc/CLI.md` for the full FIT round-trip
guarantee.

### Simulated vs. real incline

Some indoor bikes report a grade value that is purely a visual display —
the flywheel does not adjust resistance to match it. On these bikes, the
rider's power goes entirely into flywheel speed regardless of what grade
is shown on screen. Applying the reported grade in the physics model would
unrealistically slow the rider down.

Each parser declares whether its incline data is simulated via `incline_is_simulated()`:

| Equipment | Simulated | Reason |
|---|---|---|
| Stages | Yes | Non-smart flywheel, grade is display-only |
| Echelon V1/V2/V3 | Yes | Same |
| The Sufferfest | Yes | Same |
| Wahoo SYSTM | No | Smart trainer, resistance follows grade |
| TrainerRoad | No | Outdoor GPS elevation or smart trainer |
| FIT | No | Real altitude from device recording |
| TCX | No | Real altitude from device recording |

When `incline_is_simulated` is true, the physics model skips grade entirely
and treats all power as going into speed — matching what the flywheel actually
does.

## Data flow

```
source file
    │
    ▼
parser: extracts power, cadence, hr, distance
        extracts altitude → stored in ride.altitude (absolute, meters)
        extracts altitude → computed to grade → stored in ride.incline (%)
        marks incline_is_simulated if grade is display-only
    │
    ▼
optional interpolation (1 Hz resample, interpolates both altitude and incline)
    │
    ▼
optional physics model (--model):
  if !incline_is_simulated && incline.len() == sample_count:
    sets bike.grade = incline[i] / 100 before each next_sample()
  recomputes self.distance from power
  self.altitude is NOT touched (absolute values from source)
    │
    ▼
TCX renderer:
  if altitude.len() == sample_count:
    emit altitude[i] directly → <AltitudeMeters>
  else if incline.len() == sample_count:
    emit computed elevation from grade × distance → <AltitudeMeters>
```

## Example files

### `samples/2021_09_15_11_09_Get_STRONG_Torque_Workout_2.csv`

Stages CSV with 9 columns including an `Incline` column (col 8).
Grade ranges from -1% to 10% (mean 4%) across 12 distinct values. This is
the richest elevation dataset in the sample set.

Parsed as `Stages` → `incline_is_simulated = true` → physics model skips grade.
The renderer has no `altitude` vec (Stages only stores `incline`), so it
computes altitude from grade × distance:

```
elev[i] = elev[i-1] + (grade[i] / 100) × (dist[i] - dist[i-1])
```

This exposes the circularity: the physics model rewrites distance, so the
same grade values produce different altitude depending on whether physics ran:

| Reference output | Altitude range | Distance source |
|---|---|---|
| plain `.tcx` | 0.0 to 428.9m | Original from file |
| `_model.tcx` | 0.0 to **560.5m** (+31%) | Physics-model |

For a non-smart bike the grade is a display value — the flywheel speed doesn't
respond to it — so the altitude difference is cosmetic. But it's a clear
demonstration of the circularity that the `altitude`/`incline` split solves for
FIT, TCX, and TrainerRoad.

### `samples/trainerroad_outdoor.txt`

40 type-2 sample rows with an `elev` column carrying absolute altitude in
meters (4.0 to 4.4m, 3 unique values). The parser populates both `altitude`
(absolute) and `incline` (computed grade, -4.4% to +4.4%). `incline_is_simulated`
is `false`. The renderer emits `altitude` directly — the elevation trace is
immune to distance recomputation.

### `samples/wahoo_systm_activity.csv`

Wahoo SYSTM export with a `grade` column (0 to 0.1%, mean
0.035%). `incline` populated but not `altitude` (no absolute elevation in
the source). The physics model applies grade; the renderer falls back to
grade × distance. Tiny grades → 0.4% distance delta with the model.
