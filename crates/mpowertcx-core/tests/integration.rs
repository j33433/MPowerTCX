use mpowertcx_core::{ConvertOptions, Converter};
use chrono::NaiveDateTime;
use std::fs;
use std::path::PathBuf;

fn samples_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("samples")
}

fn parse_tcx(content: &str) -> TcxData {
    let mut data = TcxData::default();

    for line in content.lines() {
        let trimmed = line.trim();

        if let Some(val) = extract_tag(trimmed, "TotalTimeSeconds") {
            data.total_time = val.to_string();
        }
        if let Some(val) = extract_tag(trimmed, "DistanceMeters") {
            if !trimmed.contains("MaximumSpeed") {
                data.total_distance = val.to_string();
            }
        }
        if let Some(val) = extract_tag(trimmed, "Value") {
            if data.avg_hr.is_empty() {
                data.avg_hr = val.to_string();
            } else if data.max_hr.is_empty() {
                data.max_hr = val.to_string();
            }
        }

        if trimmed == "<Trackpoint>" {
            data.trackpoints.push(Trackpoint::default());
        }
        if let Some(val) = extract_tag(trimmed, "Watts") {
            if let Some(tp) = data.trackpoints.last_mut() {
                tp.watts = val.to_string();
            }
        }
        if let Some(val) = extract_tag(trimmed, "Cadence") {
            if let Some(tp) = data.trackpoints.last_mut() {
                tp.cadence = val.to_string();
            }
        }
        if let Some(val) = extract_tag(trimmed, "DistanceMeters") {
            if let Some(tp) = data.trackpoints.last_mut() {
                if !trimmed.contains("MaximumSpeed") {
                    tp.distance = val.to_string();
                }
            }
        }
        if let Some(val) = extract_tag(trimmed, "Value") {
            if let Some(tp) = data.trackpoints.last_mut() {
                tp.hr = val.to_string();
            }
        }
    }

    data
}

fn extract_tag<'a>(line: &'a str, tag: &str) -> Option<&'a str> {
    let open = format!("<{}>", tag);
    let close = format!("</{}>", tag);
    if line.starts_with(&open) && line.ends_with(&close) {
        let start = open.len();
        let end = line.len() - close.len();
        Some(&line[start..end])
    } else {
        None
    }
}

#[derive(Default)]
struct TcxData {
    total_time: String,
    total_distance: String,
    avg_hr: String,
    max_hr: String,
    trackpoints: Vec<Trackpoint>,
}

#[derive(Default)]
struct Trackpoint {
    watts: String,
    cadence: String,
    hr: String,
    distance: String,
}

fn compare_f64(a: &str, b: &str, tolerance: f64) -> bool {
    let af: f64 = a.parse().unwrap_or(0.0);
    let bf: f64 = b.parse().unwrap_or(0.0);
    (af - bf).abs() <= tolerance
}

fn compare_int(a: &str, b: &str, tolerance: i64) -> bool {
    let ai: f64 = a.parse().unwrap_or(0.0);
    let bi: f64 = b.parse().unwrap_or(0.0);
    ((ai - bi).abs() as i64) <= tolerance
}

fn run_conversion(csv_path: &str, interpolate: bool, physics: bool) -> String {
    let data = fs::read(csv_path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    let start_time = NaiveDateTime::parse_from_str("2010-10-19T20:56:35", "%Y-%m-%dT%H:%M:%S").unwrap();

    let options = ConvertOptions {
        interpolate,
        physics,
        physics_mass_kg: if physics { 70.0 } else { 0.0 },
        power_adjust_percent: 0.0,
    };

    converter.convert(start_time, &options)
}

#[test]
fn test_plain_conversions_exact() {
    let dir = samples_dir();
    let mut tested = 0;

    for entry in fs::read_dir(&dir).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        let name = path.file_name().unwrap().to_string_lossy().to_string();

        if !name.to_lowercase().ends_with(".csv") {
            continue;
        }

        let base = name.trim_end_matches(".csv").trim_end_matches(".CSV");
        let tcx_name = format!("{}.tcx", base);
        let tcx_path = dir.join(&tcx_name);

        if !tcx_path.exists() {
            continue;
        }

        let output = run_conversion(path.to_str().unwrap(), false, false);
        let expected = fs::read_to_string(&tcx_path).unwrap();

        assert_eq!(output, expected, "Exact mismatch for {}", name);
        tested += 1;
    }

    assert_eq!(tested, 26, "Expected 26 plain test cases");
}

#[test]
fn test_model_conversions_exact() {
    let dir = samples_dir();
    let mut tested = 0;

    for entry in fs::read_dir(&dir).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        let name = path.file_name().unwrap().to_string_lossy().to_string();

        if !name.to_lowercase().ends_with(".csv") {
            continue;
        }

        let base = name.trim_end_matches(".csv").trim_end_matches(".CSV");
        let tcx_name = format!("{}_model.tcx", base);
        let tcx_path = dir.join(&tcx_name);

        if !tcx_path.exists() {
            continue;
        }

        let output = run_conversion(path.to_str().unwrap(), false, true);
        let expected = fs::read_to_string(&tcx_path).unwrap();

        assert_eq!(output, expected, "Exact mismatch for {} (model)", name);
        tested += 1;
    }

    assert_eq!(tested, 26, "Expected 26 model test cases");
}

#[test]
fn test_interpolated_conversions_semantic() {
    let dir = samples_dir();
    let mut tested = 0;

    for entry in fs::read_dir(&dir).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        let name = path.file_name().unwrap().to_string_lossy().to_string();

        if !name.to_lowercase().ends_with(".csv") {
            continue;
        }

        let base = name.trim_end_matches(".csv").trim_end_matches(".CSV");
        let tcx_name = format!("{}_interp.tcx", base);
        let tcx_path = dir.join(&tcx_name);

        if !tcx_path.exists() {
            continue;
        }

        let output = run_conversion(path.to_str().unwrap(), true, false);
        let expected = fs::read_to_string(&tcx_path).unwrap();

        let out_data = parse_tcx(&output);
        let exp_data = parse_tcx(&expected);

        assert_eq!(
            out_data.trackpoints.len(),
            exp_data.trackpoints.len(),
            "Trackpoint count mismatch for {} (interp): {} vs {}",
            name,
            out_data.trackpoints.len(),
            exp_data.trackpoints.len()
        );

        for (i, (out_tp, exp_tp)) in out_data.trackpoints.iter().zip(exp_data.trackpoints.iter()).enumerate() {
            assert!(
                compare_int(&out_tp.watts, &exp_tp.watts, 10),
                "Watts mismatch at point {} for {} (interp): {} vs {}",
                i, name, out_tp.watts, exp_tp.watts
            );
            assert!(
                compare_int(&out_tp.cadence, &exp_tp.cadence, 20),
                "Cadence mismatch at point {} for {} (interp): {} vs {}",
                i, name, out_tp.cadence, exp_tp.cadence
            );
            assert!(
                compare_int(&out_tp.hr, &exp_tp.hr, 10),
                "HR mismatch at point {} for {} (interp): {} vs {}",
                i, name, out_tp.hr, exp_tp.hr
            );
            assert!(
                compare_f64(&out_tp.distance, &exp_tp.distance, 10.0),
                "Distance mismatch at point {} for {} (interp): {} vs {}",
                i, name, out_tp.distance, exp_tp.distance
            );
        }

        tested += 1;
    }

    assert_eq!(tested, 26, "Expected 26 interp test cases");
}
