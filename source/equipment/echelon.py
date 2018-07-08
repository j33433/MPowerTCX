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

import re

from . import bikes

#
# The version numbers represent the order in which I encountered them, not official firmware revisions
#
class EchelonV1(bikes.Bike):
    def load(self, peek, reader):
        if peek == ['Stage_Totals']:
            self._load_header(reader)
            return True
        elif peek == ['Stage_Workout (min)', 'Distance(km)', 'Speed(km/h)', 'Watts ', 'HR ', 'RPM ']:
            self._load_data(reader)
            return True
            
        return False

    def name(self):
        return "Echelon Variant 1"
        
    def _load_header(self, reader):
        header = {}

        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

        self.ride.header.setSummary(
            time=float(header["Total Time"]) * 60.0,
            distance=float(header["Total_distance:"]) * 1000.0,
            average_power=header["Watts Avg"],
            max_power=header["Watts Max"],
            average_rpm=header["RPM Avg"],
            max_rpm=header["RPM Max"],
            average_hr=header["HR Avg"],
            max_hr=header["HR Max"],
            calories=header["KCal"]
        )

    def _load_data(self, reader):
        last_time = 0
        
        for row in reader:
            if len(row) == 0:
                break
            elif len(row) == 6:
                last_time = float(row[0]) * 60
                self.ride.addSample(
                    power=row[3],
                    rpm=row[5],
                    hr=row[4],
                    distance=float(row[1]) * 1000.0
                )
            else:
                self.skip(row)

        if self.ride.header.time == 0:
            print ("v1 header missing")
            self.ride.inferHeader(last_time)
    
    
class EchelonV2(bikes.Bike):
    def load(self, peek, reader):
        if peek[0:2] == ['RIDE SUMMARY', '']:
            self._load_header(reader)
            return True
        elif peek[0:2] == ['RIDE DATA', '']:
            self._load_data(reader)
            return True
        elif re.match('^STAGE_[0-9]+_SUMMARY$', peek[0]):
            self._skip_section(reader)
            return True
            
        return False

    def name(self):
        return "Echelon Variant 2"
        
    def _skip_section(self, reader):
        for row in reader:
            # Return on "" or ",,,"
            if len(row) == 0 or ''.join(row) == '':
                break
    
    def _load_header(self, reader):
        header = {}

        for row in reader:
#            print ('ROW %r' % row)
            
            # Return on "" or ",,,"
            if len(row) and ''.join(row) != '':
                header[row[0]] = row[1]
            else:
                break

#        print ('HEADER %r' % header)
        
        self.ride.header.setSummary(
            time=float(header["Total Time"]) * 60.0,
            distance=float(header["Total Distance"]) * 1609.34,
            average_power=header["AVG Power"],
            max_power=header["MAX Power"],
            average_rpm=header["AVG RPM"],
            max_rpm=header["MAX RPM"],
            average_hr=header["AVG HR"],
            max_hr=header["MAX HR"],
            calories=header["CAL"]
        )

    def _load_data(self, reader):
        keys = next(reader)

        for row in reader:
            if len(row):
                data = dict(zip(keys, row))
                self.ride.addSample(
                    power=data["Power"],
                    rpm=data["RPM"],
                    hr=data["HR"],
                    distance=float(data["DISTANCE"]) * 1609.34
                )
            else:
                break

                
class EchelonV3(bikes.Bike):
    """ 
    So called v3 is a messed up version of v1. I suspect it's an earlier firmware. 
    """
    def load(self, peek, reader):
        if peek == ['Stage_Workout (min)', 'Distance(mile)', 'Speed (mph)', 'Watts ', 'HR ', 'RPM ']:
            self._load(reader)
            return True
            
        return False

    def name(self):
        return "Echelon Variant 3"
        
    def _load(self, reader):
        for row in reader:
            if len(row) == 6:
                self.ride.addSample(
                    power=row[3],
                    rpm=row[5],
                    hr=row[4],
                    distance=float(row[1]) * 1609.34
                )
            elif row == ['Stage_Totals']:
                self._load_header(reader)
            else:
                self.skip(row)
        
    def _load_header(self, reader):
        header = {}

        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

        self.ride.header.setSummary(
            time=float(header["Total Time"]) * 60.0,
            distance=float(header["Total_distance:"]) * 1609.34,
            average_power=header["Watts Avg"],
            max_power=header["Watts Max"],
            average_rpm=header["RPM Avg"],
            max_rpm=header["RPM Max"],
            average_hr=header["HR Avg"],
            max_hr=header["HR Max"],
            calories=header["KCal"]
        )
     