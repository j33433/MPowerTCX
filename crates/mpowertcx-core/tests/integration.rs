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
fn test_equipment_slugs() {
    let expected = [
        ("Stages", "stages"),
        ("Wahoo SYSTM", "systm"),
        ("The Sufferfest", "sufferfest"),
        ("TrainerRoad", "trainerroad"),
        ("Echelon Variant 1", "echelon-v1"),
        ("Echelon Variant 2", "echelon-v2"),
        ("Echelon Variant 3", "echelon-v3"),
    ];

    let mut seen: std::collections::HashMap<String, String> = std::collections::HashMap::new();
    let mut checked = 0usize;

    for path in fs::read_dir(samples_dir()).unwrap().filter_map(|e| e.ok()) {
        let path = path.path();
        let ext_ok = path
            .file_name()
            .and_then(|n| n.to_str())
            .map(|n| {
                ["csv", "txt"]
                    .iter()
                    .any(|ext| n.to_lowercase().ends_with(&format!(".{ext}")))
            })
            .unwrap_or(false);
        if !ext_ok {
            continue;
        }

        let Ok(converter) = fs::read(&path).map(|data| Converter::from_csv(&data)).unwrap_or(Err(String::new())) else {
            continue;
        };
        let name = converter.equipment_name();
        if name.is_empty() {
            continue;
        }
        let slug = converter.equipment_slug();
        seen.entry(name.to_string()).or_insert_with(|| slug.to_string());
        checked += 1;

        if let Some(&(_, want)) = expected.iter().find(|(n, _)| *n == name) {
            assert_eq!(slug, want, "slug mismatch for {name} in {:?}", path);
        } else {
            assert!(!slug.is_empty(), "empty slug for {name} in {:?}", path);
            assert!(
                slug.chars().all(|c| c.is_ascii_lowercase() || c == '-'),
                "slug not lowercase/dashed: {slug} for {name}"
            );
        }
    }

    assert!(checked > 0, "no sample files parsed");
    for (name, want) in expected {
        assert_eq!(
            seen.get(name)
                .map(|s| s.as_str())
                .unwrap_or_else(|| panic!("no sample exercises parser {name}")),
            want,
            "slug mismatch for {name}"
        );
    }
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
    assert_eq!(converter.equipment_slug(), "trainerroad");
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
    assert_eq!(converter.equipment_slug(), "fit");
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
    assert_eq!(converter.equipment_slug(), "tcx");
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
fn test_fit_output_roundtrip() {
    let path = samples_dir().join("1122.csv");
    let data = fs::read(&path).unwrap();
    let converter = Converter::from_csv(&data).unwrap();
    let start_time = NaiveDateTime::parse_from_str("2010-10-19T20:56:35", "%Y-%m-%dT%H:%M:%S").unwrap();
    let options = ConvertOptions {
        interpolate: true,
        physics: false,
        physics_mass_kg: 0.0,
        power_adjust_percent: 0.0,
    };

    let fit = converter.convert_fit(start_time, &options);
    assert!(fit.len() > 1000, "FIT output too small");

    let mut ride = mpowertcx_core::Ride::new();
    mpowertcx_core::equipment::fit::load_fit(&fit, &mut ride).unwrap();

    let golden = fs::read_to_string(samples_dir().join("1122.csv_interp.tcx")).unwrap();
    let expected = parse_tcx(&golden);
    assert_eq!(expected.trackpoints.len(), ride.count());

    for (i, tp) in expected.trackpoints.iter().enumerate() {
        let watts = ride.power[i].parse::<f64>().unwrap();
        assert!(compare_f64(&tp.watts, &watts.to_string(), 0.6), "power at sample {i}");
        assert!(compare_f64(&tp.cadence, &ride.rpm[i], 0.6), "cadence at sample {i}");
        assert!(compare_f64(&tp.hr, &ride.hr[i], 0.6), "hr at sample {i}");
        // FIT stores distance at 0.01 m resolution
        assert!(compare_f64(&tp.distance, &ride.distance[i], 0.02), "distance at sample {i}");
    }

    // Message structure: one file_id, activity, session, lap, then records.
    let records = fitparser::from_bytes(&fit).unwrap();
    let kinds: Vec<fitparser::profile::MesgNum> = records.iter().map(|m| m.kind()).collect();
    assert_eq!(kinds.iter().filter(|k| **k == fitparser::profile::MesgNum::FileId).count(), 1);
    assert_eq!(kinds.iter().filter(|k| **k == fitparser::profile::MesgNum::Activity).count(), 1);
    assert_eq!(kinds.iter().filter(|k| **k == fitparser::profile::MesgNum::Session).count(), 1);
    assert_eq!(kinds.iter().filter(|k| **k == fitparser::profile::MesgNum::Lap).count(), 1);
    assert_eq!(kinds.iter().filter(|k| **k == fitparser::profile::MesgNum::Record).count(), ride.count());
}

/// Extract trackpoint-level cumulative distances from a rendered TCX.
fn tcx_track_distances(tcx: &str) -> Vec<f64> {
    let mut in_track = false;
    tcx.lines()
        .filter(|l| {
            let l = l.trim();
            if l == "<Track>" {
                in_track = true;
                return false;
            }
            if l == "</Track>" {
                in_track = false;
                return false;
            }
            in_track && l.starts_with("<DistanceMeters>")
        })
        .map(|l| {
            let l = l.trim();
            l.trim_start_matches("<DistanceMeters>")
                .trim_end_matches("</DistanceMeters>")
                .parse::<f64>()
                .unwrap()
        })
        .collect()
}

/// Applying the physics model to a FIT round trip must reproduce the repair on
/// the original file. Before this fix, grade-derived altitude was written into
/// the FIT at 0.5 m resolution; re-parsing it produced noisy "real" incline,
/// and the repair applied it, giving wild speed/distance.
#[test]
fn test_fit_roundtrip_repair_parity() {
    let web_sample = samples_dir().parent().unwrap().join("web/samples/sample.csv");
    let cases: Vec<(PathBuf, &str, f64, bool)> = vec![
        // Simulated incline (Stages, elevation column): repair must skip grade
        // both times. This is the upload.bike sample from the bug report.
        (web_sample, "stages sample (simulated incline)", 0.5, false),
        // Real incline (smart trainer): exact grade must survive the round trip.
        (
            samples_dir().join("wahoo_systm_activity.csv"),
            "SYSTM (real incline)",
            5.0,
            true,
        ),
    ];

    for (path, label, tolerance_m, expect_grade) in cases {
        let data = fs::read(&path).unwrap();
        let converter = Converter::from_csv(&data).unwrap();
        let start_time =
            NaiveDateTime::parse_from_str("2010-10-19T20:56:35", "%Y-%m-%dT%H:%M:%S").unwrap();
        let options = ConvertOptions {
            interpolate: false,
            physics: true,
            physics_mass_kg: 70.0,
            power_adjust_percent: 0.0,
        };

        let reference = tcx_track_distances(&converter.convert(start_time, &options));

        let fit = converter.convert_fit(start_time, &options);

        // Simulated equipment must not leak grade/altitude into the FIT (that
        // is what made re-parsed incline look real); real-incline equipment
        // must carry an exact grade field and no synthesized altitude.
        let records = fitparser::from_bytes(&fit).unwrap();
        let mut saw_grade = false;
        let mut saw_altitude = false;
        for m in records.iter().filter(|m| m.kind() == fitparser::profile::MesgNum::Record) {
            for f in m.fields() {
                match f.name() {
                    "grade" => saw_grade = true,
                    "altitude" | "enhanced_altitude" => saw_altitude = true,
                    _ => {}
                }
            }
        }
        assert_eq!(saw_grade, expect_grade, "{label}: grade field presence");
        assert!(!saw_altitude, "{label}: no synthesized altitude in FIT");

        let mut ride = mpowertcx_core::Ride::new();
        mpowertcx_core::equipment::fit::load_fit(&fit, &mut ride).unwrap();
        assert_eq!(ride.count(), reference.len(), "{label}: sample count preserved");

        let mut repaired = mpowertcx_core::Ride {
            power: ride.power.clone(),
            rpm: ride.rpm.clone(),
            hr: ride.hr.clone(),
            distance: ride.distance.clone(),
            incline: ride.incline.clone(),
            altitude: ride.altitude.clone(),
            header: mpowertcx_core::RideHeader::new(),
        };
        repaired.header.time = ride.header.time;
        repaired.header.time_str = ride.header.time_str.clone();
        if options.interpolate {
            repaired.interpolate();
        }
        if options.physics {
            repaired.model_distance(options.physics_mass_kg, true);
        }

        for (i, (a, b)) in reference.iter().zip(repaired.distance.iter()).enumerate() {
            let b: f64 = b.parse().unwrap_or(0.0);
            assert!(
                (a - b).abs() <= tolerance_m,
                "{label}: distance diverged at sample {i}: {a} vs {b}"
            );
        }
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
