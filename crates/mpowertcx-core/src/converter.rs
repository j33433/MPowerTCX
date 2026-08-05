use crate::equipment::{all_parsers, fit, tcx_in, CsvRows};
use crate::ride::Ride;
use chrono::NaiveDateTime;

const UNRECOGNIZED_FILE: &str =
    "Could not recognize this file. Upload a workout export from your bike or app.";

pub struct ConvertOptions {
    pub interpolate: bool,
    pub physics: bool,
    pub physics_mass_kg: f64,
    pub power_adjust_percent: f64,
}

impl Default for ConvertOptions {
    fn default() -> Self {
        Self {
            interpolate: false,
            physics: false,
            physics_mass_kg: 0.0,
            power_adjust_percent: 0.0,
        }
    }
}

pub struct Converter {
    ride: Ride,
    equipment_name: String,
    equipment_slug: String,
    incline_is_simulated: bool,
    diagnostics: Vec<String>,
}

impl Converter {
    pub fn from_csv(data: &[u8]) -> Result<Self, String> {
        if fit::is_fit(data) {
            let mut ride = Ride::new();
            fit::load_fit(data, &mut ride).map_err(user_safe_error)?;
            let equipment_name = "FIT".to_string();
            ride.header.equipment = equipment_name.clone();
            return Ok(Self {
                ride,
                equipment_name,
                equipment_slug: "fit".to_string(),
                incline_is_simulated: false,
                diagnostics: Vec::new(),
            });
        }

        if tcx_in::is_tcx(data) {
            let mut ride = Ride::new();
            tcx_in::load_tcx(data, &mut ride).map_err(user_safe_error)?;
            let equipment_name = "TCX".to_string();
            ride.header.equipment = equipment_name.clone();
            return Ok(Self {
                ride,
                equipment_name,
                equipment_slug: "tcx".to_string(),
                incline_is_simulated: false,
                diagnostics: Vec::new(),
            });
        }

        if looks_like_binary(data) {
            return Err(UNRECOGNIZED_FILE.into());
        }

        let mut rows = CsvRows::new(data);
        let mut ride = Ride::new();
        let mut parsers = all_parsers();
        let mut equipment_name = String::new();
        let mut equipment_slug = String::new();
        let mut incline_is_simulated = false;
        let mut diagnostics: Vec<String> = Vec::new();
        let mut total_rows = 0usize;
        let mut unmatched_rows = 0usize;

        while let Some(peek) = rows.next() {
            if peek.is_empty() {
                continue;
            }
            total_rows += 1;

            let peek = peek.clone();
            let mut found = false;
            for parser in &mut parsers {
                match parser.try_load(&peek, &mut rows, &mut ride) {
                    Ok(true) => {
                        equipment_name = parser.name().to_string();
                        equipment_slug = parser.slug().to_string();
                        incline_is_simulated = parser.incline_is_simulated();
                        ride.header.equipment = equipment_name.clone();
                        found = true;
                        break;
                    }
                    Ok(false) => {}
                    Err(e) => {
                        diagnostics.push(format!("{}: {}", parser.name(), user_safe_error(e)));
                        found = true;
                        break;
                    }
                }
            }

            if !found {
                unmatched_rows += 1;
                if diagnostics.len() < 5 {
                    if let Some(preview) = row_preview(&peek) {
                        diagnostics.push(format!("No parser matched row: [{preview}]"));
                    } else {
                        diagnostics.push("No parser matched a non-text row.".into());
                    }
                }
                while let Some(row) = rows.next() {
                    if row.is_empty() {
                        break;
                    }
                }
            }
        }

        if total_rows == 0 {
            return Ok(Self {
                ride,
                equipment_name,
                equipment_slug,
                incline_is_simulated,
                diagnostics,
            });
        }

        if ride.count() == 0 {
            // Binary-ish or wholly unmatched input: keep the message clean.
            if unmatched_rows == total_rows && diagnostics.iter().all(|d| d.starts_with("No parser"))
            {
                return Err(UNRECOGNIZED_FILE.into());
            }

            let mut msg = format!(
                "No data was parsed from {} rows. Tried {} parsers.",
                total_rows,
                parsers.len(),
            );
            if !diagnostics.is_empty() {
                msg.push('\n');
                msg.push_str(&diagnostics.join("\n"));
            }
            if equipment_name.is_empty() {
                msg.push_str("\nNo equipment format was recognized.");
            }
            return Err(user_safe_error(msg));
        }

        Ok(Self {
            ride,
            equipment_name,
            equipment_slug,
            incline_is_simulated,
            diagnostics,
        })
    }

