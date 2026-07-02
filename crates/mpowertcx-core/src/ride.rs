use chrono::NaiveDateTime;

pub struct RideHeader {
    pub time: f64,
    pub time_str: String,
    pub distance: f64,
    pub average_power: String,
    pub max_power: String,
    pub average_rpm: String,
    pub max_rpm: String,
    pub average_hr: String,
    pub max_hr: String,
    pub calories: String,
    pub equipment: String,
    pub start_datetime: Option<NaiveDateTime>,
}

impl Default for RideHeader {
    fn default() -> Self {
        Self::new()
    }
}

impl RideHeader {
    pub fn new() -> Self {
        Self {
            time: 0.0,
            time_str: "0".to_string(),
            distance: 0.0,
            average_power: "0".to_string(),
            max_power: "0".to_string(),
            average_rpm: "0".to_string(),
            max_rpm: "0".to_string(),
            average_hr: "0".to_string(),
            max_hr: "0".to_string(),
            calories: "0".to_string(),
            equipment: String::new(),
            start_datetime: None,
        }
    }

    pub fn set_summary(
        &mut self,
        time: f64,
        time_str: impl ToString,
        distance: f64,
        average_power: impl ToString,
        max_power: impl ToString,
        average_rpm: impl ToString,
        max_rpm: impl ToString,
        average_hr: impl ToString,
        max_hr: impl ToString,
        calories: impl ToString,
    ) {
        self.time = time;
        self.time_str = time_str.to_string();
        self.distance = distance;
        self.average_power = average_power.to_string();
        self.max_power = max_power.to_string();
        self.average_rpm = average_rpm.to_string();
        self.max_rpm = max_rpm.to_string();
        self.average_hr = average_hr.to_string();
        self.max_hr = max_hr.to_string();
        self.calories = calories.to_string();
    }

    pub fn set_date_hint(&mut self, hint: NaiveDateTime) {
        self.start_datetime = Some(hint);
    }
}

pub struct Ride {
    pub power: Vec<String>,
    pub rpm: Vec<String>,
    pub hr: Vec<String>,
    pub distance: Vec<String>,
    pub header: RideHeader,
}

impl Default for Ride {
    fn default() -> Self {
        Self::new()
    }
}

impl Ride {
    pub fn new() -> Self {
        Self {
            power: Vec::new(),
            rpm: Vec::new(),
            hr: Vec::new(),
            distance: Vec::new(),
            header: RideHeader::new(),
        }
    }

    pub fn add_sample(&mut self, power: impl ToString, rpm: impl ToString, hr: impl ToString, distance: impl ToString) {
        self.power.push(power.to_string());
        self.rpm.push(rpm.to_string());
        self.hr.push(hr.to_string());
        self.distance.push(distance.to_string());
    }

    pub fn count(&self) -> usize {
        self.power.len()
    }

    pub fn infer_header(&mut self, time: f64, time_str: impl ToString) {
        if !self.power.is_empty() {
            let sum: f64 = self.power.iter().map(|p| p.parse::<f64>().unwrap_or(0.0)).sum();
            let avg = sum / self.power.len() as f64;
            let max = self
                .power
                .iter()
                .map(|p| p.parse::<f64>().unwrap_or(0.0))
                .fold(0.0f64, f64::max);
            self.header.set_summary(
                time,
                time_str,
                0.0,
                avg.to_string(),
                max.to_string(),
                "0",
                "0",
                "0",
                "0",
                "0",
            );
        } else {
            self.header.time = time;
            self.header.time_str = time_str.to_string();
        }
    }

    pub fn delta(&self) -> f64 {
        if self.count() > 0 {
            self.header.time / self.count() as f64
        } else {
            0.0
        }
    }

    pub fn set_date_hint(&mut self, hint: NaiveDateTime) {
        self.header.set_date_hint(hint);
    }

    pub fn get_date_hint(&self) -> Option<NaiveDateTime> {
        self.header.start_datetime
    }

