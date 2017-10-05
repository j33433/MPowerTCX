#!/usr/bin/env python

import math
import matplotlib.pyplot as plt

class SimpleBike(object):
    def __init__(self):
        self.drag_coeff = 0.88
        self.frontal_area = 0.32
        self.rho = 1.2
        self.eta = 0.97  	
        self.rolling_coeff = 5.0e-3   
        # kg
        self.mass = 73
        self.grade = 0.0
        self.g = 9.81
        self.dt = 0.1
        self.x = 0
        self.v = 0.0
        
    def drag(self, velocity):
        return 0.5 * self.drag_coeff * self.frontal_area * self.rho * velocity * velocity

    def rolling(self, grade, velocity):
        if velocity > 0.01:
            return self.g * math.cos(math.atan(grade)) * self.mass * self.rolling_coeff
        else:
            return 0.0

    def gravity(self, grade):
        return self.g * math.sin(math.atan(grade)) * self.mass

    def get_power(self, t):
        if t > 20:
            return 220
        elif t > 10: 
            return 60
        else:
            return 500

    def next_velocity(self):
        t = self.x * self.dt
        total_force = self.drag(self.v) + self.rolling(self.grade, self.v) + self.gravity(self.grade)
        power_needed = total_force * self.v / self.eta
        power = self.get_power(t)
        net_power = power - power_needed
        # m/s to mph
        v_mph = self.v * 2.23694
        self.v = math.sqrt(self.v * self.v + 2 * net_power * self.dt * self.eta / self.mass)
        self.x += 1
        
        return (power, v_mph)
         
va = [0] 
ta = [0]
pa = [0]
bike = SimpleBike()

# loop over time:
for x in range(0, 600):
    (p, v) = bike.next_velocity()
    va.append(v)
    pa.append(p)
    ta.append(bike.dt * x)

fig, vaxis = plt.subplots()
vaxis.margins(0.05)
vaxis.plot(ta, va)
vaxis.set_xlabel('time (s)')
vaxis.set_ylabel('velocity (mph)')

paxis = vaxis.twinx()
paxis.margins(0.05)
paxis.plot(ta, pa, 'r')
paxis.set_ylabel('power (w)', color='r')
plt.show()

