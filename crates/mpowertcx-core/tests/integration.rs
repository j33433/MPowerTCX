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

fn detect_parser(csv_path: &PathBuf) -> String {
    let data = fs::read(csv_path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    let name = converter.equipment_name();
    if name.is_empty() {
        "(none)".to_string()
    } else {
        name.to_string()
    }
}

fn sample_csv_paths() -> Vec<PathBuf> {
    let mut paths: Vec<PathBuf> = fs::read_dir(samples_dir())
        .unwrap()
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| {
            p.file_name()
                .and_then(|n| n.to_str())
                .map(|n| n.to_lowercase().ends_with(".csv"))
                .unwrap_or(false)
        })
        .collect();
    paths.sort();
    paths
}

/// Reports which parser (equipment format) handled each sample CSV.
/// Run with `cargo test -p mpowertcx-core report_parsers -- --nocapture`.
#[test]
fn report_parsers() {
    use std::collections::BTreeMap;

    let paths = sample_csv_paths();
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    let name_width = paths
        .iter()
        .map(|p| p.file_name().unwrap().to_string_lossy().len())
        .max()
        .unwrap_or(0);

    println!("\nParser used per sample file:");
    println!("{:-<width$}", "", width = name_width + 24);
    for path in &paths {
        let name = path.file_name().unwrap().to_string_lossy().to_string();
        let parser = detect_parser(path);
        *counts.entry(parser.clone()).or_insert(0) += 1;
        println!("{:<width$}  {}", name, parser, width = name_width);
    }

    println!("\nParser totals:");
    println!("{:-<32}", "");
    for (parser, count) in &counts {
        println!("{:<24}  {}", parser, count);
    }
    println!("{:<24}  {}", "TOTAL", paths.len());
    println!();
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

        let tcx_name = format!("{}.tcx", name);
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

        let tcx_name = format!("{}_model.tcx", name);
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

        let tcx_name = format!("{}_interp.tcx", name);
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

#[test]
fn test_trainerroad_indoor() {
    let path = samples_dir().join("trainerroad_indoor.txt");
    let data = fs::read(&path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    assert_eq!(converter.equipment_name(), "TrainerRoad");
    assert_eq!(converter.count(), 60);
    assert_eq!(
        converter.date_hint(),
        Some(NaiveDateTime::parse_from_str("2026-07-22T15:15:21", "%Y-%m-%dT%H:%M:%S").unwrap())
    );

    let start = NaiveDateTime::parse_from_str("2026-07-22T15:15:21", "%Y-%m-%dT%H:%M:%S").unwrap();
    let tcx = converter.convert(start, &ConvertOptions::default());
    assert!(tcx.contains("<Watts>75</Watts>"));
    assert!(tcx.contains("<Cadence>67.0</Cadence>") || tcx.contains("<Cadence>67</Cadence>"));
    assert!(tcx.contains("<Value>86.0</Value>") || tcx.contains("<Value>86</Value>"));
}

#[test]
fn test_trainerroad_outdoor_distance() {
    let path = samples_dir().join("trainerroad_outdoor.txt");
    let data = fs::read(&path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    assert_eq!(converter.equipment_name(), "TrainerRoad");
    assert_eq!(converter.count(), 40);
    assert!(converter.ride().header.distance > 9000.0);

    let start = NaiveDateTime::parse_from_str("2026-07-15T11:54:13", "%Y-%m-%dT%H:%M:%S").unwrap();
    let tcx = converter.convert(start, &ConvertOptions::default());
    assert!(tcx.contains("9919.4") || tcx.contains("9919.40"));
    assert!(converter.ride().distance.first().unwrap().starts_with("9919"));
}

#[test]
fn test_fit_black() {
    let path = samples_dir().join("Black.fit");
    let data = fs::read(&path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    assert_eq!(converter.equipment_name(), "FIT");
    assert_eq!(converter.count(), 3601);
    assert_eq!(
        converter.date_hint(),
        Some(NaiveDateTime::parse_from_str("2026-07-22T15:15:21", "%Y-%m-%dT%H:%M:%S").unwrap())
    );
    assert!((converter.ride().header.time - 3600.0).abs() < 1.0);
    assert!(converter.ride().header.distance > 16000.0);

    let start = converter.date_hint().unwrap();
    let tcx = converter.convert(start, &ConvertOptions::default());
    assert!(tcx.contains("<Watts>75</Watts>"));
    assert!(tcx.contains("<Cadence>67.0</Cadence>") || tcx.contains("<Cadence>67</Cadence>"));
    assert!(tcx.contains("<Value>86.0</Value>") || tcx.contains("<Value>86</Value>"));
}

#[test]
fn test_tcx_black() {
    let path = samples_dir().join("Black.fit.tcx");
    let data = fs::read(&path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    assert_eq!(converter.equipment_name(), "TCX");
    assert_eq!(converter.count(), 3600);
    assert_eq!(
        converter.date_hint(),
        Some(NaiveDateTime::parse_from_str("2026-07-22T15:15:21", "%Y-%m-%dT%H:%M:%S").unwrap())
    );
    assert!((converter.ride().header.time - 3599.0).abs() < 1.0);
    assert!(converter.ride().header.distance > 24000.0);

    let start = converter.date_hint().unwrap();
    let tcx = converter.convert(start, &ConvertOptions::default());
    assert!(tcx.contains("<Watts>75</Watts>"));
    assert!(tcx.contains("<Cadence>67.0</Cadence>") || tcx.contains("<Cadence>67</Cadence>"));
    assert!(tcx.contains("<Value>86.0</Value>") || tcx.contains("<Value>86</Value>"));
}

#[test]
fn test_fit_mywhoosh() {
    let path = samples_dir().join("MyNewActivity-5.8.1.fit");
    let data = fs::read(&path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    assert_eq!(converter.equipment_name(), "FIT");
    assert_eq!(converter.count(), 3782);
    assert_eq!(
        converter.date_hint(),
        Some(NaiveDateTime::parse_from_str("2026-07-24T15:08:04", "%Y-%m-%dT%H:%M:%S").unwrap())
    );
    assert!((converter.ride().header.time - 3782.0).abs() < 1.0);

    let ride = converter.ride();
    assert_eq!(ride.altitude.len(), 3782, "altitude vec populated");
    assert_eq!(ride.incline.len(), 3782, "incline vec populated");
    let alt_vec: Vec<f64> = ride.altitude.iter().map(|s| s.parse().unwrap_or(0.0)).collect();
    assert!(alt_vec.iter().cloned().fold(f64::NAN, f64::max) - alt_vec.iter().cloned().fold(f64::NAN, f64::min) > 100.0,
        "meaningful elevation range");

    // physics model: altitude must not drift (altitude vec breaks circularity)
    let start = converter.date_hint().unwrap();
    let plain = converter.convert(start, &ConvertOptions::default());
    let model = converter.convert(start, &ConvertOptions {
        physics: true,
        physics_mass_kg: 70.0,
        ..ConvertOptions::default()
    });
    fn extract_alts(tcx: &str) -> Vec<f64> {
        tcx.lines()
            .filter(|l| l.contains("<AltitudeMeters>"))
            .map(|l| {
                let start = l.find('>').unwrap() + 1;
                let end = l[start..].find('<').unwrap();
                l[start..start + end].parse::<f64>().unwrap()
            })
            .collect()
    }
    let plain_alts = extract_alts(&plain);
    let model_alts = extract_alts(&model);
    assert_eq!(plain_alts.len(), model_alts.len());
    for (i, (a, b)) in plain_alts.iter().zip(model_alts.iter()).enumerate() {
        assert!((a - b).abs() < 0.001, "altitude drift at sample {i}: {a} vs {b}");
    }
}

#[test]
fn test_binary_upload_clean_error() {
    let data: Vec<u8> = (0u8..=255).cycle().take(800).collect();
    let err = match Converter::from_csv(&data) {
        Ok(_) => panic!("expected error for binary input"),
        Err(e) => e,
    };
    assert!(!err.chars().any(|c| c.is_control() && c != '\n' && c != '\t'));
    assert!(err.len() < 200, "error too long: {err}");
    assert!(!err.contains('\u{0001}'));
    assert!(err.contains("Could not recognize") || err.contains("recognize"));

    let mut jpeg = b"\xff\xd8\xff\xe0JFIF".to_vec();
    jpeg.extend_from_slice(&[1u8; 300]);
    let err = Converter::from_csv(&jpeg).err().expect("jpeg should fail");
    assert!(err.chars().all(|c| c == '\n' || c == '\t' || c.is_ascii_graphic() || c == ' '));
}
