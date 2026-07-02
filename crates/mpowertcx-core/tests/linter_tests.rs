use mpowertcx_core::linter::{has_errors, lint_tcx, Severity};

fn codes(results: &[mpowertcx_core::LintResult]) -> Vec<&str> {
    results.iter().map(|r| r.code).collect()
}

fn error_codes(results: &[mpowertcx_core::LintResult]) -> Vec<&str> {
    results
        .iter()
        .filter(|r| r.severity == Severity::Error)
        .map(|r| r.code)
        .collect()
}

// ---------------------------------------------------------------------------
// Non-interpolated samples should have zero errors
// ---------------------------------------------------------------------------

fn read_sample(name: &str) -> String {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("samples")
        .join(name);
    std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {}", path.display(), e))
}

#[test]
fn test_clean_samples_no_errors() {
    let clean = [
        "MPower33.tcx",
        "STAGES01.tcx",
        "STAGES16.tcx",
        "MPower88.tcx",
        "MPower14.tcx",
        "MPower27.tcx",
        "sufferfest.tcx",
        "bmstages02.tcx",
        "bmstages06.tcx",
        "cordis.tcx",
        "1122.tcx",
        "1214.tcx",
        "wahoo_systm_activity.tcx",
        "echelon1 workout.tcx",
        "stages_header_at_end.tcx",
        "STAGES01-no-header.tcx",
        "v1_no_header.tcx",
        "STAGES28null.tcx",
        "stagesnul.tcx",
        "c56c4102-0555-4144-8c74-2a00be281cfb.tcx",
        "STAGES18.tcx",
        "STAGES98.tcx",
        "STAGES01-JS.tcx",
        "MPower1RJ.tcx",
    ];

    for name in &clean {
        let xml = read_sample(name);
        let results = lint_tcx(&xml);
        let errs = error_codes(&results);
        assert!(errs.is_empty(), "{} has errors: {:?}", name, errs);
    }
}

#[test]
fn test_nothing_tcx_clean() {
    let xml = read_sample("nothing.tcx");
    let results = lint_tcx(&xml);
    assert!(!has_errors(&results), "nothing.tcx should have no errors");
    let codes = codes(&results);
    // Empty track but TotalTimeSeconds=0, so W023 should not fire
    assert!(!codes.contains(&"W023"), "W023 should not fire when TotalTimeSeconds=0");
}

// ---------------------------------------------------------------------------
// Interpolated samples should have warnings (known interpolation artifacts)
// ---------------------------------------------------------------------------

#[test]
fn test_interp_negative_watts_detected() {
    let xml = read_sample("c56c4102-0555-4144-8c74-2a00be281cfb_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"E030"),
        "c56c4102_interp should have negative Watts (E030)"
    );
}

#[test]
fn test_interp_negative_distance_detected() {
    let xml = read_sample("MPower33_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"E036"),
        "MPower33_interp should have negative distance (E036)"
    );
}

#[test]
fn test_interp_distance_backwards_detected() {
    let xml = read_sample("MPower33_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"E035"),
        "MPower33_interp should have distance going backwards (E035)"
    );
}

#[test]
fn test_interp_power_whipsaw_detected() {
    let xml = read_sample("c56c4102-0555-4144-8c74-2a00be281cfb_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"W032"),
        "c56c4102_interp should have power whipsaw (W032)"
    );
}

#[test]
fn test_interp_hr_zero_detected() {
    let xml = read_sample("MPower33_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"W021"),
        "MPower33_interp should have HR=0 warnings (W021)"
    );
}

#[test]
fn test_interp_implausible_hr_change_detected() {
    let xml = read_sample("MPower33_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"W038"),
        "MPower33_interp should have implausible HR change (W038)"
    );
}

#[test]
fn test_interp_negative_zero_distance_detected() {
    let xml = read_sample("stagesnul_interp.tcx");
    let results = lint_tcx(&xml);
    let codes = codes(&results);
    assert!(
        codes.contains(&"W037"),
        "stagesnul_interp should have negative-zero distance (W037)"
    );
}

// ---------------------------------------------------------------------------
// Synthetic broken TCX for individual error codes
// ---------------------------------------------------------------------------

fn minimal_tcx(body: &str) -> String {
    let header = "<?xml version='1.0' encoding='utf-8'?>\n\
<TrainingCenterDatabase xmlns=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2\">\n\
  <Activities>\n    <Activity Sport=\"Biking\">\n";
    let footer = "    </Activity>\n  </Activities>\n</TrainingCenterDatabase>\n";
    format!("{}{}{}", header, body, footer)
}

