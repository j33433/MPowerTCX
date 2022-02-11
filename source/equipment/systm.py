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

import datetime

from . import bikes


class Systm(bikes.Bike):
    header = [
        'ticks',
        'videoTimestamp',
        'targetPower4dpType',
        'intervalId',
        'timeOfDayTimestamp',   # time_t + 3 digits
        'distanceMeters',
        'speedVirtualMps',
        'distanceVirtualMeters',
        'workoutPosition',
        'powerMatchOffset',
        'cadence',
        'speed',
        'heartRate',
        'power',
        'distanceSensorMeters',
        'trainerPower',
        'time',
        'targetPower',
        'targetHeartRateZone',
        'targetCadence',
        'targetRpe',
        'secondsSinceStart',
        'grade',
        'speedSensorMps',
        'leftPower',
        'rightPower'
    ]

    keys = dict(zip(header, list(range(len(header)))))

    def load(self, peek, reader):
        if peek == self.header:
            self._load(reader)
            return True

        return False

    def name(self):
        return "Wahoo SYSTM"

    def get(self, row, field):
        idx = self.keys[field]
        value = row[idx]

        if value == "NaN":
            value = "0"

        return float(value)

    def _load(self, reader):
        last_time = 0.0
        start_stamp = None

        for row in reader:
            if len(row):
                if start_stamp is None:
                    start_stamp = int(self.get(row, 'timeOfDayTimestamp') / 1000)

                last_time = self.get(row, 'videoTimestamp')

                self.ride.addSample(
                    power=int(self.get(row, 'trainerPower')),
                    rpm=self.get(row, 'cadence'),
                    hr=self.get(row, 'heartRate'),
                    distance=self.get(row, 'distanceVirtualMeters')
                )

        when = datetime.datetime.fromtimestamp(start_stamp)
        print("start %r" % when)
        self.ride.inferHeader(last_time)
