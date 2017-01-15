#
# MPowerTCX: Share Schwinn A.C. indoor cycle data with Strava, GoldenCheetah and other apps
# Copyright (C) 2016 James Roth
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

import csv
import sys
import datetime
import xml.etree.cElementTree as ET


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


class MPower(object):
    """ Process the CSV into TCX """
    def __init__(self, in_filename):
        self.in_filename = in_filename
        self.out_filename = None

        # The power meter on my favorite bike is at least 5% high.
        # In that case, this value could be set to 0.95.
        self.power_fudge = 1.0
        self.sport = "Biking"

        # Distance sometimes results in erratic speed values (84 mph)
        self.use_distance = True
        self.ride = Ride()

    def count(self):
        return self.ride.count()

    def header(self):
        return self.ride.header

    def set_include_speed_data(self, value):
        """ Allow estimated speed data to be excluded. They aren't really worth much. """
        self.use_distance = value

    def set_power_adjust(self, value):
        """ Power readings vary quite a bit from bike to bike. Allow adjustment """
        self.power_fudge = 1.0 + value / 100.0

    def _load_csv_chunk(self, reader):
        """ Guess what the next block of CSV data is an process it """
        line = reader.next()

        if line == []:
            pass
        elif line == ['Stages_Data', '', '', '', '', '']:
            self._load_stages(reader)
        elif line == ['RIDE SUMMARY', '']:
            self._load_v2_header(reader)
        elif line == ['RIDE DATA', '']:
            self._load_v2_data(reader)
        elif line == ['Stage_Totals']:
            self._load_v1_header(reader)
        elif line == ['Stage_Workout (min)', 'Distance(km)', 'Speed(km/h)', 'Watts ', 'HR ', 'RPM ']:
            self._load_v1_data(reader)
        elif line == ['Stage_Workout (min)', 'Distance(mile)', 'Speed (mph)', 'Watts ', 'HR ', 'RPM ']:
            # The Cordis file
            self._load_v3(reader)
        else:
           print ("skip start %r" % line)

           while True:
               line = reader.next()

               if line == []:
                   break

               print ("skip %r" % line)

    def load_csv(self):
        """ Read the CSV into a summary and time series """
        with open(self.in_filename, 'rU') as infile:
            reader = csv.reader(infile, skipinitialspace=True)

            try:
                while True:
                    self._load_csv_chunk(reader)
            except StopIteration:
                pass
                
    def _parse_stages_time(self, time):
        # I've seen mm:ss or mm:ss:00 so far 
        parts = time.split(':')
        
        if len(parts) == 2 or len(parts) == 3:
            try:
                minutes = int(parts[0])
                seconds = int(parts[1])
                result = minutes * 60 + seconds
            except:
                result = -1
        else:
            result = -1
            
        return result

    # TODO: unify this        
    def _stages_distance(self, d):
        if self._stages_metric:
            return d * 1000.0
        else:
            return d * 1609.34
            
    def _load_stages(self, reader):
        self._stages_metric = True
        distance = 0.0
        
        for row in reader:
            if row == ['English', '', '', '', '', '']:
                self._stages_metric = False
            elif row == ['Ride_Totals', '', '', '', '', '']:
                self._load_stages_header(reader)
            elif len(row) == 6:
                time = self._parse_stages_time(row[0])
                
                if time >= 0:
                    # ['Time', 'Miles', 'MPH', 'Watts', 'HR', 'RPM']
                    # TODO: maybe use this method on all file formats.
                    #       Infer distance from MPH.
                    distance += float(row[2]) / (60.0 * 60.0)
                    
                    self.ride.addSample(
                        power=row[3],
                        rpm=row[5],
                        hr=row[4],
                        distance=self._stages_distance(distance)
                    )
                    pass
                else:
                    print ("skip %r" % row)
            else:
                print ("skip %r" % row)
        
    def _load_stages_header(self, reader):
        header = {}
        
        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

        parts = header['Time'].split(':')
        h = 0
        m = 0 
        s = 0
        
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2])
        elif len(parts) == 2:
            m = int(parts[0])
            s = int(parts[1])
        elif len(parts) == 2:
            s = int(parts[0])
        
        time = h * 60 * 60 + m * 60 + s    
        
        self.ride.header.setSummary(
            time=time,
            distance=self._stages_distance(float(header["Distance"])),
            average_power=header["Watts_Avg"],
            max_power=header["Watts_Max"],
            average_rpm=header["RPM_Avg"],
            max_rpm=header["RPM_Max"],
            average_hr=header["HR_Avg"],
            max_hr=header["HR_Max"],
            calories=header["KCal"]
        )
        
    def _load_v2_header(self, reader):
        """ Read Echelon2 header data """
        header = {}

        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

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

    def _load_v2_data(self, reader):
        """ Read Echelon2 time series """
        keys = reader.next()

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

    def _load_v1_header(self, reader):
        """ Read Echelon 1 header data """
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

    def _load_v1_data(self, reader):
        """ Read Echelon 1 time series """
        for row in reader:
            if len(row):
                self.ride.addSample(
                    power=row[3],
                    rpm=row[5],
                    hr=row[4],
                    distance=float(row[1]) * 1000.0
                )
            else:
                break

    def _load_v3(self, reader):
        """ So called v3 is a messed up version of v1. I suspect it's an earlier firmware. """
        for row in reader:
            if len(row) == 6:
                self.ride.addSample(
                    power=row[3],
                    rpm=row[5],
                    hr=row[4],
                    distance=float(row[1]) * 1609.34
                )
            elif row == ['Stage_Totals']:
                self._load_v3_header(reader)
            else:
                print ("v3 drop %r" % row)
        
    def _load_v3_header(self, reader):
        """ Read Echelon 1 header data """
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

    def _format_time(self, dt):
        """ Return a time string in TCX format """
        return dt.isoformat() + "Z"

    def _save_xml_cruft(self, root):
        """ The header stuff for the TCX XML """
        root.set("xmlns:ns5", "http://www.garmin.com/xmlschemas/ActivityGoals/v1")
        root.set("xmlns:ns3", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")
        root.set("xmlns:ns2", "http://www.garmin.com/xmlschemas/UserProfile/v2")
        root.set("xmlns", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd")

    def save_data(self, filename, start_time):
        """ Save the parsed CSV to TCX """
        now = self._format_time(start_time)

        root = ET.Element("TrainingCenterDatabase")
        self._save_xml_cruft(root)

        doc = ET.SubElement(root, "Activities")
        activity = ET.SubElement(doc, "Activity", Sport=self.sport)
        ET.SubElement(activity, "Id").text = now

        lap = ET.SubElement(activity, "Lap", StartTime=now)
        seconds = self.ride.header.time
        ET.SubElement(lap, "TotalTimeSeconds").text = str(seconds)

        if self.use_distance:
            meters = float(self.ride.header.distance)
        else:
            meters = 0

        ET.SubElement(lap, "DistanceMeters").text = str(meters)
        ET.SubElement(lap, "MaximumSpeed").text = "0"
        ET.SubElement(lap, "Calories").text = "0"

        avg_hr = ET.SubElement(lap, "AverageHeartRateBpm")
        ET.SubElement(avg_hr, "Value").text = self.ride.header.average_hr

        max_hr = ET.SubElement(lap, "MaximumHeartRateBpm")
        ET.SubElement(max_hr, "Value").text = self.ride.header.max_hr

        ET.SubElement(lap, "Intensity").text = "Active"
        ET.SubElement(lap, "Cadence").text = "0"
        ET.SubElement(lap, "TriggerMethod").text = "Manual"

        # Infer the time between samples
        if self.ride.count():
            secs_per_sample = seconds / self.ride.count()
        else:
            secs_per_sample = 0
            
        print ("%d seconds per sample" % secs_per_sample)

        track = ET.SubElement(lap, "Track")

        for i in xrange(0, self.ride.count()):
            point = ET.SubElement(track, "Trackpoint")
            delta_time = start_time + datetime.timedelta(seconds=i * secs_per_sample)
            ET.SubElement(point, "Time").text = self._format_time(delta_time)

            hr = ET.SubElement(point, "HeartRateBpm")
            ET.SubElement(hr, "Value").text = self.ride.hr[i]
            hr = ET.SubElement(point, "Cadence").text = self.ride.rpm[i]

            if self.use_distance:
                distance = self.ride.distance[i]
            else:
                distance = 0

            hr = ET.SubElement(point, "DistanceMeters").text = str(distance)
            ext = ET.SubElement(point, "Extensions")
            tpx = ET.SubElement(ext, "TPX", xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2")
            power = float(self.ride.power[i]) * self.power_fudge
            ET.SubElement(tpx, "Watts").text = str(int(power))
            i += 1

        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

