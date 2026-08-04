use crate::ride::Ride;

pub mod echelon;
pub mod fit;
pub mod stages;
pub mod thesufferfest;
pub mod systm;
pub mod tcx_in;
pub mod trainerroad;

pub trait BikeParser {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> Result<bool, String>;
    fn name(&self) -> &str;
    fn slug(&self) -> &str;

    /// When true, incline data is a visual display value only (the trainer
    /// does NOT adjust resistance to match it). The physics model should not
    /// apply grade because the power goes entirely into flywheel speed.
    fn incline_is_simulated(&self) -> bool {
        false
    }
}

pub fn all_parsers() -> Vec<Box<dyn BikeParser>> {
    vec![
        Box::new(thesufferfest::TheSufferfest::new()),
        Box::new(echelon::EchelonV1::new()),
        Box::new(echelon::EchelonV2::new()),
        Box::new(echelon::EchelonV3::new()),
        Box::new(systm::Systm::new()),
        Box::new(trainerroad::TrainerRoad::new()),
        Box::new(stages::Stages::new()),
    ]
}

pub fn to_meters(d: f64, metric: bool) -> f64 {
    if metric {
        d * 1000.0
    } else {
        d * 1609.34
    }
}

pub struct CsvRows {
    rows: Vec<Vec<String>>,
    pos: usize,
}

impl CsvRows {
    pub fn new(data: &[u8]) -> Self {
        let clean: Vec<u8> = data.iter().filter(|&&b| b != 0).copied().collect();
        let text = String::from_utf8_lossy(&clean);

        let normalized = text
            .replace("\r\r\n", "\n")
            .replace("\r\n", "\n")
            .replace("\r", "\n");

        let delimiter = detect_delimiter(&normalized);
        let rows: Vec<Vec<String>> = normalized
            .split('\n')
            .map(|line| parse_csv_line(line, delimiter))
            .collect();

        Self { rows, pos: 0 }
    }

    pub fn next(&mut self) -> Option<&Vec<String>> {
        if self.pos < self.rows.len() {
            let row = &self.rows[self.pos];
            self.pos += 1;
            Some(row)
        } else {
            None
        }
    }
}

fn detect_delimiter(text: &str) -> char {
    for line in text.lines().take(20) {
        if line.is_empty() {
            continue;
        }
        if line.contains('\t') {
            return '\t';
        }
        break;
    }
    ','
}

fn parse_csv_line(line: &str, delimiter: char) -> Vec<String> {
    if line.is_empty() {
        return Vec::new();
    }
    // CSV headers (e.g. Echelon "Watts ") keep trailing spaces; TSV trims fully.
    if delimiter == '\t' {
        line.split(delimiter).map(|s| s.trim().to_string()).collect()
    } else {
        line.split(delimiter).map(|s| s.trim_start().to_string()).collect()
    }
}
