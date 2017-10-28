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
            EchelonV1(self.ride),
            EchelonV2(self.ride),
            EchelonV3(self.ride)
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
        else:
           print ("skip start %r" % line)

           while True:
               line = reader.next()

               if line == []:
                   break

               print ("skip %r" % line)

    def load_csv(self):
        """ 
        Read the CSV into a summary and time series 
        """
        with open(self.in_filename, 'rb') as infile:
            iterator = LineIterator(infile)
            reader = csv.reader(iterator, skipinitialspace=True)

            try:
                while True:
                    self._load_csv_chunk(reader)
            except StopIteration:
                pass

    def _format_time(self, dt):
        """ 
        Return a time string in TCX format 
        """
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    def _save_xml_cruft(self, root):
        """ 
        The header stuff for the TCX XML 
        """
        root.set("xmlns:ns5", "http://www.garmin.com/xmlschemas/ActivityGoals/v1")
        root.set("xmlns:ns3", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")
        root.set("xmlns:ns2", "http://www.garmin.com/xmlschemas/UserProfile/v2")
        root.set("xmlns", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd")

    @profile
    def prettify(self, elem):
        """
        The official pretty prenters for xml are slow beyond usefulness
        """
        ugly = ET.tostring(elem, 'utf-8')
        
        # something<foo -> something\n<foo
        tmp = re.sub('<([^\/])', '\n<\\1', ugly)
        
        # <anytag></anytag> -> <anytag>\n</antyag>
        tmp = re.sub('></', '>\n</', tmp)
        
        indent = 0
        spaces = '\t'
        out = '<?xml version="1.0" ?>\n'
        
        for line in tmp.split('\n'):
            if len(line):
                # <foo>x</foo>
                if line[1] != '/' and '</' in line:
                    out += (spaces * indent) + line + '\n'
                # </foo>
                elif line[1] == '/':
                    indent -= 1
                    out += (spaces * indent) + line + '\n'
                # <foo>...
                else:
                    out += (spaces * indent) + line + '\n'
                    indent += 1
        
        return out
        
    def save_data(self, filename, start_time, model=False):
        """ 
        Save the parsed CSV to TCX 
        """

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

