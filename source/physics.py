#!/usr/bin/env python

import math
import matplotlib.pyplot as plt

class SimpleBike(object):
    def __init__(self):
        self.drag_coefficient = 0.88
        self.frontal_area = 0.32
        self.rho = 1.2
        self.eta = 0.97  	
        self.rolling_coefficient = 5.0e-3
        # kg
        self.mass = 73
        self.grade = 0.0
        self.g = 9.81
        self.time_delta = 0.1
        self.x = 0
        self.velocity = 0.0
        self.distance = 0.0
        
    def drag(self, velocity):
        return 0.5 * self.drag_coefficient * self.frontal_area * self.rho * velocity * velocity

    def rolling(self, grade, velocity):
        if velocity > 0.01:
            return self.g * math.cos(math.atan(grade)) * self.mass * self.rolling_coefficient
        else:
            return 0.0

    def gravity(self, grade):
        return self.g * math.sin(math.atan(grade)) * self.mass

    def get_power(self, t):
        if t > 50:
            return 0
        elif t > 20: 
            return 60
        else:
            return 10

    def next_sample(self):
        t = self.x * self.time_delta
        total_force = self.drag(self.velocity) + self.rolling(self.grade, self.velocity) + self.gravity(self.grade)
        power_needed = total_force * self.velocity / self.eta
        power = self.get_power(t)
        net_power = power - power_needed
        self.velocity = math.sqrt(self.velocity * self.velocity + 2 * net_power * self.time_delta * self.eta / self.mass)
        self.distance += self.velocity * self.time_delta
        self.x += 1

        # m/s to mph
        v_mph = self.velocity * 2.23694
        
        return power, v_mph, self.distance

def main():
    velocity_a = [0]
    time_a = [0]
    power_a = [0]
    distance_a = [0]

    bike = SimpleBike()

    # loop over time:
    for x in range(0, 1000):
        (power, velocity, distance) = bike.next_sample()
        velocity_a.append(velocity)
        power_a.append(power)
        distance_a.append(distance)
        time_a.append(bike.time_delta * x)

    fig, velocity_axis = plt.subplots()
    velocity_axis.margins(0.05)
    velocity_axis.plot(time_a, velocity_a, color='b')
    velocity_axis.set_xlabel('time (s)')
    velocity_axis.set_ylabel('velocity (mph)', color='b')

    power_axis = velocity_axis.twinx()
    power_axis.margins(0.05)
    power_axis.plot(time_a, power_a, 'r')
    power_axis.set_ylabel('power (w)', color='r')

    distance_axis = velocity_axis.twinx()
    distance_axis.margins(0.05)
    distance_axis.plot(time_a, distance_a, 'g')
    distance_axis.set_ylabel('distance (m)', color='g')

    plt.show()

main()
