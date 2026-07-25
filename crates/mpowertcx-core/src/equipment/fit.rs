use crate::ride::{python_float, Ride};
use chrono::{DateTime, NaiveDateTime};
use fitparser::profile::MesgNum;
use fitparser::Value;

/// True when bytes look like a Garmin/ANT FIT file (".FIT" signature at offset 8).
pub fn is_fit(data: &[u8]) -> bool {
    data.len() >= 12 && &data[8..12] == b".FIT"
}

/// Parse a FIT activity into a Ride. Expects record messages with power/cadence/hr/distance.
pub fn load_fit(data: &[u8], ride: &mut Ride) -> Result<(), String> {
    let records = fitparser::from_bytes(data).map_err(|e| format!("FIT parse error: {e}"))?;

    let mut first_ts: Option<NaiveDateTime> = None;
    let mut last_ts: Option<NaiveDateTime> = None;
    let mut session_timer: Option<f64> = None;
    let mut session_distance: Option<f64> = None;
    let mut max_distance = 0.0f64;
    let mut prev_altitude: Option<f64> = None;
    let mut prev_dist_for_alt: f64 = 0.0;

    for rec in &records {
        match rec.kind() {
            MesgNum::Record => {
                let mut power = 0.0f64;
                let mut cadence = 0.0f64;
                let mut hr = 0.0f64;
                let mut distance = 0.0f64;
                let mut has_metrics = false;
                let mut ts: Option<NaiveDateTime> = None;
                let mut altitude: Option<f64> = None;

                for field in rec.fields() {
                    match field.name() {
                        "timestamp" => {
                            if let Some(t) = value_timestamp(field.value()) {
                                ts = Some(t);
                            }
                        }
                        "power" => {
                            if let Some(v) = value_f64(field.value()) {
                                power = v;
                                has_metrics = true;
                            }
                        }
                        "cadence" => {
                            if let Some(v) = value_f64(field.value()) {
                                cadence = v;
                                has_metrics = true;
                            }
                        }
                        "heart_rate" => {
                            if let Some(v) = value_f64(field.value()) {
                                hr = v;
                                has_metrics = true;
                            }
                        }
                        "distance" => {
                            if let Some(v) = value_f64(field.value()) {
                                distance = v;
                                has_metrics = true;
                            }
                        }
                        "altitude" | "enhanced_altitude" => {
                            if altitude.is_none() {
                                altitude = value_f64(field.value());
                            }
                        }
                        _ => {}
                    }
                }

                if !has_metrics {
                    continue;
                }

                if let Some(t) = ts {
                    if first_ts.is_none() {
                        first_ts = Some(t);
                    }
                    last_ts = Some(t);
                }

                if distance > max_distance {
                    max_distance = distance;
                }

                // Carry forward last known distance when a sample omits/resets it.
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

                if let Some(alt) = altitude {
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
            MesgNum::Session => {
                for field in rec.fields() {
                    match field.name() {
                        "start_time" => {
                            if ride.get_date_hint().is_none() {
                                if let Some(t) = value_timestamp(field.value()) {
                                    ride.set_date_hint(t);
                                }
                            }
                        }
                        "total_timer_time" => {
                            if let Some(v) = value_f64(field.value()) {
                                session_timer = Some(v);
                            }
                        }
                        "total_distance" => {
                            if let Some(v) = value_f64(field.value()) {
                                session_distance = Some(v);
                            }
                        }
                        _ => {}
                    }
                }
            }
            MesgNum::Activity => {
                for field in rec.fields() {
                    if field.name() == "timestamp" || field.name() == "local_timestamp" {
                        if ride.get_date_hint().is_none() {
                            if let Some(t) = value_timestamp(field.value()) {
                                ride.set_date_hint(t);
                            }
                        }
                    }
                }
            }
            _ => {}
        }
    }

    if ride.count() == 0 {
        return Err("FIT file had no record samples".into());
    }

    if ride.get_date_hint().is_none() {
        if let Some(t) = first_ts {
            ride.set_date_hint(t);
        }
    }

    let duration = session_timer.unwrap_or_else(|| match (first_ts, last_ts) {
        (Some(a), Some(b)) => (b - a).num_milliseconds() as f64 / 1000.0,
        _ => ride.count() as f64,
    });

    // Prefer last sample timestamp span when session timer is missing or zero.
    let duration = if duration > 0.0 {
        duration
    } else {
        ride.count() as f64
    };

    ride.infer_header(duration, python_float(duration));
    ride.header.distance = session_distance.unwrap_or(max_distance);

    Ok(())
}

fn value_f64(v: &Value) -> Option<f64> {
    match v {
        Value::Invalid => None,
        other => other.clone().try_into().ok(),
    }
}

fn value_timestamp(v: &Value) -> Option<NaiveDateTime> {
    match v {
        Value::Timestamp(dt) => Some(dt.naive_utc()),
        _ => {
            // Some decoders leave raw seconds; convert FIT epoch if numeric.
            let secs: i64 = v.clone().try_into().ok()?;
            fit_epoch_to_naive(secs)
        }
    }
}

fn fit_epoch_to_naive(secs: i64) -> Option<NaiveDateTime> {
    // FIT timestamps < 0x10000000 are device-relative, not absolute.
    if secs < 0x1000_0000 {
        return None;
    }
    // FIT epoch is 1989-12-31 00:00:00 UTC
    let base = DateTime::parse_from_rfc3339("1989-12-31T00:00:00Z")
        .ok()?
        .naive_utc();
    base.checked_add_signed(chrono::Duration::seconds(secs))
}
