use crate::ride::Ride;
use chrono::NaiveDateTime;
use embedded_io::{ErrorType, Seek, SeekFrom, Write};
use rustyfit::profile::{mesgdef, typedef};
use rustyfit::proto::{FIT, Message};

/// Encode a workout into a Garmin FIT activity file.
///
/// Timestamps follow the same convention as the TCX renderer: samples are
/// spaced `max(ride.delta(), 1)` seconds apart from `start_time`. FIT stores
/// UTC epochs and the source times carry no timezone, so local time is
/// treated as UTC (the same ambiguity the TCX output has).
///
/// Elevation policy: only absolute altitude from the source file is emitted.
/// The grade x distance fallback is intentionally NOT written, because FIT
/// altitude resolution (0.5 m) would quantize it into noise, and re-parsing
/// that noise as real incline would make the physics model produce wild
/// speed/distance on a round trip. Instead, when the source grade is real
/// (`!incline_is_simulated`) it is written verbatim as the record `grade`
/// field (0.01% resolution), so a round trip reproduces the original repair.
/// When the grade is display-only (simulated), neither altitude nor grade is
/// emitted, so re-parsing yields no incline at all.
pub fn render_fit(
    ride: &Ride,
    start_time: NaiveDateTime,
    power_fudge: f64,
    incline_is_simulated: bool,
) -> Vec<u8> {
    let secs_per_sample = ride.delta().max(1.0) as i64;
    let count = ride.count();
    let start_secs = start_time.and_utc().timestamp();
    // Record timestamps are integer-spaced (FIT stores u32 seconds). The
    // session/lap timers carry the source header duration instead, so a
    // re-import recovers the exact original sample delta (header.time / count).
    let lap_seconds = if count > 1 {
        (count as i64 - 1) * secs_per_sample
    } else {
        0
    };
    let duration_seconds = if count > 1 {
        ride.header.time
    } else {
        0.0
    };
    let end_secs = start_secs + lap_seconds;

    let lap_distance = ride
        .distance
        .last()
        .and_then(|d| d.parse::<f64>().ok())
        .unwrap_or(ride.header.distance);

    let altitudes: Vec<f64> = if !ride.altitude.is_empty() && ride.altitude.len() == count {
        ride.altitude
            .iter()
            .map(|s| s.parse::<f64>().unwrap_or(0.0))
            .collect()
    } else {
        Vec::new()
    };
    let write_grade = !incline_is_simulated && !ride.incline.is_empty() && ride.incline.len() == count;

    let mut messages: Vec<Message> = Vec::with_capacity(count + 4);

    let mut file_id = mesgdef::FileId::new();
    file_id.r#type = typedef::File::ACTIVITY;
    file_id.manufacturer = typedef::Manufacturer::GARMIN;
    file_id.time_created = typedef::DateTime::from_unix_timestamp(start_secs);
    messages.push(Message::from(file_id));

    let mut act = mesgdef::Activity::new();
    act.timestamp = typedef::DateTime::from_unix_timestamp(start_secs);
    act.num_sessions = 1;
    act.event = typedef::Event::ACTIVITY;
    act.event_type = typedef::EventType::START;
    act.r#type = typedef::Activity::MANUAL;
    messages.push(Message::from(act));

    let (avg_power, max_power, avg_cadence, max_cadence, avg_hr, max_hr, max_speed) =
        summary_from_samples(ride, secs_per_sample, power_fudge);

    let mut session = mesgdef::Session::new();
    session.start_time = typedef::DateTime::from_unix_timestamp(start_secs);
    session.timestamp = typedef::DateTime::from_unix_timestamp(end_secs);
    session.event = typedef::Event::SESSION;
    session.event_type = typedef::EventType::START;
    session.sport = typedef::Sport::CYCLING;
    session.sub_sport = typedef::SubSport::INDOOR_CYCLING;
    session.set_total_elapsed_time_scaled(duration_seconds);
    session.set_total_timer_time_scaled(duration_seconds);
    session.set_total_distance_scaled(lap_distance);
    session.avg_heart_rate = avg_hr;
    session.max_heart_rate = max_hr;
    session.avg_cadence = avg_cadence;
    session.max_cadence = max_cadence;
    session.avg_power = avg_power;
    session.max_power = max_power;
    session.num_laps = 1;
    session.first_lap_index = 0;
    if duration_seconds > 0.0 {
        session.set_avg_speed_scaled(lap_distance / duration_seconds);
        session.set_max_speed_scaled(max_speed);
    }
    messages.push(Message::from(session));

    let mut lap = mesgdef::Lap::new();
    lap.start_time = typedef::DateTime::from_unix_timestamp(start_secs);
    lap.timestamp = typedef::DateTime::from_unix_timestamp(end_secs);
    lap.event = typedef::Event::LAP;
    lap.event_type = typedef::EventType::START;
    lap.sport = typedef::Sport::CYCLING;
    lap.sub_sport = typedef::SubSport::INDOOR_CYCLING;
    lap.intensity = typedef::Intensity::ACTIVE;
    lap.lap_trigger = typedef::LapTrigger::MANUAL;
    lap.set_total_elapsed_time_scaled(duration_seconds);
    lap.set_total_timer_time_scaled(duration_seconds);
    lap.set_total_distance_scaled(lap_distance);
    lap.avg_heart_rate = avg_hr;
    lap.max_heart_rate = max_hr;
    lap.avg_cadence = avg_cadence;
    lap.max_cadence = max_cadence;
    lap.avg_power = avg_power;
    lap.max_power = max_power;
    if duration_seconds > 0.0 {
        lap.set_avg_speed_scaled(lap_distance / duration_seconds);
        lap.set_max_speed_scaled(max_speed);
    }
    messages.push(Message::from(lap));

    let mut prev_dist = 0.0f64;
    for i in 0..count {
        let mut record = mesgdef::Record::new();
        record.timestamp =
            typedef::DateTime::from_unix_timestamp(start_secs + i as i64 * secs_per_sample);

        let power = ride.power[i].parse::<f64>().unwrap_or(0.0) * power_fudge;
        record.power = power.clamp(0.0, u16::MAX as f64) as u16;

        let cadence = ride.rpm[i].parse::<f64>().unwrap_or(0.0);
        record.cadence = cadence.max(0.0) as u8;

        let hr = ride.hr[i].parse::<f64>().unwrap_or(0.0);
        record.heart_rate = hr.max(0.0) as u8;

        let dist = ride.distance[i].parse::<f64>().unwrap_or(0.0);
        record.distance = (dist * 100.0) as u32;

        let speed = if i > 0 {
            (dist - prev_dist).max(0.0) / secs_per_sample as f64
        } else {
            0.0
        };
        record.set_speed_scaled(speed);
        prev_dist = dist;

        if !altitudes.is_empty() {
            record.set_altitude_scaled(altitudes[i]);
        }
        if write_grade {
            record.set_grade_scaled(ride.incline[i].parse::<f64>().unwrap_or(0.0));
        }

        messages.push(Message::from(record));
    }

    let mut fit = FIT {
        messages,
        ..Default::default()
    };

    let mut out = VecCursor::new();
    let mut encoder = rustyfit::Encoder::new();
    encoder
        .encode(&mut out, &mut fit)
        .expect("FIT encoding cannot fail with an in-memory writer");
    out.into_inner()
}

