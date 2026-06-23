use crate::ride::Ride;

pub mod echelon;
pub mod stages;
pub mod thesufferfest;
pub mod systm;

pub trait BikeParser {
    fn try_load(&mut self, peek: &[String], rows: &mut CsvRows, ride: &mut Ride) -> bool;
    fn name(&self) -> &str;
}

pub fn all_parsers() -> Vec<Box<dyn BikeParser>> {
    vec![
        Box::new(thesufferfest::TheSufferfest::new()),
        Box::new(echelon::EchelonV1::new()),
        Box::new(echelon::EchelonV2::new()),
        Box::new(echelon::EchelonV3::new()),
        Box::new(systm::Systm::new()),
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

        let rows: Vec<Vec<String>> = normalized
            .split('\n')
            .map(parse_csv_line)
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

fn parse_csv_line(line: &str) -> Vec<String> {
    if line.is_empty() {
        return Vec::new();
    }
    line.split(',').map(|s| s.trim_start().to_string()).collect()
}
