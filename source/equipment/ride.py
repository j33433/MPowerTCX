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

import physics.physics as model


class RideHeader(object):
    """
    Summary statistics for a ride
    """

    def __init__(self):
        self.setSummary()
        self.equipment = ''
        self.start_datetime = None

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

    def set_date_hint(self, hint):
        self.start_datetime = hint


class Ride(object):
    """
    Hold the time series data for the ride and a header
    """

    def __init__(self):
        self.power = []
        self.rpm = []
        self.hr = []
        self.distance = []
        self.header = RideHeader()

    def set_date_hint(self, hint):
        self.header.set_date_hint(hint)

    def get_date_hint(self):
        return self.header.start_datetime

    def add_sample(self, power=0, rpm=0, hr=0, distance=0):
        self.power.append(str(power))
        self.rpm.append(str(rpm))
        self.hr.append(str(hr))
        self.distance.append(str(distance))

    def count(self):
        """
        The number of samples in the time series
        """
        return len(self.power)

    def infer_header(self, time=0):
        """
        Calculate missing header values
        """
        if len(self.power):
            average_power = sum(int(p) for p in self.power) / len(self.power)
            max_power = max(int(p) for p in self.power)
        else:
            average_power = 0
            max_power = 0

        self.header.setSummary(time=time, distance=0, average_power=average_power, max_power=max_power)

    def delta(self):
        """
        Return the average time between samples
        """
        if self.count():
            return self.header.time / self.count()
        else:
            return 0

    def interpolate(self):
        """
        Resample the data to one second intervals
        """
        import numpy as np

        seconds = self.header.time
        delta = self.delta()
        print("interpolate: %d seconds, %.2f seconds per sample before interpolation" % (seconds, delta))

        if delta == 0:
            print("nothing to interpolate")
            return

        limit = int(seconds)
        xa = np.arange(0, limit, delta)
        xb = np.arange(0, limit - delta, 1)

        if len(xa) != len(self.power):
            print('resizing for interpolation %r vs %r' % (len(xa), len(self.power)))
            xa.resize((len(self.power)))

        self.power = self._interpolate(xa, xb, self.power).astype("int").astype("str")
        self.rpm = self._interpolate(xa, xb, self.rpm).astype("int").astype("str")
        self.hr = self._interpolate(xa, xb, self.hr).astype("int").astype("str")
        self.distance = self._interpolate(xa, xb, self.distance).astype("str")

    def _interpolate(self, xa, xb, data):
        from scipy import interpolate

        f = interpolate.splrep(xa, data)
        return interpolate.splev(xb, f)

    def model_distance(self, mass):
        print('modeling distance with %r kg' % mass)
        delta = self.delta()
        bike = model.SimpleBike(mass)
        bike.set_time_delta(delta)
        self.distance = []
        distance = 0.0

        for p in self.power:
            power, v_mph, distance = bike.next_sample(float(p))
            self.distance.append(distance)

        self.header.distance = int(distance)
