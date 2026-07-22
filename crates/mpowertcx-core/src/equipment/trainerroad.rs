use crate::equipment::{BikeParser, CsvRows};
use crate::ride::{python_float, Ride};

/// TrainerRoad activity export (tab-separated `.txt` in the user's WorkoutRecords folder).
///
/// Row types:
/// - `0` target power profile
/// - `1` interval labels
/// - `2` samples: sec, cadence, hr, power, speed, ?, target, distance_m, ?, lat, lon, elev, ?, iso8601
/// - `3` lap / workout summaries
pub struct TrainerRoad;

impl TrainerRoad {
    pub fn new() -> Self {
        Self
    }

    fn matches(row: &[String]) -> bool {
        match row.first().map(|s| s.as_str()) {
            Some("0") => {
                row.len() == 3
                    && row[1].parse::<f64>().is_ok()
                    && row[2].parse::<f64>().is_ok()
            }
            Some("1") => row.len() >= 6,
            Some("2") => row.len() >= 15 && is_iso8601(&row[14]),
            Some("3") => row.len() >= 4,
            _ => false,
        }
    }

    fn parse_num(s: &str) -> f64 {
        if s.is_empty() || s == "null" {
            0.0
        } else {
            s.parse::<f64>().unwrap_or(0.0)
        }
    }

    fn load_row(row: &[String], ride: &mut Ride, last_time: &mut f64, max_distance: &mut f64) {
        if row.first().map(|s| s.as_str()) != Some("2") || row.len() < 15 {
            return;
        }

        *last_time = Self::parse_num(&row[1]);
        let cadence = Self::parse_num(&row[2]);
        let hr = Self::parse_num(&row[3]);
        let power = Self::parse_num(&row[4]);
        let distance = Self::parse_num(&row[8]);
        if distance > *max_distance {
            *max_distance = distance;
        }

        if ride.get_date_hint().is_none() {
            if let Ok(dt) = chrono::DateTime::parse_from_rfc3339(&row[14]) {
                ride.set_date_hint(dt.naive_utc());
            }
        }

        // Carry forward last known distance across pause gaps (distance resets to 0).
        let sample_distance = if distance > 0.0 {
            distance
        } else if *max_distance > 0.0 {
            *max_distance
        } else {
            0.0
        };

        ride.add_sample(
            power as i64,
            python_float(cadence),
            python_float(hr),
            python_float(sample_distance),
        );
    }

    fn load(peek: &[String], rows: &mut CsvRows, ride: &mut Ride) {
        let mut last_time = 0.0f64;
        let mut max_distance = 0.0f64;

        Self::load_row(peek, ride, &mut last_time, &mut max_distance);
        while let Some(row) = rows.next() {
            if row.is_empty() {
                continue;
            }
            Self::load_row(row, ride, &mut last_time, &mut max_distance);
        }

        ride.infer_header(last_time, python_float(last_time));
        ride.header.distance = max_distance;
    }
}

fn is_iso8601(s: &str) -> bool {
    s.len() >= 20 && s.contains('T') && (s.ends_with('Z') || s.contains('+') || s.rfind('-').map(|i| i > 10).unwrap_or(false))
}

impl BikeParser for TrainerRoad {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String> {
        if !Self::matches(peek) {
            return Ok(false);
        }
        Self::load(peek, rows, ride);
        if ride.count() == 0 {
            return Err("TrainerRoad file had no sample rows (type 2)".into());
        }
        Ok(true)
    }

    fn name(&self) -> &str {
        "TrainerRoad"
    }
}
