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

from libc.math cimport sin, cos, atan, sqrt

cdef class SimpleBike(object):
    cdef double drag_coefficient
    cdef double frontal_area
    cdef double rho
    cdef double eta
    cdef double rolling_coefficient
    # kg
    cdef double mass
    cdef double grade
    cdef double g
    cdef double time_delta
    cdef double velocity
    cdef double distance 
    
    def __init__(self, double mass):
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
        
    def set_time_delta(self, double delta):
        self.time_delta = delta
        
    cdef drag(self, double velocity):
        return 0.5 * self.drag_coefficient * self.frontal_area * self.rho * velocity * velocity

    cdef rolling(self, double grade, double velocity):
        if velocity > 0.01:
            return self.g * cos(atan(grade)) * self.mass * self.rolling_coefficient
        else:
            return 0.0

    cdef gravity(self, double grade):
        return self.g * sin(atan(grade)) * self.mass

    def next_sample(self, double power):
        cdef double drag = self.drag(self.velocity)
        cdef double rolling = self.rolling(self.grade, self.velocity)
        cdef double gravity = self.gravity(self.grade)
        cdef double total_force = drag + rolling + gravity
        cdef double power_needed = total_force * (self.velocity / self.eta)
        cdef double net_power = power - power_needed
        cdef double r = self.velocity * self.velocity + 2.0 * net_power * self.time_delta * self.eta / self.mass
        
        if r > 0.0:
            self.velocity = sqrt(r)
        else:
            self.velocity = 0.0
            
#        print ("p %.2f, v %.2f, drag %.2f, rolling %.6f, gravity %.2f, total %.2f, r %.2f" % (power, self.velocity, drag, gravity, rolling, total_force, r))
        self.distance += self.velocity * self.time_delta

        # m/s to mph
        cdef double v_mph = self.velocity * 2.23694
        
        return power, v_mph, self.distance

