use crate::ride::{python_float, Ride};
use chrono::{Datelike, NaiveDateTime, Timelike};

fn format_time(dt: NaiveDateTime) -> String {
    format!(
        "{}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        dt.year(),
        dt.month(),
        dt.day(),
        dt.hour(),
        dt.minute(),
        dt.second(),
    )
}

pub fn render_tcx(ride: &Ride, start_time: NaiveDateTime, power_fudge: f64) -> String {
    let now = format_time(start_time);

    let secs_per_sample = ride.delta().max(1.0) as i64;

    // Lap summary must describe the track we actually emit, not the raw source
    // header. The last trackpoint sits at (count - 1) * secs_per_sample seconds,
    // and the lap distance is the final trackpoint's cumulative distance.
    let lap_total_seconds = if ride.count() > 1 {
        (ride.count() as i64 - 1) * secs_per_sample
    } else {
        0
    };
    let lap_distance = ride
        .distance
        .last()
        .and_then(|d| d.parse::<f64>().ok())
        .unwrap_or(ride.header.distance);

    let mut out = String::new();
    out.push_str("<?xml version='1.0' encoding='utf-8'?>\n");
    out.push_str("<TrainingCenterDatabase xmlns:ns2=\"http://www.garmin.com/xmlschemas/UserProfile/v2\" xmlns:ns3=\"http://www.garmin.com/xmlschemas/ActivityExtension/v2\" xmlns:ns5=\"http://www.garmin.com/xmlschemas/ActivityGoals/v1\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2\" xsi:schemaLocation=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd\">\n");
    out.push_str("  <Activities>\n");
    out.push_str("    <Activity Sport=\"Biking\">\n");
    out.push_str(&format!("      <Id>{}</Id>\n", now));
    out.push_str(&format!("      <Lap StartTime=\"{}\">\n", now));
    out.push_str(&format!("        <TotalTimeSeconds>{}</TotalTimeSeconds>\n", lap_total_seconds));
    out.push_str(&format!("        <DistanceMeters>{:.5}</DistanceMeters>\n", lap_distance));
    out.push_str("        <MaximumSpeed>0</MaximumSpeed>\n");
    out.push_str("        <Calories>0</Calories>\n");
    out.push_str("        <AverageHeartRateBpm>\n");
    out.push_str(&format!("          <Value>{}</Value>\n", ride.header.average_hr));
    out.push_str("        </AverageHeartRateBpm>\n");
    out.push_str("        <MaximumHeartRateBpm>\n");
    out.push_str(&format!("          <Value>{}</Value>\n", ride.header.max_hr));
    out.push_str("        </MaximumHeartRateBpm>\n");
    out.push_str("        <Intensity>Active</Intensity>\n");
    out.push_str("        <Cadence>0</Cadence>\n");
    out.push_str("        <TriggerMethod>Manual</TriggerMethod>\n");
    out.push_str("        <Track>\n");

    let altitudes: Vec<f64> = if !ride.altitude.is_empty() && ride.altitude.len() == ride.count() {
        ride.altitude.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect()
    } else if !ride.incline.is_empty() && ride.incline.len() == ride.count() {
        let mut alts = Vec::with_capacity(ride.count());
        let mut elev = 0.0f64;
        let mut prev_dist = 0.0f64;
        for i in 0..ride.count() {
            if i > 0 {
                let dist = ride.distance[i].parse::<f64>().unwrap_or(0.0);
                let incline = ride.incline[i].parse::<f64>().unwrap_or(0.0);
                elev += (incline / 100.0) * (dist - prev_dist);
                prev_dist = dist;
            } else {
                prev_dist = ride.distance[0].parse::<f64>().unwrap_or(0.0);
            }
            alts.push(elev);
        }
        alts
    } else {
        Vec::new()
    };

    for i in 0..ride.count() {
        let delta_time = start_time + chrono::Duration::seconds(i as i64 * secs_per_sample);
        let time_str = format_time(delta_time);
        let power = ride.power[i].parse::<f64>().unwrap_or(0.0) * power_fudge;
        let watts = power as i64;
        let distance = ride.distance[i].parse::<f64>().unwrap_or(0.0);

        out.push_str("          <Trackpoint>\n");
        out.push_str(&format!("            <Time>{}</Time>\n", time_str));
        if !altitudes.is_empty() {
            out.push_str(&format!("            <AltitudeMeters>{}</AltitudeMeters>\n", python_float(altitudes[i])));
        }
        out.push_str("            <HeartRateBpm>\n");
        out.push_str(&format!("              <Value>{}</Value>\n", ride.hr[i]));
        out.push_str("            </HeartRateBpm>\n");
        out.push_str(&format!("            <Cadence>{}</Cadence>\n", ride.rpm[i]));
        out.push_str(&format!("            <DistanceMeters>{:.5}</DistanceMeters>\n", distance));
        out.push_str("            <Extensions>\n");
        out.push_str("              <TPX xmlns=\"http://www.garmin.com/xmlschemas/ActivityExtension/v2\">\n");
        out.push_str(&format!("                <Watts>{}</Watts>\n", watts));
        out.push_str("              </TPX>\n");
        out.push_str("            </Extensions>\n");
        out.push_str("          </Trackpoint>\n");
    }

    out.push_str("        </Track>\n");
    out.push_str("      </Lap>\n");
    out.push_str("    </Activity>\n");
    out.push_str("  </Activities>\n");
    out.push_str("</TrainingCenterDatabase>\n");

    out
}
