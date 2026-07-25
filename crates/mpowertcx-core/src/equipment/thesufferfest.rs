use crate::equipment::{BikeParser, CsvRows};
use crate::ride::{python_float, Ride};

pub struct TheSufferfest;

impl TheSufferfest {
    pub fn new() -> Self {
        Self
    }

    fn load(rows: &mut CsvRows, ride: &mut Ride) {
        let mut last_time = 0.0f64;
        let mut distance = 0.0f64;

        while let Some(row) = rows.next() {
            if row.is_empty() {
                continue;
            }
            let time = row.get(1).and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0);
            let time_delta = time - last_time;
            last_time = time;
            let speed = row.get(5).and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0);
            distance += speed * time_delta / 22.36936;

            ride.add_sample(
                row.get(2).map(|s| s.as_str()).unwrap_or("0"),
                row.get(3).map(|s| s.as_str()).unwrap_or("0"),
                row.get(4).map(|s| s.as_str()).unwrap_or("0"),
                distance,
            );
        }

        ride.infer_header(last_time, python_float(last_time));
    }
}

impl BikeParser for TheSufferfest {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String> {
        let expected = [
            "ticks", "time", "power", "cadence", "heartRate", "speed",
            "targetPower", "targetHeartRateZone", "targetCadence", "targetRpe",
        ];
        if peek.len() == 10 && peek.iter().zip(expected.iter()).all(|(a, b)| a == b) {
            Self::load(rows, ride);
            Ok(true)
        } else {
            Ok(false)
        }
    }

    fn name(&self) -> &str {
        "The Sufferfest"
    }

    fn incline_is_simulated(&self) -> bool {
        true
    }
}
