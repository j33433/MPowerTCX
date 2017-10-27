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

import numpy as np
from scipy import interpolate   

 
class RideHeader(object):
    """ Summary statistics for a ride """
    def __init__(self):
        self.setSummary()

    def setSummary(self, time=0, distance=0, average_power=0, max_power=0, average_rpm=0, max_rpm=0, average_hr=0, max_hr=0, calories=0):
        self.time = time
        self.distance = distance
        self.average_power = average_power
        self.max_power = max_power
        self.average_rpm = average_rpm
        self.max_rpm = max_rpm
        self.average_hr = average_hr
        self.max_hr = max_hr
        self.calories = calories


class Ride(object):
    """ Hold the time series data for the ride and a header """
    def __init__(self):
        self.power = []
        self.rpm = []
        self.hr = []
        self.distance = []
        self.header = RideHeader()

    def addSample(self, power=0, rpm=0, hr=0, distance=0):
        self.power.append(str(power))
        self.rpm.append(str(rpm))
        self.hr.append(str(hr))
        self.distance.append(str(distance))

    def count(self):
        """ The number of samples in the time series """
        return len(self.power)
        
    def inferHeader(self, time=0):
        average_power = sum(int(p) for p in self.power) / len(self.power)
        max_power = max(int(p) for p in self.power)
        print ("%d %d" % (average_power, max_power))
        self.header.setSummary(time=time, distance=0, average_power=average_power, max_power=max_power)

    def delta(self):
        if self.count():
            return self.header.time / self.count()
        else:
            return 0
        
    def interpolate(self):
        seconds = self.header.time
        delta = self.delta()
        print ("%.2f seconds per sample before interpolation" % (delta))
        
        if delta == 0:
            print ("nothing to interpolate")
            return
        
        limit = int(seconds)
        xa = np.arange(0, limit, delta)
        xb = np.arange(0, limit - delta, 1)
       
        f = interpolate.interp1d(xa, self.power)
        self.power = f(xb).astype("int").astype("str")
        
        f = interpolate.interp1d(xa, self.rpm)
        self.rpm = f(xb).astype("int").astype("str")
        
        f = interpolate.interp1d(xa, self.hr)
        self.hr = f(xb).astype("int").astype("str")
        
        f = interpolate.interp1d(xa, self.distance)
        self.distance = f(xb).astype("str")
        
    def modelDistance(self):
        delta = self.delta()
        print ("delta %.2f" % delta)
        bike = physics.SimpleBike()
        bike.time_delta = delta
        self.distance = []

        for p in self.power:
            power, v_mph, distance = bike.next_sample(float(p))
            self.distance.append(distance)
            #print (power, v_mph, distance)

