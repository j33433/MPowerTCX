pub struct SimpleBike {
    drag_coefficient: f64,
    frontal_area: f64,
    rho: f64,
    eta: f64,
    rolling_coefficient: f64,
    mass: f64,
    grade: f64,
    g: f64,
    time_delta: f64,
    velocity: f64,
    distance: f64,
}

impl SimpleBike {
    pub fn new(mass: f64) -> Self {
        Self {
            drag_coefficient: 0.88,
            frontal_area: 0.32,
            rho: 1.2,
            eta: 0.97,
            rolling_coefficient: 5.0e-3,
            mass,
            grade: 0.0,
            g: 9.81,
            time_delta: 1.0,
            velocity: 0.0,
            distance: 0.0,
        }
    }

    pub fn set_time_delta(&mut self, delta: f64) {
        self.time_delta = delta;
    }

    fn drag(&self, velocity: f64) -> f64 {
        0.5 * self.drag_coefficient * self.frontal_area * self.rho * velocity * velocity
    }

    fn rolling(&self, grade: f64, velocity: f64) -> f64 {
        if velocity > 0.01 {
            self.g * grade.atan().cos() * self.mass * self.rolling_coefficient
        } else {
            0.0
        }
    }

    fn gravity(&self, grade: f64) -> f64 {
        self.g * grade.atan().sin() * self.mass
    }

    pub fn next_sample(&mut self, power: f64) -> (f64, f64, f64) {
        let drag = self.drag(self.velocity);
        let rolling = self.rolling(self.grade, self.velocity);
        let gravity = self.gravity(self.grade);
        let total_force = drag + rolling + gravity;
        let power_needed = total_force * (self.velocity / self.eta);
        let net_power = power - power_needed;
        let r = self.velocity * self.velocity + 2.0 * net_power * self.time_delta * self.eta / self.mass;

        if r > 0.0 {
            self.velocity = r.sqrt();
        } else {
            self.velocity = 0.0;
        }

        self.distance += self.velocity * self.time_delta;
        let v_mph = self.velocity * 2.23694;

        (power, v_mph, self.distance)
    }

    pub fn total_distance(&self) -> f64 {
        self.distance
    }
}