fn summary_from_samples(
    ride: &Ride,
    secs_per_sample: i64,
    power_fudge: f64,
) -> (u16, u16, u8, u8, u8, u8, f64) {
    let mut power_sum = 0.0f64;
    let mut power_max = 0.0f64;
    let mut cad_sum = 0.0f64;
    let mut cad_max = 0.0f64;
    let mut hr_sum = 0.0f64;
    let mut hr_max = 0.0f64;
    let mut speed_max = 0.0f64;
    let mut prev_dist = 0.0f64;

    for (i, p) in ride.power.iter().enumerate() {
        let power = p.parse::<f64>().unwrap_or(0.0) * power_fudge;
        power_sum += power;
        power_max = power_max.max(power);

        let cad = ride.rpm[i].parse::<f64>().unwrap_or(0.0);
        cad_sum += cad;
        cad_max = cad_max.max(cad);

        let hr = ride.hr[i].parse::<f64>().unwrap_or(0.0);
        hr_sum += hr;
        hr_max = hr_max.max(hr);

        let dist = ride.distance[i].parse::<f64>().unwrap_or(0.0);
        if i > 0 {
            let speed = (dist - prev_dist).max(0.0) / secs_per_sample as f64;
            speed_max = speed_max.max(speed);
        }
        prev_dist = dist;
    }

    let n = ride.count() as f64;
    (
        if n > 0.0 { (power_sum / n).clamp(0.0, u16::MAX as f64) as u16 } else { 0 },
        power_max.clamp(0.0, u16::MAX as f64) as u16,
        if n > 0.0 { (cad_sum / n) as u8 } else { 0 },
        cad_max as u8,
        if n > 0.0 { (hr_sum / n) as u8 } else { 0 },
        hr_max as u8,
        speed_max,
    )
}

/// In-memory `Write + Seek` sink so core stays I/O-free (WASM-safe).
struct VecCursor {
    buf: Vec<u8>,
    pos: usize,
}

impl VecCursor {
    fn new() -> Self {
        Self { buf: Vec::new(), pos: 0 }
    }

    fn into_inner(self) -> Vec<u8> {
        self.buf
    }
}

impl ErrorType for VecCursor {
    type Error = core::convert::Infallible;
}

impl Write for VecCursor {
    fn write(&mut self, buf: &[u8]) -> Result<usize, Self::Error> {
        if self.pos + buf.len() > self.buf.len() {
            self.buf.resize(self.pos + buf.len(), 0);
        }
        self.buf[self.pos..self.pos + buf.len()].copy_from_slice(buf);
        self.pos += buf.len();
        Ok(buf.len())
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        Ok(())
    }
}

impl Seek for VecCursor {
    fn seek(&mut self, pos: SeekFrom) -> Result<u64, Self::Error> {
        let base = self.buf.len() as i64;
        let new = match pos {
            SeekFrom::Start(n) => n as i64,
            SeekFrom::End(n) => base + n,
            SeekFrom::Current(n) => self.pos as i64 + n,
        };
        if new < 0 {
            panic!("seek before start of buffer");
        }
        self.pos = new as usize;
        Ok(new as u64)
    }
}
