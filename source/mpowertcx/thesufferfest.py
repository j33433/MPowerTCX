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

import bikes

class TheSufferfest(bikes.Bike):
    def load(self, peek, reader):
        if peek == ['ticks', 'time', 'power', 'cadence', 'heartRate', 'speed', 'targetPower', 'targetHeartRateZone', 'targetCadence', 'targetRpe']:
            self._load(reader)
            return True
            
        return False
        
    def _load(self, reader):
        last_time = 0.0
        
        for row in reader:
            if len(row):
                time = float(row[1])
                last_time = time
                
                self.ride.addSample(
                    power=row[2],
                    rpm=row[3],
                    hr=row[4]
                )
                
        self.ride.inferHeader(last_time)
    
    