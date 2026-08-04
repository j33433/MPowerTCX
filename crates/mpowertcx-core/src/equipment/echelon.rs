use crate::equipment::{BikeParser, CsvRows};
use crate::ride::{python_float, Ride};

pub struct EchelonV1;

impl EchelonV1 {
    pub fn new() -> Self {
        Self
    }

    fn load_header(rows: &mut CsvRows, ride: &mut Ride) {
        let mut header = std::collections::HashMap::new();
        while let Some(row) = rows.next() {
            if row.is_empty() {
                break;
            }
            if row.len() >= 2 {
                header.insert(row[0].clone(), row[1].clone());
            }
        }

        let time = header.get("Total Time").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 60.0;
        let distance = header.get("Total_distance:").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 1000.0;

        ride.header.set_summary(
            time,
            python_float(time),
            distance,
            header.get("Watts Avg").cloned().unwrap_or_default(),
            header.get("Watts Max").cloned().unwrap_or_default(),
            header.get("RPM Avg").cloned().unwrap_or_default(),
            header.get("RPM Max").cloned().unwrap_or_default(),
            header.get("HR Avg").cloned().unwrap_or_default(),
            header.get("HR Max").cloned().unwrap_or_default(),
            header.get("KCal").cloned().unwrap_or_default(),
        );
    }

    fn load_data(rows: &mut CsvRows, ride: &mut Ride) {
        let mut last_time = 0.0f64;
        while let Some(row) = rows.next() {
            if row.is_empty() {
                break;
            }
            if row.len() == 6 {
                last_time = row[0].parse::<f64>().unwrap_or(0.0) * 60.0;
                let distance = row[1].parse::<f64>().unwrap_or(0.0) * 1000.0;
                ride.add_sample(
                    &row[3],
                    &row[5],
                    &row[4],
                    distance,
                );
            }
        }

        if ride.header.time == 0.0 {
            ride.infer_header(last_time, python_float(last_time));
        }
    }
}

impl BikeParser for EchelonV1 {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String> {
        if peek.len() == 1 && peek[0] == "Stage_Totals" {
            Self::load_header(rows, ride);
            return Ok(true);
        }
        let expected = ["Stage_Workout (min)", "Distance(km)", "Speed(km/h)", "Watts ", "HR ", "RPM "];
        if peek.len() == 6 && peek.iter().zip(expected.iter()).all(|(a, b)| a == b) {
            Self::load_data(rows, ride);
            return Ok(true);
        }
        Ok(false)
    }

    fn name(&self) -> &str {
        "Echelon Variant 1"
    }

    fn slug(&self) -> &str {
        "echelon-v1"
    }

    fn incline_is_simulated(&self) -> bool {
        true
    }
}

pub struct EchelonV2;

impl EchelonV2 {
    pub fn new() -> Self {
        Self
    }

    fn is_stage_summary(peek: &[String]) -> bool {
        if peek.is_empty() {
            return false;
        }
        let s = &peek[0];
        s.starts_with("STAGE_") && s.ends_with("_SUMMARY") && {
            let mid = &s[6..s.len() - 8];
            !mid.is_empty() && mid.chars().all(|c| c.is_ascii_digit())
        }
    }

    fn skip_section(rows: &mut CsvRows) {
        while let Some(row) = rows.next() {
            if row.is_empty() || row.iter().all(|s| s.is_empty()) {
                break;
            }
        }
    }

    fn load_header(rows: &mut CsvRows, ride: &mut Ride) {
        let mut header = std::collections::HashMap::new();
        while let Some(row) = rows.next() {
            if row.is_empty() || row.iter().all(|s| s.is_empty()) {
                break;
            }
            if row.len() >= 2 {
                header.insert(row[0].clone(), row[1].clone());
            }
        }

        let time = header.get("Total Time").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 60.0;
        let distance = header.get("Total Distance").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 1609.34;

        ride.header.set_summary(
            time,
            python_float(time),
            distance,
            header.get("AVG Power").cloned().unwrap_or_default(),
            header.get("MAX Power").cloned().unwrap_or_default(),
            header.get("AVG RPM").cloned().unwrap_or_default(),
            header.get("MAX RPM").cloned().unwrap_or_default(),
            header.get("AVG HR").cloned().unwrap_or_default(),
            header.get("MAX HR").cloned().unwrap_or_default(),
            header.get("CAL").cloned().unwrap_or_default(),
        );
    }

