use crate::equipment::{BikeParser, CsvRows};
use crate::ride::{python_float, Ride};

pub struct Systm;

impl Systm {
    pub fn new() -> Self {
        Self
    }

    fn header() -> &'static [&'static str] {
        &[
            "ticks", "videoTimestamp", "targetPower4dpType", "intervalId",
            "timeOfDayTimestamp", "distanceMeters", "speedVirtualMps",
            "distanceVirtualMeters", "workoutPosition", "powerMatchOffset",
            "cadence", "speed", "heartRate", "power", "distanceSensorMeters",
            "trainerPower", "time", "targetPower", "targetHeartRateZone",
            "targetCadence", "targetRpe", "secondsSinceStart", "grade",
            "speedSensorMps", "leftPower", "rightPower",
        ]
    }

    fn get(row: &[String], field: &str) -> f64 {
        let header = Self::header();
        if let Some(idx) = header.iter().position(|h| *h == field) {
            if let Some(val) = row.get(idx) {
                if val == "NaN" {
                    return 0.0;
                }
                return val.parse::<f64>().unwrap_or(0.0);
            }
        }
        0.0
    }

    fn load(rows: &mut CsvRows, ride: &mut Ride) {
        let mut last_time = 0.0f64;
        let mut start_stamp: Option<i64> = None;

        while let Some(row) = rows.next() {
            if row.is_empty() {
                continue;
            }
            if start_stamp.is_none() {
                start_stamp = Some(Self::get(row, "timeOfDayTimestamp") as i64 / 1000);
            }
            last_time = Self::get(row, "videoTimestamp");

            let power = Self::get(row, "trainerPower") as i64;
            let cadence = python_float(Self::get(row, "cadence"));
            let hr = python_float(Self::get(row, "heartRate"));
            let distance = python_float(Self::get(row, "distanceVirtualMeters"));

            ride.add_sample(power, cadence, hr, distance);
        }

        if let Some(stamp) = start_stamp {
            if let Some(dt) = chrono::DateTime::from_timestamp(stamp, 0) {
                ride.set_date_hint(dt.naive_local());
            }
        }

        ride.infer_header(last_time, python_float(last_time));
    }
}

impl BikeParser for Systm {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> bool {
        let header = Self::header();
        if peek.len() == header.len() && peek.iter().zip(header.iter()).all(|(a, b)| a == b) {
            Self::load(rows, ride);
            true
        } else {
            false
        }
    }

    fn name(&self) -> &str {
        "Wahoo SYSTM"
    }
}
