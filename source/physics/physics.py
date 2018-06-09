#!/usr/bin/env python

#
# MPowerTCX: Share Schwinn A.C. indoor cycle data with Strava, GoldenCheetah and other apps
# Copyright (C) 2017 James Roth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# This file contains a model to estimate bike speed based on power
#

import math

class SimpleBike(object):
    def __init__(self, mass):
        self.drag_coefficient = 0.88
        self.frontal_area = 0.32
        self.rho = 1.2
        self.eta = 0.97  	
        self.rolling_coefficient = 5.0e-3
        # kg
        self.mass = mass
        self.grade = 0.0
        self.g = 9.81
        self.time_delta = 1
        self.velocity = 0.0
        self.distance = 0.0

    def set_time_delta(self, delta):
        self.time_delta = delta
         
    def drag(self, velocity):
        return 0.5 * self.drag_coefficient * self.frontal_area * self.rho * velocity * velocity

    def rolling(self, grade, velocity):
        if velocity > 0.01:
            return self.g * math.cos(math.atan(grade)) * self.mass * self.rolling_coefficient
        else:
            return 0.0

    def gravity(self, grade):
        return self.g * math.sin(math.atan(grade)) * self.mass

    def next_sample(self, power):
        drag = self.drag(self.velocity)
        rolling = self.rolling(self.grade, self.velocity)
        gravity = self.gravity(self.grade)
        total_force = drag + rolling + gravity
        power_needed = total_force * (self.velocity / self.eta)
        net_power = power - power_needed
        r = self.velocity * self.velocity + 2 * net_power * self.time_delta * self.eta / self.mass
        
        if r > 0.0:
            self.velocity = math.sqrt(r)
        else:
            self.velocity = 0.0
            
#        print ("p %.2f, v %.2f, drag %.2f, rolling %.6f, gravity %.2f, total %.2f, r %.2f" % (power, self.velocity, drag, gravity, rolling, total_force, r))
        self.distance += self.velocity * self.time_delta

        # m/s to mph
        v_mph = self.velocity * 2.23694
        
        return power, v_mph, self.distance

def main():
    #import matplotlib.pyplot as plt
    
    velocity_a = [0]
    time_a = [0]
    power_a = [0]
    distance_a = [0]

    bike = SimpleBike()

    # loop over time:
    for x in range(0, 150):
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

#main()
