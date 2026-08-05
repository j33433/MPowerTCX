use crate::ride::{python_float, Ride};
use chrono::{DateTime, NaiveDateTime};
use rustyfit::profile::{mesgdef, typedef};

/// True when bytes look like a Garmin/ANT FIT file (".FIT" signature at offset 8).
pub fn is_fit(data: &[u8]) -> bool {
    data.len() >= 12 && &data[8..12] == b".FIT"
}

/// Parse a FIT activity into a Ride. Expects record messages with power/cadence/hr/distance.
pub fn load_fit(data: &[u8], ride: &mut Ride) -> Result<(), String> {
    let mut decoder = rustyfit::Decoder::new();
    let mut reader: &[u8] = data;
    let fit = decoder
        .decode(&mut reader)
        .map_err(|e| format!("FIT parse error: {e}"))?;
    let records = fit.map(|f| f.messages).unwrap_or_default();

    let mut first_ts: Option<NaiveDateTime> = None;
    let mut last_ts: Option<NaiveDateTime> = None;
    let mut session_timer: Option<f64> = None;
    let mut session_distance: Option<f64> = None;
    let mut max_distance = 0.0f64;
    let mut prev_altitude: Option<f64> = None;
    let mut prev_dist_for_alt: f64 = 0.0;

    for mesg in &records {
        match mesg.num {
            typedef::MesgNum::RECORD => {
                let rec = mesgdef::Record::from(mesg);

                let mut power = 0.0f64;
                let mut cadence = 0.0f64;
                let mut hr = 0.0f64;
                let mut distance = 0.0f64;
                let mut has_metrics = false;
                let mut ts: Option<NaiveDateTime> = None;
                let altitude = rec
                    .altitude_scaled()
                    .or_else(|| rec.enhanced_altitude_scaled());
                let grade = rec.grade_scaled();

                if rec.power != u16::MAX {
                    power = rec.power as f64;
                    has_metrics = true;
                }
                if rec.cadence != u8::MAX {
                    cadence = rec.cadence as f64;
                    has_metrics = true;
                }
                if rec.heart_rate != u8::MAX {
                    hr = rec.heart_rate as f64;
                    has_metrics = true;
                }
                if let Some(d) = rec.distance_scaled() {
                    distance = d;
                    has_metrics = true;
                }
                if rec.timestamp.0 != u32::MAX {
                    ts = fit_epoch_to_naive(rec.timestamp.0);
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

                if let Some(g) = grade {
                    // Exact grade written by MPowerTCX; prefer it over the
                    // coarse altitude-derived estimate below.
                    ride.add_incline(python_float(g));
                } else if let Some(alt) = altitude {
                    let g = match (prev_altitude, sample_distance - prev_dist_for_alt) {
                        (Some(prev_alt), d_delta) if d_delta > 0.0 => {
                            ((alt - prev_alt) / d_delta) * 100.0
                        }
                        _ => 0.0,
                    };
                    ride.add_incline(python_float(g));
                } else {
                    ride.add_incline("0");
                }

                if let Some(alt) = altitude {
                    ride.add_altitude(python_float(alt));
                    prev_altitude = Some(alt);
                    prev_dist_for_alt = sample_distance;
                } else {
                    ride.add_altitude("0");
                }
            }
            typedef::MesgNum::SESSION => {
                let ses = mesgdef::Session::from(mesg);
                if ride.get_date_hint().is_none() && ses.start_time.0 != u32::MAX {
                    if let Some(t) = fit_epoch_to_naive(ses.start_time.0) {
                        ride.set_date_hint(t);
                    }
                }
                if let Some(v) = ses.total_timer_time_scaled() {
                    session_timer = Some(v);
                }
                if let Some(v) = ses.total_distance_scaled() {
                    session_distance = Some(v);
                }
            }
            typedef::MesgNum::ACTIVITY => {
                let act = mesgdef::Activity::from(mesg);
                if ride.get_date_hint().is_none() {
                    if act.timestamp.0 != u32::MAX {
                        if let Some(t) = fit_epoch_to_naive(act.timestamp.0) {
                            ride.set_date_hint(t);
                        }
                    } else if act.local_timestamp.0 != u32::MAX {
                        if let Some(t) = fit_epoch_to_naive(act.local_timestamp.0) {
                            ride.set_date_hint(t);
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

fn fit_epoch_to_naive(secs: u32) -> Option<NaiveDateTime> {
    // FIT timestamps < 0x10000000 are device-relative, not absolute.
    if secs < 0x1000_0000 {
        return None;
    }
    // FIT epoch is 1989-12-31 00:00:00 UTC
    let base = DateTime::parse_from_rfc3339("1989-12-31T00:00:00Z")
        .ok()?
        .naive_utc();
    base.checked_add_signed(chrono::Duration::seconds(secs as i64))
}
