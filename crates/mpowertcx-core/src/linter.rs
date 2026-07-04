use quick_xml::escape::unescape;
use quick_xml::events::Event;
use quick_xml::Reader;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Severity {
    Error,
    Warning,
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Severity::Error => write!(f, "ERROR"),
            Severity::Warning => write!(f, "WARN"),
        }
    }
}

#[derive(Debug)]
pub struct LintResult {
    pub severity: Severity,
    pub code: &'static str,
    pub message: String,
    pub context: Option<String>,
}

impl LintResult {
    fn error(code: &'static str, msg: impl Into<String>, ctx: Option<String>) -> Self {
        Self { severity: Severity::Error, code, message: msg.into(), context: ctx }
    }
    fn warn(code: &'static str, msg: impl Into<String>, ctx: Option<String>) -> Self {
        Self { severity: Severity::Warning, code, message: msg.into(), context: ctx }
    }
}

pub fn lint_tcx(tcx_xml: &str) -> Vec<LintResult> {
    let mut results = Vec::new();

    let parsed = match parse(tcx_xml) {
        Ok(p) => p,
        Err(e) => {
            results.push(LintResult::error(
                "E001",
                format!("XML parse error: {}", e),
                None,
            ));
            return results;
        }
    };

    check_structure(&parsed, &mut results);
    check_trackpoint_data(&parsed, &mut results);

    results
}

pub fn has_errors(results: &[LintResult]) -> bool {
    results.iter().any(|r| r.severity == Severity::Error)
}

// ---------------------------------------------------------------------------
// Parsed data structures
// ---------------------------------------------------------------------------

#[derive(Default)]
struct ParsedTcx {
    root_name: Option<String>,
    has_tcx_ns: bool,
    activities: Vec<ParsedActivity>,
}

#[derive(Default)]
struct ParsedActivity {
    sport: Option<String>,
    id: Option<String>,
    laps: Vec<ParsedLap>,
}

#[derive(Default)]
struct ParsedLap {
    start_time: Option<String>,
    total_time_seconds: Option<String>,
    distance_meters: Option<String>,
    maximum_speed: Option<String>,
    calories: Option<String>,
    average_hr: Option<String>,
    maximum_hr: Option<String>,
    intensity: Option<String>,
    cadence: Option<String>,
    trigger_method: Option<String>,
    has_track: bool,
    trackpoints: Vec<ParsedTrackpoint>,
}

struct ParsedTrackpoint {
    index: usize,
    time: Option<String>,
    hr: Option<i64>,
    cadence: Option<i64>,
    distance_meters: Option<f64>,
    distance_raw: String,
    watts: Option<i64>,
}

impl Default for ParsedTrackpoint {
    fn default() -> Self {
        Self {
            index: 0,
            time: None,
            hr: None,
            cadence: None,
            distance_meters: None,
            distance_raw: String::new(),
            watts: None,
        }
    }
}

// ---------------------------------------------------------------------------
// XML parsing
// ---------------------------------------------------------------------------

