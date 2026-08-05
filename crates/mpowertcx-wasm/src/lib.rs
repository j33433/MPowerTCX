use mpowertcx_core::{lint_tcx, Severity, ConvertOptions, Converter};
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn get_sample_csv() -> Vec<u8> {
    include_bytes!("../../../web/samples/1122.csv").to_vec()
}

#[wasm_bindgen]
pub struct ConvertResult {
    tcx: String,
    fit: Vec<u8>,
    equipment: String,
    equipment_slug: String,
    sample_count: usize,
    date_hint: Option<String>,
    debug: Option<String>,
    lint_error_count: usize,
}

#[wasm_bindgen]
impl ConvertResult {
    #[wasm_bindgen(getter)]
    pub fn tcx(&self) -> String {
        self.tcx.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn fit(&self) -> Vec<u8> {
        self.fit.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn equipment(&self) -> String {
        self.equipment.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn equipment_slug(&self) -> String {
        self.equipment_slug.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn sample_count(&self) -> usize {
        self.sample_count
    }

    #[wasm_bindgen(getter)]
    pub fn date_hint(&self) -> Option<String> {
        self.date_hint.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn debug(&self) -> Option<String> {
        self.debug.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn lint_error_count(&self) -> usize {
        self.lint_error_count
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
    let fit = converter.convert_fit(start_time, &options);

    let debug = if converter.diagnostics().is_empty() {
        None
    } else {
        Some(converter.diagnostics().join("\n"))
    };

    let lint_error_count = lint_tcx(&tcx)
        .iter()
        .filter(|r| r.severity == Severity::Error)
        .count();

    Ok(ConvertResult {
        tcx,
        fit,
        equipment: converter.equipment_name().to_string(),
        equipment_slug: converter.equipment_slug().to_string(),
        sample_count: converter.count(),
        date_hint: converter.date_hint().map(|dt| dt.format("%Y-%m-%dT%H:%M:%S").to_string()),
        debug,
        lint_error_count,
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