    pub fn date_hint(&self) -> Option<NaiveDateTime> {
        self.ride.get_date_hint()
    }

    pub fn ride(&self) -> &Ride {
        &self.ride
    }

    pub fn equipment_name(&self) -> &str {
        &self.equipment_name
    }

    pub fn equipment_slug(&self) -> &str {
        &self.equipment_slug
    }

    pub fn diagnostics(&self) -> &[String] {
        &self.diagnostics
    }

    pub fn count(&self) -> usize {
        self.ride.count()
    }

    pub fn convert(&self, start_time: NaiveDateTime, options: &ConvertOptions) -> String {
        let ride = self.prepared_ride(options);
        let power_fudge = 1.0 + options.power_adjust_percent / 100.0;
        crate::tcx::render_tcx(&ride, start_time, power_fudge)
    }

    pub fn convert_fit(&self, start_time: NaiveDateTime, options: &ConvertOptions) -> Vec<u8> {
        let ride = self.prepared_ride(options);
        let power_fudge = 1.0 + options.power_adjust_percent / 100.0;
        crate::fit_out::render_fit(&ride, start_time, power_fudge, self.incline_is_simulated)
    }

    fn prepared_ride(&self, options: &ConvertOptions) -> Ride {
        let mut ride = Ride {
            power: self.ride.power.clone(),
            rpm: self.ride.rpm.clone(),
            hr: self.ride.hr.clone(),
            distance: self.ride.distance.clone(),
            incline: self.ride.incline.clone(),
            altitude: self.ride.altitude.clone(),
            header: crate::ride::RideHeader::new(),
        };

        ride.header.time = self.ride.header.time;
        ride.header.time_str = self.ride.header.time_str.clone();
        ride.header.distance = self.ride.header.distance;
        ride.header.average_hr = self.ride.header.average_hr.clone();
        ride.header.max_hr = self.ride.header.max_hr.clone();

        if options.interpolate {
            ride.interpolate();
        }

        if options.physics {
            ride.model_distance(options.physics_mass_kg, !self.incline_is_simulated);
        }

        ride
    }
}

/// True when the buffer is mostly non-text (e.g. JPEG, PDF, random bytes).
/// NUL bytes are ignored: some Stages CSV exports are null-padded.
fn looks_like_binary(data: &[u8]) -> bool {
    let sample: Vec<u8> = data.iter().copied().filter(|&b| b != 0).take(1024).collect();
    let n = sample.len();
    if n < 8 {
        return false;
    }
    let mut control = 0usize;
    for &b in &sample {
        match b {
            1..=8 | 11 | 12 | 14..=31 | 127 => control += 1,
            _ => {}
        }
    }
    // High-bit bytes alone are fine (UTF-8). Flag dense control characters.
    control * 8 > n
}

/// Printable, length-capped preview of a CSV row; None if the row is binary junk.
fn row_preview(row: &[String]) -> Option<String> {
    let parts: Vec<String> = row.iter().take(4).map(|s| sanitize_preview_piece(s)).collect();
    let joined = parts.join(", ");
    if is_mostly_printable(&joined) {
        Some(joined)
    } else {
        None
    }
}

fn sanitize_preview_piece(s: &str) -> String {
    let mut out = String::new();
    for c in s.chars().take(40) {
        if c.is_ascii_graphic() || c == ' ' {
            out.push(c);
        } else {
            out.push('?');
        }
    }
    if s.chars().count() > 40 {
        out.push('…');
    }
    out
}

fn is_mostly_printable(s: &str) -> bool {
    if s.is_empty() {
        return true;
    }
    let total = s.chars().count();
    let ok = s
        .chars()
        .filter(|c| c.is_ascii_graphic() || c.is_ascii_whitespace())
        .count();
    ok * 100 / total >= 85
}

/// Strip control characters and cap length so errors stay readable in the UI.
fn user_safe_error(msg: impl AsRef<str>) -> String {
    let cleaned: String = msg
        .as_ref()
        .chars()
        .map(|c| {
            if c == '\n' || c == '\t' || (c.is_ascii_graphic() || c == ' ') {
                c
            } else {
                '?'
            }
        })
        .collect();
    const MAX: usize = 500;
    if cleaned.chars().count() > MAX {
        let truncated: String = cleaned.chars().take(MAX).collect();
        format!("{truncated}…")
    } else {
        cleaned
    }
}
