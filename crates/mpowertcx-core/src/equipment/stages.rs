use crate::equipment::{to_meters, BikeParser, CsvRows};
use crate::ride::Ride;

pub struct Stages {
    metric: bool,
}

impl Stages {
    pub fn new() -> Self {
        Self { metric: true }
    }

    fn distance_to_float(dist: &str) -> f64 {
        let dist = if dist.starts_with(':') {
            format!("10{}", &dist[1..])
        } else {
            dist.to_string()
        };
        dist.parse::<f64>().unwrap_or(0.0)
    }

    fn parse_time(time: &str) -> i64 {
        let parts: Vec<&str> = time.split(':').collect();
        if parts.len() == 2 || parts.len() == 3 {
            let minutes: i64 = parts[0].parse().unwrap_or(-1);
            let seconds: i64 = parts[1].parse().unwrap_or(-1);
            if minutes >= 0 && seconds >= 0 {
                return minutes * 60 + seconds;
            }
        }
        -1
    }

    fn load_header(rows: &mut CsvRows, ride: &mut Ride, metric: bool) {
        let mut header = std::collections::HashMap::new();
        while let Some(row) = rows.next() {
            if row.is_empty() {
                break;
            }
            if row.len() >= 2 {
                header.insert(row[0].clone(), row[1].clone());
            }
        }

        let time_str = header.get("Time").cloned().unwrap_or_default();
        let parts: Vec<&str> = time_str.split(':').collect();
        let (h, m, s) = match parts.len() {
            3 => (
                parts[0].parse::<i64>().unwrap_or(0),
                parts[1].parse::<i64>().unwrap_or(0),
                parts[2].parse::<i64>().unwrap_or(0),
            ),
            2 => (
                0,
                parts[0].parse::<i64>().unwrap_or(0),
                parts[1].parse::<i64>().unwrap_or(0),
            ),
            1 => (0, 0, parts[0].parse::<i64>().unwrap_or(0)),
            _ => (0, 0, 0),
        };
        let time = (h * 60 * 60 + m * 60 + s) as f64;
        let time_str = (h * 60 * 60 + m * 60 + s).to_string();

        let distance = to_meters(
            Self::distance_to_float(header.get("Distance").map(|s| s.as_str()).unwrap_or("0")),
            metric,
        );

        ride.header.set_summary(
            time,
            time_str,
            distance,
            header.get("Watts_Avg").cloned().unwrap_or_default(),
            header.get("Watts_Max").cloned().unwrap_or_default(),
            header.get("RPM_Avg").cloned().unwrap_or_default(),
            header.get("RPM_Max").cloned().unwrap_or_default(),
            header.get("HR_Avg").cloned().unwrap_or_default(),
            header.get("HR_Max").cloned().unwrap_or_default(),
            header.get("KCal").cloned().unwrap_or_default(),
        );
    }

    fn load(&mut self, rows: &mut CsvRows, ride: &mut Ride) {
        self.metric = true;
        let mut distance = 0.0f64;
        let mut header_found = false;
        let mut last_time: i64 = 0;

        while let Some(row) = rows.next() {
            if row.is_empty() {
                continue;
            }
            if row[0] == "English" {
                self.metric = false;
            } else if row[0] == "Ride_Totals" {
                Self::load_header(rows, ride, self.metric);
                header_found = true;
            } else if row.len() >= 6 {
                let time = Self::parse_time(&row[0]);
                if last_time > 0 && time - last_time > 1 {
                    // time warp detected
                }
                last_time = time;
                if time >= 0 {
                    distance += Self::distance_to_float(&row[2]) / (60.0 * 60.0);
                    ride.add_sample(
                        &row[3],
                        &row[5],
                        &row[4],
                        to_meters(distance, self.metric),
                    );
                    if row.len() >= 9 {
                        ride.add_incline(&row[8]);
                    }
                }
            }
        }

        if !header_found {
            ride.infer_header(last_time as f64, last_time.to_string());
        }
    }
}

impl BikeParser for Stages {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String> {
        if !peek.is_empty() && peek[0] == "Stages_Data" {
            self.load(rows, ride);
            return Ok(true);
        }

        if peek.len() == 6 && peek[0].contains(':') {
            let all_floats = peek[1..].iter().all(|f| f.parse::<f64>().is_ok());
            if all_floats {
                self.load(rows, ride);
                return Ok(true);
            }
        }

        Ok(false)
    }

    fn name(&self) -> &str {
        "Stages"
    }
}
