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
        let hr_f: Vec<f64> = self.hr.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect();
        let dist_f: Vec<f64> = self.distance.iter().map(|s| s.parse::<f64>().unwrap_or(0.0)).collect();

        let interp_power = spline_interp(&xa, &power_f, &xb);
        let interp_rpm = spline_interp(&xa, &rpm_f, &xb);
        let interp_hr = spline_interp(&xa, &hr_f, &xb);
        let interp_dist = spline_interp(&xa, &dist_f, &xb);

        self.power = interp_power.iter().map(|v| (*v as i64).to_string()).collect();
        self.rpm = interp_rpm.iter().map(|v| (*v as i64).to_string()).collect();
        self.hr = interp_hr.iter().map(|v| (*v as i64).to_string()).collect();
        self.distance = interp_dist.iter().map(|v| float_to_str(*v)).collect();
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

fn spline_interp(xa: &[f64], ya: &[f64], xb: &[f64]) -> Vec<f64> {
    let n = xa.len();
    if n < 2 || xb.is_empty() {
        return xb.iter().map(|&x| {
            if n == 1 { return ya[0]; }
            linear_extrap(xa, ya, x)
        }).collect();
    }
    if n == 2 {
        return xb.iter().map(|&x| {
            if x < xa[0] || x > xa[1] { linear_extrap(xa, ya, x) }
            else { let t = (x - xa[0]) / (xa[1] - xa[0]); ya[0] + t * (ya[1] - ya[0]) }
        }).collect();
    }

    let mut h = vec![0.0f64; n - 1];
    for i in 0..n - 1 {
        h[i] = xa[i + 1] - xa[i];
    }

    // Not-a-knot boundary conditions, solving for c[1..n-1] (size m = n-2)
    // c[0] is expressed from the left not-a-knot condition:
    //   -h[1]*c[0] + (h[0]+h[1])*c[1] - h[0]*c[2] = 0
    //   c[0] = ((h[0]+h[1])*c[1] - h[0]*c[2]) / h[1]
    // c[n-1] from the right not-a-knot:
    //   -h[n-2]*c[n-3] + (h[n-3]+h[n-2])*c[n-2] - h[n-3]*c[n-1] = 0
    //   c[n-1] = ((h[n-3]+h[n-2])*c[n-2] - h[n-2]*c[n-3]) / h[n-3]

    let m = n - 2; // number of interior unknowns: c[1]..c[n-2]

    // Build tridiagonal system for c[1]..c[n-2]
    let mut dl = vec![0.0f64; m]; // sub-diagonal
    let mut dd = vec![0.0f64; m]; // diagonal
    let mut du = vec![0.0f64; m]; // super-diagonal
    let mut rhs = vec![0.0f64; m];

    // Interior equations (rows 1..n-2 of the full system map to rows 0..m-1)
    // Row j in reduced system corresponds to c[j+1]
    for j in 0..m {
        let i = j + 1; // original index
        rhs[j] = 3.0 * ((ya[i + 1] - ya[i]) / h[i] - (ya[i] - ya[i - 1]) / h[i - 1]);
        if j > 0 {
            dl[j] = h[i - 1];
        }
        dd[j] = 2.0 * (h[i - 1] + h[i]);
        if j < m - 1 {
            du[j] = h[i];
        }
    }

    // Modify first row (j=0, i=1): substitute c[0] = alpha*c[1] + beta*c[2]
    // c[0] = ((h0+h1)*c[1] - h0*c[2]) / h1
    let h0 = h[0];
    let h1 = h[1];
    let alpha = (h0 + h1) / h1;
    let beta = -h0 / h1;
    // Row 1: h0*c[0] + 2*(h0+h1)*c[1] + h1*c[2] = rhs[1]
    // => h0*(alpha*c[1] + beta*c[2]) + 2*(h0+h1)*c[1] + h1*c[2] = rhs[1]
    // => (h0*alpha + 2*(h0+h1))*c[1] + (h0*beta + h1)*c[2] = rhs[1]
    dd[0] = h0 * alpha + 2.0 * (h0 + h1);
    du[0] = h0 * beta + h1;

    // Modify last row (j=m-1, i=n-2): substitute c[n-1] = gamma*c[n-2] + delta*c[n-3]
    let hnm2 = h[n - 2];
    let hnm3 = h[n - 3];
    let gamma = (hnm3 + hnm2) / hnm3;
    let delta = -hnm2 / hnm3;
    // Row n-2: h[n-3]*c[n-3] + 2*(h[n-3]+h[n-2])*c[n-2] + h[n-2]*c[n-1] = rhs[n-2]
    // => h[n-3]*c[n-3] + 2*(hnm3+hnm2)*c[n-2] + hnm2*(gamma*c[n-2] + delta*c[n-3]) = rhs[n-2]
    // => (hnm3 + hnm2*delta)*c[n-3] + (2*(hnm3+hnm2) + hnm2*gamma)*c[n-2] = rhs[n-2]
    dl[m - 1] = hnm3 + hnm2 * delta;
    dd[m - 1] = 2.0 * (hnm3 + hnm2) + hnm2 * gamma;

    // Solve tridiagonal system using Thomas algorithm
    let mut cp = vec![0.0f64; m];
    let mut dp = vec![0.0f64; m];

    cp[0] = du[0] / dd[0];
    dp[0] = rhs[0] / dd[0];

    for j in 1..m {
        let denom = dd[j] - dl[j] * cp[j - 1];
        cp[j] = if j < m - 1 { du[j] / denom } else { 0.0 };
        dp[j] = (rhs[j] - dl[j] * dp[j - 1]) / denom;
    }

    let mut c_int = vec![0.0f64; m];
    c_int[m - 1] = dp[m - 1];
    for j in (0..m - 1).rev() {
        c_int[j] = dp[j] - cp[j] * c_int[j + 1];
    }

    // Full c array: c[0]..c[n-1]
    let mut c = vec![0.0f64; n];
    for j in 0..m {
        c[j + 1] = c_int[j];
    }
    // c[0] from not-a-knot
    c[0] = alpha * c[1] + beta * c[2];
    // c[n-1] from not-a-knot
    c[n - 1] = gamma * c[n - 2] + delta * c[n - 3];

    // Compute b and d coefficients
    let mut b = vec![0.0f64; n];
    let mut d = vec![0.0f64; n];
    for i in 0..n - 1 {
        b[i] = (ya[i + 1] - ya[i]) / h[i] - h[i] * (c[i + 1] + 2.0 * c[i]) / 3.0;
        d[i] = (c[i + 1] - c[i]) / (3.0 * h[i]);
    }

    // Evaluate spline at query points
    let mut result = Vec::with_capacity(xb.len());
    for &x in xb {
        if x < xa[0] || x > xa[n - 1] {
            result.push(linear_extrap(xa, ya, x));
            continue;
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
        let dx = x - xa[lo];
        let val = ya[lo] + b[lo] * dx + c[lo] * dx * dx + d[lo] * dx * dx * dx;
        result.push(val);
    }
    result
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
