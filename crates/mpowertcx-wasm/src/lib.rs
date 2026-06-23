use mpowertcx_core::{ConvertOptions, Converter};
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct ConvertResult {
    tcx: String,
    equipment: String,
    sample_count: usize,
    date_hint: Option<String>,
}

#[wasm_bindgen]
impl ConvertResult {
    #[wasm_bindgen(getter)]
    pub fn tcx(&self) -> String {
        self.tcx.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn equipment(&self) -> String {
        self.equipment.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn sample_count(&self) -> usize {
        self.sample_count
    }

    #[wasm_bindgen(getter)]
    pub fn date_hint(&self) -> Option<String> {
        self.date_hint.clone()
    }
}

#[wasm_bindgen]
pub fn convert_csv_to_tcx(
    csv_bytes: &[u8],
    start_time_str: Option<String>,
    interpolate: bool,
    physics: bool,
    mass_kg: f64,
    power_adjust_percent: f64,
) -> Result<ConvertResult, JsValue> {
    let converter = Converter::from_csv(csv_bytes)
        .map_err(|e| JsValue::from_str(&e))?;

    let start_time = if let Some(ref s) = start_time_str {
        parse_time(s)?
    } else if let Some(hint) = converter.date_hint() {
        hint
    } else {
        chrono::DateTime::from_timestamp(0, 0)
            .unwrap_or_default().naive_local()
    };

    let options = ConvertOptions {
        interpolate,
        physics,
        physics_mass_kg: mass_kg,
        power_adjust_percent,
    };

    let tcx = converter.convert(start_time, &options);

    Ok(ConvertResult {
        tcx,
        equipment: converter.equipment_name().to_string(),
        sample_count: converter.count(),
        date_hint: converter.date_hint().map(|dt| dt.format("%Y-%m-%dT%H:%M:%S").to_string()),
    })
}

fn parse_time(s: &str) -> Result<chrono::NaiveDateTime, JsValue> {
    let formats = [
        "%Y-%m-%dT%H:%M:%S%.f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
    ];
    for fmt in &formats {
        if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(s, fmt) {
            return Ok(dt);
        }
    }
    Err(JsValue::from_str(&format!("could not parse time: {}", s)))
}