fn one_lap(trackpoints: &str) -> String {
    format!(
        "      <Id>2010-10-19T20:56:35Z</Id>\n\
         <Lap StartTime=\"2010-10-19T20:56:35Z\">\n\
         <TotalTimeSeconds>100</TotalTimeSeconds>\n\
         <DistanceMeters>1000.0</DistanceMeters>\n\
         <MaximumSpeed>0</MaximumSpeed>\n\
         <Calories>0</Calories>\n\
         <AverageHeartRateBpm><Value>150</Value></AverageHeartRateBpm>\n\
         <MaximumHeartRateBpm><Value>160</Value></MaximumHeartRateBpm>\n\
         <Intensity>Active</Intensity>\n\
         <Cadence>0</Cadence>\n\
         <TriggerMethod>Manual</TriggerMethod>\n\
         <Track>\n{}\n        </Track>\n      </Lap>\n",
        trackpoints
    )
}

fn tp(_idx: usize, time: &str, hr: i64, cad: i64, dist: &str, watts: i64) -> String {
    format!(
        "          <Trackpoint>\n\
         <Time>{}</Time>\n\
         <HeartRateBpm><Value>{}</Value></HeartRateBpm>\n\
         <Cadence>{}</Cadence>\n\
         <DistanceMeters>{}</DistanceMeters>\n\
         <Extensions><TPX xmlns=\"http://www.garmin.com/xmlschemas/ActivityExtension/v2\"><Watts>{}</Watts></TPX></Extensions>\n\
         </Trackpoint>",
        time, hr, cad, dist, watts
    )
}

#[test]
fn test_valid_minimal_tcx() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 130, 80, "10.0", 150)));
    let results = lint_tcx(&xml);
    assert!(!has_errors(&results), "valid TCX should have no errors: {:?}", error_codes(&results));
}

#[test]
fn test_broken_xml() {
    let xml = "<?xml version='1.0'?><Broken><NoClose>";
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E001"), "broken XML should trigger E001");
}

#[test]
fn test_missing_namespace() {
    let xml = "<?xml version='1.0'?>\n<TrainingCenterDatabase xmlns=\"http://wrong.namespace.com\">\n  <Activities/>\n</TrainingCenterDatabase>";
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E002"), "wrong namespace should trigger E002");
}

#[test]
fn test_no_activity() {
    let xml = "<?xml version='1.0'?>\n<TrainingCenterDatabase xmlns=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2\">\n  <Activities/>\n</TrainingCenterDatabase>";
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E003"), "no Activity should trigger E003");
}

#[test]
fn test_no_sport_attribute() {
    let xml = "<?xml version='1.0'?>\n<TrainingCenterDatabase xmlns=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2\">\n  <Activities><Activity></Activity></Activities>\n</TrainingCenterDatabase>";
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E003"), "missing Sport attribute should trigger E003");
}

#[test]
fn test_invalid_id_datetime() {
    let xml = minimal_tcx(
        "      <Id>not-a-date</Id>\n      <Lap StartTime=\"not-a-date\">\n\
         <TotalTimeSeconds>100</TotalTimeSeconds>\n\
         <DistanceMeters>1000.0</DistanceMeters>\n\
         <Track></Track>\n      </Lap>\n"
    );
    let results = lint_tcx(&xml);
    let c = codes(&results);
    assert!(c.contains(&"E005"), "invalid Id datetime should trigger E005");
}

#[test]
fn test_negative_watts() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 130, 80, "10.0", -50)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E030"), "negative Watts should trigger E030");
}

#[test]
fn test_absurd_watts() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 130, 80, "10.0", 3000)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"W019"), "absurd Watts should trigger W019");
}

#[test]
fn test_negative_distance() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 130, 80, "-5.0", 150)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E036"), "negative distance should trigger E036");
}

#[test]
fn test_distance_backwards() {
    let trackpoints = format!(
        "{}\n{}",
        tp(0, "2010-10-19T20:56:35Z", 130, 80, "100.0", 150),
        tp(1, "2010-10-19T20:56:36Z", 130, 80, "50.0", 150)
    );
    let xml = minimal_tcx(&one_lap(&trackpoints));
    let results = lint_tcx(&xml);
    let c = codes(&results);
    assert!(c.contains(&"E035"), "distance backwards should trigger E035");
    assert!(c.contains(&"E034"), "power+distance reversed should trigger E034");
}

#[test]
fn test_power_flat_distance() {
    let trackpoints = format!(
        "{}\n{}",
        tp(0, "2010-10-19T20:56:35Z", 130, 80, "100.0", 150),
        tp(1, "2010-10-19T20:56:36Z", 130, 80, "100.0", 150)
    );
    let xml = minimal_tcx(&one_lap(&trackpoints));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"W033"), "power+flat distance should trigger W033");
}

#[test]
fn test_time_backwards() {
    let trackpoints = format!(
        "{}\n{}",
        tp(0, "2010-10-19T20:56:36Z", 130, 80, "10.0", 150),
        tp(1, "2010-10-19T20:56:35Z", 130, 80, "20.0", 150)
    );
    let xml = minimal_tcx(&one_lap(&trackpoints));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"E010"), "time backwards should trigger E010");
}

#[test]
fn test_hr_zero_warning() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 0, 80, "10.0", 150)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"W021"), "HR=0 should trigger W021");
}

#[test]
fn test_all_zero_trackpoint() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 0, 0, "10.0", 0)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"W020"), "all-zero trackpoint should trigger W020");
}