    fn load_data(rows: &mut CsvRows, ride: &mut Ride) {
        let keys = rows.next().cloned().unwrap_or_default();
        while let Some(row) = rows.next() {
            if row.is_empty() {
                break;
            }
            let data: std::collections::HashMap<&str, &str> = keys
                .iter()
                .zip(row.iter())
                .map(|(k, v)| (k.as_str(), v.as_str()))
                .collect();
            let distance = data.get("DISTANCE").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 1609.34;
            ride.add_sample(
                data.get("Power").copied().unwrap_or("0"),
                data.get("RPM").copied().unwrap_or("0"),
                data.get("HR").copied().unwrap_or("0"),
                distance,
            );
        }
    }
}

impl BikeParser for EchelonV2 {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String> {
        if peek.len() >= 2 && peek[0] == "RIDE SUMMARY" && peek[1] == "" {
            Self::load_header(rows, ride);
            return Ok(true);
        }
        if peek.len() >= 2 && peek[0] == "RIDE DATA" && peek[1] == "" {
            Self::load_data(rows, ride);
            return Ok(true);
        }
        if Self::is_stage_summary(peek) {
            Self::skip_section(rows);
            return Ok(true);
        }
        Ok(false)
    }

    fn name(&self) -> &str {
        "Echelon Variant 2"
    }

    fn slug(&self) -> &str {
        "echelon-v2"
    }

    fn incline_is_simulated(&self) -> bool {
        true
    }
}

pub struct EchelonV3;

impl EchelonV3 {
    pub fn new() -> Self {
        Self
    }

    fn load_header(rows: &mut CsvRows, ride: &mut Ride) {
        let mut header = std::collections::HashMap::new();
        while let Some(row) = rows.next() {
            if row.is_empty() {
                break;
            }
            if row.len() >= 2 {
                header.insert(row[0].clone(), row[1].clone());
            }
        }

        let time = header.get("Total Time").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 60.0;
        let distance = header.get("Total_distance:").and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) * 1609.34;

        ride.header.set_summary(
            time,
            python_float(time),
            distance,
            header.get("Watts Avg").cloned().unwrap_or_default(),
            header.get("Watts Max").cloned().unwrap_or_default(),
            header.get("RPM Avg").cloned().unwrap_or_default(),
            header.get("RPM Max").cloned().unwrap_or_default(),
            header.get("HR Avg").cloned().unwrap_or_default(),
            header.get("HR Max").cloned().unwrap_or_default(),
            header.get("KCal").cloned().unwrap_or_default(),
        );
    }

    fn load(rows: &mut CsvRows, ride: &mut Ride) {
        while let Some(row) = rows.next() {
            if row.len() == 6 {
                let distance = row[1].parse::<f64>().unwrap_or(0.0) * 1609.34;
                ride.add_sample(&row[3], &row[5], &row[4], distance);
            } else if row.len() == 1 && row[0] == "Stage_Totals" {
                Self::load_header(rows, ride);
            }
        }
    }
}

impl BikeParser for EchelonV3 {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String> {
        let expected = ["Stage_Workout (min)", "Distance(mile)", "Speed (mph)", "Watts ", "HR ", "RPM "];
        if peek.len() == 6 && peek.iter().zip(expected.iter()).all(|(a, b)| a == b) {
            Self::load(rows, ride);
            return Ok(true);
        }
        Ok(false)
    }

    fn name(&self) -> &str {
        "Echelon Variant 3"
    }

    fn slug(&self) -> &str {
        "echelon-v3"
    }

    fn incline_is_simulated(&self) -> bool {
        true
    }
}