    pub fn interpolate(&mut self) {
        let seconds = self.header.time;
        let delta = self.delta();

        if delta == 0.0 {
            return;
        }

        let limit = seconds as i64;
        let delta_f = delta;

        let xa: Vec<f64> = {
            let mut v = Vec::new();
            let mut x = 0.0f64;
            while x < limit as f64 {
                v.push(x);
                x += delta_f;
            }
            if v.len() != self.power.len() {
                while v.len() < self.power.len() {
                    v.push(x);
                    x += delta_f;
                }
                v.truncate(self.power.len());
            }
            v
        };

        let xb: Vec<f64> = {
            let mut v = Vec::new();
            let mut x = 0.0f64;
            while x < (limit as f64 - delta_f) {
                v.push(x);
                x += 1.0;
            }
            v
        };

        let power_f: Vec<f64> = self.power.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect();
        let rpm_f: Vec<f64> = self.rpm.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect();
        let mut hr_f: Vec<f64> = self.hr.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect();
        let dist_f: Vec<f64> = self.distance.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect();

        forward_fill(&mut hr_f);

        let interp_power = linear_interp(&xa, &power_f, &xb);
        let interp_rpm = linear_interp(&xa, &rpm_f, &xb);
        let interp_hr = linear_interp(&xa, &hr_f, &xb);
        let mut interp_dist = linear_interp(&xa, &dist_f, &xb);

        enforce_monotonic(&mut interp_dist);

        self.power = interp_power.iter().map(|&v| (v.max(0.0) as i64).to_string()).collect();
        self.rpm = interp_rpm.iter().map(|&v| (v.max(0.0) as i64).to_string()).collect();
        self.hr = interp_hr.iter().map(|&v| (v as i64).to_string()).collect();
        self.distance = interp_dist.iter().map(|&v| float_to_str(v)).collect();
    }

    pub fn model_distance(&mut self, mass: f64) {
        let delta = self.delta();
        let mut bike = crate::physics::SimpleBike::new(mass);
        bike.set_time_delta(delta);

        self.distance.clear();
        for p in &self.power {
            let (_power, _v_mph, distance) = bike.next_sample(p.parse::<f64>().unwrap_or(0.0));
            self.distance.push(float_to_str(distance));
        }

        self.header.distance = bike.total_distance() as i64 as f64;
    }
}

fn float_to_str(v: f64) -> String {
    python_float(v)
}

pub fn python_float(v: f64) -> String {
    if v == v.trunc() && v.is_finite() {
        format!("{:.1}", v)
    } else {
        format!("{}", v)
    }
}

fn linear_interp(xa: &[f64], ya: &[f64], xb: &[f64]) -> Vec<f64> {
    let n = xa.len();
    if n == 0 || xb.is_empty() {
        return Vec::new();
    }
    if n == 1 {
        return xb.iter().map(|_| ya[0]).collect();
    }

    xb.iter()
        .map(|&x| {
            if x < xa[0] || x > xa[n - 1] {
                return linear_extrap(xa, ya, x);
            }

            let mut lo = 0usize;
            let mut hi = n - 1;
            while hi - lo > 1 {
                let mid = (lo + hi) / 2;
                if xa[mid] <= x {
                    lo = mid;
                } else {
                    hi = mid;
                }
            }
            let t = (x - xa[lo]) / (xa[lo + 1] - xa[lo]);
            ya[lo] + t * (ya[lo + 1] - ya[lo])
        })
        .collect()
}

fn forward_fill(vals: &mut [f64]) {
    let mut last = 0.0;
    for v in vals.iter_mut() {
        if *v == 0.0 {
            *v = last;
        } else {
            last = *v;
        }
    }
}

fn enforce_monotonic(vals: &mut [f64]) {
    let mut max_val = f64::NEG_INFINITY;
    for v in vals.iter_mut() {
        if *v < max_val {
            *v = max_val;
        } else {
            max_val = *v;
        }
    }
}

fn linear_extrap(xa: &[f64], ya: &[f64], x: f64) -> f64 {
    let n = xa.len();
    if n < 2 {
        return ya[0];
    }
    if x < xa[0] {
        let t = (x - xa[0]) / (xa[1] - xa[0]);
        ya[0] + t * (ya[1] - ya[0])
    } else {
        let t = (x - xa[n - 2]) / (xa[n - 1] - xa[n - 2]);
        ya[n - 2] + t * (ya[n - 1] - ya[n - 2])
    }
}
