use crate::equipment::{all_parsers, CsvRows};
use crate::ride::Ride;
use chrono::NaiveDateTime;

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
    diagnostics: Vec<String>,
}

impl Converter {
    pub fn from_csv(data: &[u8]) -> Result<Self, String> {
        let mut rows = CsvRows::new(data);
        let mut ride = Ride::new();
        let mut parsers = all_parsers();
        let mut equipment_name = String::new();
        let mut diagnostics: Vec<String> = Vec::new();
        let mut total_rows = 0usize;

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
                        ride.header.equipment = equipment_name.clone();
                        found = true;
                        break;
                    }
                    Ok(false) => {}
                    Err(e) => {
                        diagnostics.push(format!("{}: {}", parser.name(), e));
                        found = true;
                        break;
                    }
                }
            }

            if !found {
                let preview: Vec<&str> = peek.iter().take(4).map(|s| s.as_str()).collect();
                diagnostics.push(format!("No parser matched row: [{}]", preview.join(", ")));
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
                diagnostics,
            });
        }

        if ride.count() == 0 {
            let mut msg = format!(
                "No data was parsed from {} rows. Tried {} parsers.\n{}",
                total_rows,
                parsers.len(),
                diagnostics.join("\n")
            );
            if equipment_name.is_empty() {
                msg.push_str("\nNo equipment format was recognized.");
            }
            return Err(msg);
        }

        Ok(Self {
            ride,
            equipment_name,
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

    pub fn diagnostics(&self) -> &[String] {
        &self.diagnostics
    }

    pub fn count(&self) -> usize {
        self.ride.count()
    }

    pub fn convert(&self, start_time: NaiveDateTime, options: &ConvertOptions) -> String {
        let mut ride = Ride {
            power: self.ride.power.clone(),
            rpm: self.ride.rpm.clone(),
            hr: self.ride.hr.clone(),
            distance: self.ride.distance.clone(),
            incline: self.ride.incline.clone(),
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
            ride.model_distance(options.physics_mass_kg);
        }

        let power_fudge = 1.0 + options.power_adjust_percent / 100.0;

        crate::tcx::render_tcx(&ride, start_time, power_fudge)
    }
}
