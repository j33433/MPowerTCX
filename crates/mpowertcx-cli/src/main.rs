use chrono::NaiveDateTime;
use mpowertcx_core::{has_errors, lint_tcx, ConvertOptions, Converter};
use std::fs;
use std::process::exit;

fn parse_time(s: &str) -> Result<NaiveDateTime, String> {
    let formats = [
        "%Y-%m-%dT%H:%M:%S%.f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%.f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ];
    for fmt in &formats {
        if let Ok(dt) = NaiveDateTime::parse_from_str(s, fmt) {
            return Ok(dt);
        }
    }
    // Try parsing as timestamp
    if let Ok(ts) = s.parse::<i64>() {
        if let Some(dt) = chrono::DateTime::from_timestamp(ts, 0) {
            return Ok(dt.naive_local());
        }
    }
    Err(format!("could not parse time: {}", s))
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: mpowertcx --csv <FILE> --tcx <FILE> [--time <TIME>] [--interpolate] [--model <MASS_KG>]");
        eprintln!("       mpowertcx --lint <FILE>");
        exit(1);
    }

    let mut csv_file = None;
    let mut tcx_file = None;
    let mut time_str = None;
    let mut interpolate = false;
    let mut model: Option<f64> = None;
    let mut lint_file = None;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--csv" => {
                i += 1;
                csv_file = args.get(i).cloned();
            }
            "--tcx" => {
                i += 1;
                tcx_file = args.get(i).cloned();
            }
            "--time" => {
                i += 1;
                time_str = args.get(i).cloned();
            }
            "--interpolate" => {
                interpolate = true;
            }
            "--model" => {
                i += 1;
                model = args.get(i).and_then(|s| s.parse::<f64>().ok());
            }
            "--lint" => {
                i += 1;
                lint_file = args.get(i).cloned();
            }
            "--help" | "-h" => {
                eprintln!("MPowerTCX {} - Convert indoor bike CSV to TCX", mpowertcx_core::VERSION);
                eprintln!();
                eprintln!("Usage: mpowertcx --csv <FILE> --tcx <FILE> [OPTIONS]");
                eprintln!("       mpowertcx --lint <FILE>");
                eprintln!();
                eprintln!("Options:");
                eprintln!("  --csv <FILE>       Input CSV file");
                eprintln!("  --tcx <FILE>       Output TCX file");
                eprintln!("  --time <TIME>      Workout start time");
                eprintln!("  --interpolate      Produce samples at 1-second intervals");
                eprintln!("  --model <MASS_KG>  Use physics model for speed/distance");
                eprintln!("  --lint <FILE>      Lint a TCX file for data quality issues");
                exit(0);
            }
            _ => {
                eprintln!("Unknown argument: {}", args[i]);
                exit(1);
            }
        }
        i += 1;
    }

    if let Some(lint_path) = &lint_file {
        let data = fs::read_to_string(lint_path).expect("failed to read TCX file");
        let results = lint_tcx(&data);
        for r in &results {
            let ctx = r.context.as_deref().unwrap_or("-");
            println!("{:5} {}  {}  [{}]", r.severity, r.code, r.message, ctx);
        }
        let errors = results.iter().filter(|r| r.severity == mpowertcx_core::Severity::Error).count();
        let warns = results.iter().filter(|r| r.severity == mpowertcx_core::Severity::Warning).count();
        eprintln!("{} error(s), {} warning(s)", errors, warns);
        if has_errors(&results) {
            exit(1);
        }
        exit(0);
    }

    let csv_path = csv_file.expect("--csv is required");
    let tcx_path = tcx_file.expect("--tcx is required");

    let data = fs::read(&csv_path).expect("failed to read CSV file");

    let converter = Converter::from_csv(&data).expect("failed to parse CSV file");

    let start_time = if let Some(ref ts) = time_str {
        parse_time(ts).expect("failed to parse time")
    } else if let Some(hint) = converter.date_hint() {
        hint
    } else {
        let metadata = fs::metadata(&csv_path).expect("failed to get file metadata");
        let modified = metadata.modified().expect("failed to get modification time");
        let dt = modified.duration_since(std::time::UNIX_EPOCH).expect("time error");
        chrono::DateTime::from_timestamp(dt.as_secs() as i64, 0).expect("invalid timestamp").naive_local()
    };

    let options = ConvertOptions {
        interpolate,
        physics: model.is_some(),
        physics_mass_kg: model.unwrap_or(0.0),
        power_adjust_percent: 0.0,
    };

    let tcx = converter.convert(start_time, &options);
    fs::write(&tcx_path, tcx).expect("failed to write TCX file");

    eprintln!("Converted {} -> {} ({} samples, {})",
        csv_path, tcx_path, converter.count(), converter.equipment_name());
}
