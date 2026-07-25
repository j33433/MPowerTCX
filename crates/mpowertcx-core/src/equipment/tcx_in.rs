use crate::ride::{python_float, Ride};
use chrono::NaiveDateTime;
use std::io::{BufReader, Cursor};

/// True when bytes look like a Garmin TCX (TrainingCenterDatabase) document.
pub fn is_tcx(data: &[u8]) -> bool {
    let n = data.len().min(1024);
    let head = String::from_utf8_lossy(&data[..n]);
    head.contains("TrainingCenterDatabase")
}

/// Parse a TCX activity into a Ride from trackpoints (power/cadence/hr/distance).
pub fn load_tcx(data: &[u8], ride: &mut Ride) -> Result<(), String> {
    let mut reader = BufReader::new(Cursor::new(data));
    let db = ::tcx::read(&mut reader).map_err(|e| format!("TCX parse error: {e}"))?;

    let activities = db
        .activities
        .ok_or_else(|| "TCX file has no Activities".to_string())?;
    if activities.activities.is_empty() {
        return Err("TCX file has no Activity elements".into());
    }

    let mut first_ts: Option<NaiveDateTime> = None;
    let mut last_ts: Option<NaiveDateTime> = None;
    let mut lap_timer_sum = 0.0f64;
    let mut max_distance = 0.0f64;
    let mut max_lap_distance = 0.0f64;
    let mut prev_altitude: Option<f64> = None;
    let mut prev_dist_for_alt: f64 = 0.0;

    for activity in &activities.activities {
        if ride.get_date_hint().is_none() {
            if let Some(t) = parse_tcx_time(&activity.id) {
                ride.set_date_hint(t);
            }
        }

        for lap in &activity.laps {
            lap_timer_sum += lap.total_time_seconds;
            if lap.distance_meters > max_lap_distance {
                max_lap_distance = lap.distance_meters;
            }

            for track in &lap.tracks {
                for tp in &track.trackpoints {
                    let ts = tp.time.naive_utc();
                    if first_ts.is_none() {
                        first_ts = Some(ts);
                    }
                    last_ts = Some(ts);

                    let power = tp
                        .extensions
                        .as_ref()
                        .and_then(|e| e.tpx.as_ref())
                        .and_then(|t| t.watts)
                        .unwrap_or(0) as f64;
                    let cadence = tp.cadence.unwrap_or(0) as f64;
                    let hr = tp.heart_rate.as_ref().map(|h| h.value).unwrap_or(0.0);
                    let distance = tp.distance_meters.unwrap_or(0.0);

                    if distance > max_distance {
                        max_distance = distance;
                    }

                    let sample_distance = if distance > 0.0 {
                        distance
                    } else if max_distance > 0.0 {
                        max_distance
                    } else {
                        0.0
                    };

                    ride.add_sample(
                        power as i64,
                        python_float(cadence),
                        python_float(hr),
                        python_float(sample_distance),
                    );

                    if let Some(alt) = tp.altitude_meters {
                        let grade = match (prev_altitude, sample_distance - prev_dist_for_alt) {
                            (Some(prev_alt), d_delta) if d_delta > 0.0 => {
                                ((alt - prev_alt) / d_delta) * 100.0
                            }
                            _ => 0.0,
                        };
                        ride.add_incline(python_float(grade));
                        ride.add_altitude(python_float(alt));
                        prev_altitude = Some(alt);
                        prev_dist_for_alt = sample_distance;
                    } else {
                        ride.add_incline("0");
                        ride.add_altitude("0");
                    }
                }
            }
        }
    }

    if ride.count() == 0 {
        return Err("TCX file had no trackpoints".into());
    }

    if ride.get_date_hint().is_none() {
        if let Some(t) = first_ts {
            ride.set_date_hint(t);
        }
    }

    let span = match (first_ts, last_ts) {
        (Some(a), Some(b)) => (b - a).num_milliseconds() as f64 / 1000.0,
        _ => 0.0,
    };

    let duration = if lap_timer_sum > 0.0 {
        lap_timer_sum
    } else if span > 0.0 {
        span
    } else {
        ride.count() as f64
    };

    ride.infer_header(duration, python_float(duration));
    ride.header.distance = if max_lap_distance > 0.0 {
        max_lap_distance
    } else {
        max_distance
    };

    Ok(())
}

fn parse_tcx_time(s: &str) -> Option<NaiveDateTime> {
    let s = s.trim();
    if let Ok(dt) = chrono::DateTime::parse_from_rfc3339(s) {
        return Some(dt.naive_utc());
    }
    // Activity Id is often "...Z" without offset digits beyond Z.
    let normalized = if s.ends_with('Z') && !s.contains('+') {
        s.to_string()
    } else {
        s.to_string()
    };
    NaiveDateTime::parse_from_str(&normalized, "%Y-%m-%dT%H:%M:%SZ")
        .or_else(|_| NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S"))
        .ok()
}
