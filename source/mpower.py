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

import re
import csv
import sys
import datetime
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

from mpowertcx.ride import Ride, RideHeader
import mpowertcx.physics

# Equipment plugins
from mpowertcx.stages import Stages 
from mpowertcx.thesufferfest import TheSufferfest
from mpowertcx.echelon import EchelonV1, EchelonV2, EchelonV3

class LineIterator(object):
    """ 
    Handle files with standard and unusual newline conventions 
    """
    def __init__(self, stream):
        self._parts = re.split("\r\r\n|\r\n|\n|\r", stream.read())
        
    def __iter__(self):
        return self
        
    def next(self):
        if len(self._parts):
            n = self._parts.pop(0)
            return n
            
        raise StopIteration()

class MPower(object):
    """ 
    Process the CSV into TCX 
    """
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
        
        self.bikes = [
            Stages(self.ride), 
            TheSufferfest(self.ride),
            EchelonV1(self.ride)
        ]

    def count(self):
        return self.ride.count()

    def header(self):
        return self.ride.header

    def set_include_speed_data(self, value):
        """ 
        Allow estimated speed data to be excluded. They aren't really worth much
        """
        self.use_distance = value

    def set_power_adjust(self, value):
        """ 
        Power readings vary quite a bit from bike to bike. Allow adjustment 
        """
        self.power_fudge = 1.0 + value / 100.0

    def _load_from_plugins(self, line, reader):
        for b in self.bikes:
            if b.load(line, reader):
                return True
                
        return False
        
    def _load_csv_chunk(self, reader):
        """ 
        Guess what the next block of CSV data is an process it 
        """
        line = reader.next()
        
        if line == []:
            pass
        elif self._load_from_plugins(line, reader):
            pass
        elif line == ['RIDE SUMMARY', '']:
            self._load_v2_header(reader)
        elif line == ['RIDE DATA', '']:
            self._load_v2_data(reader)
        elif line == ['Stage_Workout (min)', 'Distance(mile)', 'Speed (mph)', 'Watts ', 'HR ', 'RPM ']:
            # The Cordis file
            self._load_v3(reader)
        elif line == ['ticks', 'time', 'power', 'cadence', 'heartRate', 'speed', 'targetPower', 'targetHeartRateZone', 'targetCadence', 'targetRpe']:
            self._load_sufferfest(reader)
        else:
           print ("skip start %r" % line)

           while True:
               line = reader.next()

               if line == []:
                   break

               print ("skip %r" % line)

    def load_csv(self):
        """ Read the CSV into a summary and time series """
        with open(self.in_filename, 'rb') as infile:
            iterator = LineIterator(infile)
            reader = csv.reader(iterator, skipinitialspace=True)

            try:
                while True:
                    self._load_csv_chunk(reader)
            except StopIteration:
                pass
        
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
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    def _save_xml_cruft(self, root):
        """ The header stuff for the TCX XML """
        root.set("xmlns:ns5", "http://www.garmin.com/xmlschemas/ActivityGoals/v1")
        root.set("xmlns:ns3", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")
        root.set("xmlns:ns2", "http://www.garmin.com/xmlschemas/UserProfile/v2")
        root.set("xmlns", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd")

    def prettify(self, elem):
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml()
        
    def save_data(self, filename, start_time, model=False):
        """ Save the parsed CSV to TCX """

        #self.ride.interpolate()
        
        #if model:
        #self.ride.modelDistance()

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

        secs_per_sample = self.ride.delta()
        print ("%.2f seconds per sample" % secs_per_sample)

        track = ET.SubElement(lap, "Track")

        for i in xrange(0, self.ride.count()):
            point = ET.SubElement(track, "Trackpoint")
            delta_time = start_time + datetime.timedelta(seconds=i * int(secs_per_sample))
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
        nice = self.prettify(root)
        
        with open(filename, "w") as f:
            f.write(nice)