fn parse(xml: &str) -> Result<ParsedTcx, String> {
    let mut reader = Reader::from_str(xml);
    reader.config_mut().trim_text(true);

    let mut buf = Vec::new();
    let mut path: Vec<String> = Vec::new();
    let mut text = String::new();

    let mut tcx = ParsedTcx::default();
    let mut cur_activity: Option<ParsedActivity> = None;
    let mut cur_lap: Option<ParsedLap> = None;
    let mut cur_tp: Option<ParsedTrackpoint> = None;
    let mut tp_counter: usize = 0;

    loop {
        buf.clear();
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = local_name(e.name().as_ref());
                path.push(name.clone());
                text.clear();

                match name.as_str() {
                    "TrainingCenterDatabase" => {
                        tcx.root_name = Some(name.clone());
                        for attr in e.attributes().flatten() {
                            if attr.key.as_ref() == b"xmlns" {
                                let val = String::from_utf8_lossy(&attr.value);
                                if val.contains("TrainingCenterDatabase/v2") {
                                    tcx.has_tcx_ns = true;
                                }
                            }
                        }
                    }
                    "Activity" => {
                        let sport = e
                            .attributes()
                            .flatten()
                            .find(|a| attr_name(a.key.as_ref()) == "Sport")
                            .map(|a| String::from_utf8_lossy(&a.value).to_string());
                        cur_activity = Some(ParsedActivity { sport, ..Default::default() });
                    }
                    "Lap" => {
                        let start_time = e
                            .attributes()
                            .flatten()
                            .find(|a| attr_name(a.key.as_ref()) == "StartTime")
                            .map(|a| String::from_utf8_lossy(&a.value).to_string());
                        cur_lap = Some(ParsedLap { start_time, ..Default::default() });
                        tp_counter = 0;
                    }
                    "Track" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.has_track = true;
                        }
                    }
                    "Trackpoint" => {
                        cur_tp = Some(ParsedTrackpoint { index: tp_counter, ..Default::default() });
                    }
                    _ => {}
                }
            }
            Ok(Event::Text(t)) => {
                let decoded = t.decode().map_err(|e| e.to_string())?;
                text.push_str(&unescape(&decoded).map_err(|e| e.to_string())?);
            }
            Ok(Event::End(e)) => {
                let name = local_name(e.name().as_ref());
                let val = text.trim().to_string();
                let parent = path
                    .get(path.len().saturating_sub(2))
                    .map(|s| s.as_str())
                    .unwrap_or("");

                match name.as_str() {
                    "Id" => {
                        if let Some(act) = &mut cur_activity {
                            act.id = Some(val.clone());
                        }
                    }
                    "Time" => {
                        if let Some(tp) = &mut cur_tp {
                            tp.time = Some(val.clone());
                        }
                    }
                    "TotalTimeSeconds" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.total_time_seconds = Some(val.clone());
                        }
                    }
                    "DistanceMeters" => {
                        if let Some(tp) = &mut cur_tp {
                            tp.distance_raw = val.clone();
                            tp.distance_meters = val.parse::<f64>().ok();
                        } else if let Some(lap) = &mut cur_lap {
                            lap.distance_meters = Some(val.clone());
                        }
                    }
                    "MaximumSpeed" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.maximum_speed = Some(val.clone());
                        }
                    }
                    "Calories" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.calories = Some(val.clone());
                        }
                    }
                    "Value" => match parent {
                        "AverageHeartRateBpm" => {
                            if let Some(lap) = &mut cur_lap {
                                lap.average_hr = Some(val.clone());
                            }
                        }
                        "MaximumHeartRateBpm" => {
                            if let Some(lap) = &mut cur_lap {
                                lap.maximum_hr = Some(val.clone());
                            }
                        }
                        "HeartRateBpm" => {
                            if let Some(tp) = &mut cur_tp {
                                tp.hr = parse_num(&val);
                            }
                        }
                        _ => {}
                    },
                    "Cadence" => {
                        if let Some(tp) = &mut cur_tp {
                            tp.cadence = parse_num(&val);
                        } else if let Some(lap) = &mut cur_lap {
                            lap.cadence = Some(val.clone());
                        }
                    }
                    "Intensity" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.intensity = Some(val.clone());
                        }
                    }
                    "TriggerMethod" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.trigger_method = Some(val.clone());
                        }
                    }
                    "Watts" => {
                        if let Some(tp) = &mut cur_tp {
                            tp.watts = parse_num(&val);
                        }
                    }
                    "Trackpoint" => {
                        if let Some(tp) = cur_tp.take() {
                            tp_counter += 1;
                            if let Some(lap) = &mut cur_lap {
                                lap.trackpoints.push(tp);
                            }
                        }
                    }
                    "Lap" => {
                        if let Some(lap) = cur_lap.take() {
                            if let Some(act) = &mut cur_activity {
                                act.laps.push(lap);
                            }
                        }
                    }
                    "Activity" => {
                        if let Some(act) = cur_activity.take() {
                            tcx.activities.push(act);
                        }
                    }
                    _ => {}
                }

                path.pop();
                text.clear();
            }
            Ok(Event::Empty(e)) => {
                let name = local_name(e.name().as_ref());

                match name.as_str() {
                    "Track" => {
                        if let Some(lap) = &mut cur_lap {
                            lap.has_track = true;
                        }
                    }
                    "Trackpoint" => {
                        if let Some(lap) = &mut cur_lap {
                            let tp = ParsedTrackpoint { index: tp_counter, ..Default::default() };
                            tp_counter += 1;
                            lap.trackpoints.push(tp);
                        }
                    }
                    "Activity" => {
                        let sport = e
                            .attributes()
                            .flatten()
                            .find(|a| attr_name(a.key.as_ref()) == "Sport")
                            .map(|a| String::from_utf8_lossy(&a.value).to_string());
                        tcx.activities.push(ParsedActivity { sport, ..Default::default() });
                    }
                    "Lap" => {
                        let start_time = e
                            .attributes()
                            .flatten()
                            .find(|a| attr_name(a.key.as_ref()) == "StartTime")
                            .map(|a| String::from_utf8_lossy(&a.value).to_string());
                        let lap = ParsedLap { start_time, ..Default::default() };
                        if let Some(act) = &mut cur_activity {
                            act.laps.push(lap);
                        }
                    }
                    _ => {}
                }
            }
            Ok(Event::Eof) => break,
            Ok(_) => {}
            Err(e) => return Err(e.to_string()),
        }
    }

    if !path.is_empty() {
        return Err(format!("unclosed element: {}", path.join(" > ")));
    }

    Ok(tcx)
}