#[test]
fn test_hr_out_of_range() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 250, 80, "10.0", 150)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"W017"), "HR>220 should trigger W017");
}

#[test]
fn test_cadence_out_of_range() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 130, 250, "10.0", 150)));
    let results = lint_tcx(&xml);
    assert!(codes(&results).contains(&"W018"), "cadence>200 should trigger W018");
}

#[test]
fn test_implausible_hr_change() {
    let trackpoints = format!(
        "{}\n{}",
        tp(0, "2010-10-19T20:56:35Z", 130, 80, "10.0", 150),
        tp(1, "2010-10-19T20:56:36Z", 160, 80, "20.0", 150)
    );
    let xml = minimal_tcx(&one_lap(&trackpoints));
    let results = lint_tcx(&xml);
    assert!(
        codes(&results).contains(&"W038"),
        "30 bpm/sec HR change should trigger W038"
    );
}

#[test]
fn test_power_whipsaw() {
    let trackpoints = format!(
        "{}\n{}",
        tp(0, "2010-10-19T20:56:35Z", 130, 80, "10.0", 150),
        tp(1, "2010-10-19T20:56:36Z", 130, 80, "20.0", 350)
    );
    let xml = minimal_tcx(&one_lap(&trackpoints));
    let results = lint_tcx(&xml);
    assert!(
        codes(&results).contains(&"W032"),
        "200 W/s change should trigger W032"
    );
}

#[test]
fn test_empty_track_with_time() {
    let xml = minimal_tcx(
        "      <Id>2010-10-19T20:56:35Z</Id>\n\
         <Lap StartTime=\"2010-10-19T20:56:35Z\">\n\
         <TotalTimeSeconds>3000</TotalTimeSeconds>\n\
         <DistanceMeters>1000.0</DistanceMeters>\n\
         <MaximumSpeed>0</MaximumSpeed>\n\
         <Calories>0</Calories>\n\
         <AverageHeartRateBpm><Value>0</Value></AverageHeartRateBpm>\n\
         <MaximumHeartRateBpm><Value>0</Value></MaximumHeartRateBpm>\n\
         <Intensity>Active</Intensity>\n\
         <Cadence>0</Cadence>\n\
         <TriggerMethod>Manual</TriggerMethod>\n\
         <Track></Track>\n      </Lap>\n"
    );
    let results = lint_tcx(&xml);
    assert!(
        codes(&results).contains(&"W023"),
        "empty track with TotalTimeSeconds>0 should trigger W023"
    );
}

#[test]
fn test_lap_starttime_mismatch() {
    let xml = minimal_tcx(
        "      <Id>2010-10-19T20:56:35Z</Id>\n\
         <Lap StartTime=\"2010-10-20T10:00:00Z\">\n\
         <TotalTimeSeconds>100</TotalTimeSeconds>\n\
         <DistanceMeters>1000.0</DistanceMeters>\n\
         <MaximumSpeed>0</MaximumSpeed>\n\
         <Calories>0</Calories>\n\
         <AverageHeartRateBpm><Value>150</Value></AverageHeartRateBpm>\n\
         <MaximumHeartRateBpm><Value>160</Value></MaximumHeartRateBpm>\n\
         <Intensity>Active</Intensity>\n\
         <Cadence>0</Cadence>\n\
         <TriggerMethod>Manual</TriggerMethod>\n\
         <Track></Track>\n      </Lap>\n"
    );
    let results = lint_tcx(&xml);
    assert!(
        codes(&results).contains(&"E012"),
        "StartTime != Id should trigger E012"
    );
}

#[test]
fn test_avg_hr_gt_max_hr() {
    let xml = minimal_tcx(
        "      <Id>2010-10-19T20:56:35Z</Id>\n\
         <Lap StartTime=\"2010-10-19T20:56:35Z\">\n\
         <TotalTimeSeconds>100</TotalTimeSeconds>\n\
         <DistanceMeters>1000.0</DistanceMeters>\n\
         <MaximumSpeed>0</MaximumSpeed>\n\
         <Calories>0</Calories>\n\
         <AverageHeartRateBpm><Value>160</Value></AverageHeartRateBpm>\n\
         <MaximumHeartRateBpm><Value>150</Value></MaximumHeartRateBpm>\n\
         <Intensity>Active</Intensity>\n\
         <Cadence>0</Cadence>\n\
         <TriggerMethod>Manual</TriggerMethod>\n\
         <Track></Track>\n      </Lap>\n"
    );
    let results = lint_tcx(&xml);
    assert!(
        codes(&results).contains(&"W016"),
        "avg HR > max HR should trigger W016"
    );
}

#[test]
fn test_negative_zero_distance() {
    let xml = minimal_tcx(&one_lap(&tp(0, "2010-10-19T20:56:35Z", 130, 80, "-0.00000", 150)));
    let results = lint_tcx(&xml);
    assert!(
        codes(&results).contains(&"W037"),
        "negative-zero distance format should trigger W037"
    );
}