fn local_name(bytes: &[u8]) -> String {
    let s = String::from_utf8_lossy(bytes);
    match s.rsplit_once(':') {
        Some((_, local)) => local.to_string(),
        None => s.to_string(),
    }
}

fn attr_name(key: &[u8]) -> String {
    local_name(key)
}

fn parse_num(val: &str) -> Option<i64> {
    val.parse::<i64>()
        .ok()
        .or_else(|| val.parse::<f64>().ok().map(|f| f as i64))
}

// ---------------------------------------------------------------------------
// Time parsing helper
// ---------------------------------------------------------------------------

fn parse_tcx_time(s: &str) -> Option<i64> {
    let s = s.trim();
    let s = s.strip_suffix('Z').unwrap_or(s);
    let dt = chrono::NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f")
        .or_else(|_| chrono::NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S"))
        .ok()?;
    Some(dt.and_utc().timestamp())
}

fn median(v: &[i64]) -> Option<i64> {
    if v.is_empty() {
        return None;
    }
    let mut sorted: Vec<i64> = v.to_vec();
    sorted.sort_unstable();
    let mid = sorted.len() / 2;
    if sorted.len() % 2 == 0 {
        Some((sorted[mid - 1] + sorted[mid]) / 2)
    } else {
        Some(sorted[mid])
    }
}

// ---------------------------------------------------------------------------
// Structure checks (E001-E012)
// ---------------------------------------------------------------------------

fn check_structure(tcx: &ParsedTcx, results: &mut Vec<LintResult>) {
    if !tcx.has_tcx_ns {
        let root = tcx.root_name.as_deref().unwrap_or("(none)");
        results.push(LintResult::error(
            "E002",
            format!(
                "Root element '{}' is not TrainingCenterDatabase with TCXv2 namespace",
                root
            ),
            None,
        ));
    }

    if tcx.activities.is_empty() {
        results.push(LintResult::error("E003", "No Activity element found", None));
    }

    for (i, act) in tcx.activities.iter().enumerate() {
        let act_ctx = format!("Activity #{}", i);

        if act.sport.is_none() {
            results.push(LintResult::error(
                "E003",
                "Activity has no Sport attribute",
                Some(act_ctx.clone()),
            ));
        }

        match &act.id {
            None => {
                results.push(LintResult::error(
                    "E005",
                    "Activity Id missing",
                    Some(act_ctx.clone()),
                ));
            }
            Some(id) => {
                if parse_tcx_time(id).is_none() {
                    results.push(LintResult::error(
                        "E005",
                        format!("Activity Id '{}' is not a valid datetime", id),
                        Some(act_ctx.clone()),
                    ));
                }
            }
        }

        if act.laps.is_empty() {
            results.push(LintResult::error(
                "E004",
                "No Lap element found",
                Some(act_ctx.clone()),
            ));
        }

        for (j, lap) in act.laps.iter().enumerate() {
            let lap_ctx = format!("Activity #{}, Lap #{}", i, j);

            if lap.start_time.is_none() {
                results.push(LintResult::error(
                    "E004",
                    "Lap has no StartTime attribute",
                    Some(lap_ctx.clone()),
                ));
            }

            match &lap.total_time_seconds {
                None => {
                    results.push(LintResult::error(
                        "E006",
                        "TotalTimeSeconds missing",
                        Some(lap_ctx.clone()),
                    ));
                }
                Some(v) => match v.parse::<f64>() {
                    Ok(n) if n < 0.0 => {
                        results.push(LintResult::error(
                            "E006",
                            format!("TotalTimeSeconds is negative: {}", v),
                            Some(lap_ctx.clone()),
                        ));
                    }
                    Err(_) => {
                        results.push(LintResult::error(
                            "E006",
                            format!("TotalTimeSeconds is not numeric: '{}'", v),
                            Some(lap_ctx.clone()),
                        ));
                    }
                    Ok(_) => {}
                },
            }

            match &lap.distance_meters {
                None => {
                    results.push(LintResult::error(
                        "E007",
                        "Lap DistanceMeters missing",
                        Some(lap_ctx.clone()),
                    ));
                }
                Some(v) => match v.parse::<f64>() {
                    Ok(n) if n < 0.0 => {
                        results.push(LintResult::error(
                            "E007",
                            format!("Lap DistanceMeters is negative: {}", v),
                            Some(lap_ctx.clone()),
                        ));
                    }
                    Err(_) => {
                        results.push(LintResult::error(
                            "E007",
                            format!("Lap DistanceMeters is not numeric: '{}'", v),
                            Some(lap_ctx.clone()),
                        ));
                    }
                    Ok(_) => {}
                },
            }

            if !lap.has_track {
                results.push(LintResult::error(
                    "E008",
                    "No Track element found in Lap",
                    Some(lap_ctx.clone()),
                ));
            }

            if let (Some(id), Some(st)) = (&act.id, &lap.start_time) {
                if id != st {
                    results.push(LintResult::error(
                        "E012",
                        format!(
                            "Lap StartTime '{}' does not match Activity Id '{}'",
                            st, id
                        ),
                        Some(lap_ctx.clone()),
                    ));
                }
            }

            let total_secs = lap
                .total_time_seconds
                .as_deref()
                .and_then(|s| s.parse::<f64>().ok())
                .unwrap_or(0.0);
            if lap.has_track && lap.trackpoints.is_empty() && total_secs > 0.0 {
                results.push(LintResult::warn(
                    "W023",
                    "Track is empty but TotalTimeSeconds > 0",
                    Some(lap_ctx.clone()),
                ));
            }

            let avg_hr = lap.average_hr.as_deref().and_then(|s| s.parse::<i64>().ok());
            let max_hr = lap.maximum_hr.as_deref().and_then(|s| s.parse::<i64>().ok());
            if let (Some(avg), Some(max)) = (avg_hr, max_hr) {
                if avg > 0 && max > 0 && avg > max {
                    results.push(LintResult::warn(
                        "W016",
                        format!(
                            "AverageHeartRateBpm ({}) > MaximumHeartRateBpm ({})",
                            avg, max
                        ),
                        Some(lap_ctx.clone()),
                    ));
                }
            }

            for tp in &lap.trackpoints {
                let tp_ctx = format!("{}, Trackpoint #{}", lap_ctx, tp.index);

                let mut missing = Vec::new();
                if tp.time.is_none() {
                    missing.push("Time");
                }
                if tp.cadence.is_none() {
                    missing.push("Cadence");
                }
                if tp.distance_meters.is_none() {
                    missing.push("DistanceMeters");
                }
                if tp.watts.is_none() {
                    missing.push("Watts");
                }
                if !missing.is_empty() {
                    results.push(LintResult::error(
                        "E009",
                        format!("Trackpoint missing required field(s): {}", missing.join(", ")),
                        Some(tp_ctx),
                    ));
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Trackpoint data checks (E010, E030-E036, W013-W038)
// ---------------------------------------------------------------------------

fn check_trackpoint_data(tcx: &ParsedTcx, results: &mut Vec<LintResult>) {
    for act in &tcx.activities {
        for lap in &act.laps {
            let lap_ctx = "Lap".to_string();

            let times: Vec<Option<i64>> = lap
                .trackpoints
                .iter()
                .map(|tp| tp.time.as_deref().and_then(parse_tcx_time))
                .collect();

            // E010: Trackpoint times monotonically non-decreasing
            for i in 1..lap.trackpoints.len() {
                if let (Some(t1), Some(t2)) = (times[i - 1], times[i]) {
                    if t2 < t1 {
                        let tp = &lap.trackpoints[i];
                        let prev = &lap.trackpoints[i - 1];
                        results.push(LintResult::error(
                            "E010",
                            format!(
                                "Trackpoint time went backwards: {} -> {}",
                                prev.time.as_deref().unwrap_or("?"),
                                tp.time.as_deref().unwrap_or("?")
                            ),
                            Some(format!("Trackpoint #{}", tp.index)),
                        ));
                    }
                }
            }

            // W013: First Trackpoint Time matches Lap StartTime
            if let (Some(st), Some(first_time)) = (
                &lap.start_time,
                lap.trackpoints
                    .first()
                    .and_then(|tp| tp.time.as_deref()),
            ) {
                if st != first_time {
                    results.push(LintResult::warn(
                        "W013",
                        format!(
                            "First Trackpoint Time '{}' does not match Lap StartTime '{}'",
                            first_time, st
                        ),
                        Some("Trackpoint #0".to_string()),
                    ));
                }
            }

            // W014: TotalTimeSeconds vs trackpoint time span
            if lap.trackpoints.len() >= 2 {
                let t_first = times[0];
                let t_last = times[lap.trackpoints.len() - 1];
                if let (Some(tf), Some(tl), Some(total_str)) =
                    (t_first, t_last, &lap.total_time_seconds)
                {
                    if let Ok(total) = total_str.parse::<f64>() {
                        let span = (tl - tf) as f64;
                        let intervals: Vec<i64> = times
                            .windows(2)
                            .filter_map(|w| match (w[0], w[1]) {
                                (Some(a), Some(b)) => Some(b - a),
                                _ => None,
                            })
                            .collect();
                        let med = median(&intervals).unwrap_or(1) as f64;
                        if med > 0.0 && (span - total).abs() > med {
                            results.push(LintResult::warn(
                                "W014",
                                format!(
                                    "TotalTimeSeconds ({}) does not match trackpoint time span ({})",
                                    total, span
                                ),
                                Some(lap_ctx.clone()),
                            ));
                        }
                    }
                }
            }

            // W022: Irregular time intervals
            let intervals: Vec<i64> = times
                .windows(2)
                .filter_map(|w| match (w[0], w[1]) {
                    (Some(a), Some(b)) => Some(b - a),
                    _ => None,
                })
                .collect();
            if intervals.len() >= 3 {
                let med = median(&intervals).unwrap_or(1);
                if med > 0 {
                    for (i, &interval) in intervals.iter().enumerate() {
                        let deviation = (interval - med).abs() as f64;
                        if deviation > (med as f64 * 0.5) {
                            results.push(LintResult::warn(
                                "W022",
                                format!(
                                    "Irregular time interval: {}s (median {}s) between trackpoints #{} and #{}",
                                    interval, med, i, i + 1
                                ),
                                Some(format!("Trackpoint #{}", i + 1)),
                            ));
                        }
                    }
                }
            }

            // W015: Final DistanceMeters vs lap DistanceMeters
            if let (Some(lap_dist_str), Some(last_tp)) =
                (&lap.distance_meters, lap.trackpoints.last())
            {
                if let (Ok(lap_dist), Some(tp_dist)) =
                    (lap_dist_str.parse::<f64>(), last_tp.distance_meters)
                {
                    let tolerance = (lap_dist * 0.01).max(1.0);
                    if (lap_dist - tp_dist).abs() > tolerance {
                        results.push(LintResult::warn(
                            "W015",
                            format!(
                                "Lap DistanceMeters ({}) does not match final trackpoint distance ({})",
                                lap_dist, tp_dist
                            ),
                            Some(lap_ctx.clone()),
                        ));
                    }
                }
            }

            // Per-trackpoint checks
            for i in 0..lap.trackpoints.len() {
                let tp = &lap.trackpoints[i];
                let tp_ctx = format!("Trackpoint #{}", tp.index);

                // W017: HR out of range
                if let Some(hr) = tp.hr {
                    if hr > 220 {
                        results.push(LintResult::warn(
                            "W017",
                            format!("HeartRate {} exceeds 220", hr),
                            Some(tp_ctx.clone()),
                        ));
                    }
                }

                // W018: Cadence out of range
                if let Some(cad) = tp.cadence {
                    if cad < 0 || cad > 200 {
                        results.push(LintResult::warn(
                            "W018",
                            format!("Cadence {} out of range 0-200", cad),
                            Some(tp_ctx.clone()),
                        ));
                    }
                }

                // E030: Negative Watts
                if let Some(w) = tp.watts {
                    if w < 0 {
                        results.push(LintResult::error(
                            "E030",
                            format!("Watts is negative: {}", w),
                            Some(tp_ctx.clone()),
                        ));
                    }
                    // W019: Watts exceeds 2500
                    if w > 2500 {
                        results.push(LintResult::warn(
                            "W019",
                            format!("Watts {} exceeds 2500", w),
                            Some(tp_ctx.clone()),
                        ));
                    }
                }

                // E036: Negative distance
                if let Some(d) = tp.distance_meters {
                    if d < 0.0 {
                        results.push(LintResult::error(
                            "E036",
                            format!("DistanceMeters is negative: {}", d),
                            Some(tp_ctx.clone()),
                        ));
                    }
                }

                // W037: Negative zero distance format
                if tp.distance_raw.starts_with('-') {
                    if let Some(d) = tp.distance_meters {
                        if d.abs() < 0.001 {
                            results.push(LintResult::warn(
                                "W037",
                                format!(
                                    "DistanceMeters has negative-zero format: {}",
                                    tp.distance_raw
                                ),
                                Some(tp_ctx.clone()),
                            ));
                        }
                    }
                }

                // W020: All-zero trackpoint
                if let (Some(hr), Some(cad), Some(w)) = (tp.hr, tp.cadence, tp.watts) {
                    if hr == 0 && cad == 0 && w == 0 {
                        results.push(LintResult::warn(
                            "W020",
                            "All values zero (HR=0, Cadence=0, Watts=0)",
                            Some(tp_ctx.clone()),
                        ));
                    }
                }

                // Checks requiring previous trackpoint
                if i > 0 {
                    let prev = &lap.trackpoints[i - 1];
                    let interval = match (times[i - 1], times[i]) {
                        (Some(a), Some(b)) => ((b - a).max(1)) as f64,
                        _ => 1.0,
                    };

                    // E035: Distance went backwards
                    if let (Some(d_prev), Some(d_cur)) = (prev.distance_meters, tp.distance_meters)
                    {
                        if d_cur < d_prev {
                            results.push(LintResult::error(
                                "E035",
                                format!("Distance went backwards: {} -> {}", d_prev, d_cur),
                                Some(tp_ctx.clone()),
                            ));
                        }
                    }

                    // E034: Power applied but distance reversed
                    if let (Some(w), Some(d_prev), Some(d_cur)) =
                        (tp.watts, prev.distance_meters, tp.distance_meters)
                    {
                        if w > 0 && d_cur < d_prev {
                            results.push(LintResult::error(
                                "E034",
                                format!(
                                    "Power applied ({}W) but distance reversed: {} -> {}",
                                    w, d_prev, d_cur
                                ),
                                Some(tp_ctx.clone()),
                            ));
                        }
                    }

                    // W033: Power applied but distance flat
                    if let (Some(w), Some(d_prev), Some(d_cur)) =
                        (tp.watts, prev.distance_meters, tp.distance_meters)
                    {
                        if w > 0 && d_cur == d_prev {
                            results.push(LintResult::warn(
                                "W033",
                                format!("Power applied ({}W) but distance unchanged: {}", w, d_cur),
                                Some(tp_ctx.clone()),
                            ));
                        }
                    }

                    // W032: Power whipsaw (> 100 W/sec)
                    if let (Some(w_prev), Some(w_cur)) = (prev.watts, tp.watts) {
                        let delta = (w_cur - w_prev).abs();
                        let rate = delta as f64 / interval;
                        if rate > 100.0 {
                            results.push(LintResult::warn(
                                "W032",
                                format!(
                                    "Power whipsaw: {} -> {} ({} W in {}s = {:.0} W/s)",
                                    w_prev,
                                    w_cur,
                                    delta,
                                    interval as i64,
                                    rate
                                ),
                                Some(tp_ctx.clone()),
                            ));
                        }
                    }

                    // W038: Implausible HR change (> 10 bpm/sec)
                    if let (Some(hr_prev), Some(hr_cur)) = (prev.hr, tp.hr) {
                        let delta = (hr_cur - hr_prev).abs();
                        let rate = delta as f64 / interval;
                        if rate > 10.0 {
                            results.push(LintResult::warn(
                                "W038",
                                format!(
                                    "Implausible HR change: {} -> {} ({} bpm in {}s = {:.0} bpm/s)",
                                    hr_prev,
                                    hr_cur,
                                    delta,
                                    interval as i64,
                                    rate
                                ),
                                Some(tp_ctx.clone()),
                            ));
                        }
                    }
                }
            }
        }
    }
}