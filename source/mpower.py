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

#
# This file contains the conversion engine
#

import re
import csv
import sys
import datetime
import lxml.etree as ET
import lxml.builder

from equipment.ride import Ride, RideHeader
import physics

# Equipment plugins
from equipment.stages import Stages 
from equipment.thesufferfest import TheSufferfest
from equipment.echelon import EchelonV1, EchelonV2, EchelonV3

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
    debug = False
    do_interpolate = False
    do_physics = False
    
    def __init__(self, in_filename):
        self.in_filename = in_filename
        self.out_filename = None

        # The power meter on my favorite bike is at least 5% high.
        # In that case, this value could be set to 0.95.
        self.power_fudge = 1.0
        self.sport = "Biking"
        self.ride = Ride()
        
        self.bikes = [
            Stages(self.ride), 
            TheSufferfest(self.ride),
            EchelonV1(self.ride),
            EchelonV2(self.ride),
            EchelonV3(self.ride)
        ]

    def skip(self, line):
        if self.debug:
            print(line)
            
    def count(self):
        return self.ride.count()

    def header(self):
        return self.ride.header

    def set_interpolation(self, use):
        self.do_interpolate = use
        
    def set_physics(self, use, mass_kg):
        self.do_physics = use
        self.physics_mass = mass_kg
        
    def set_power_adjust(self, value):
        """ 
        Power readings vary quite a bit from bike to bike. Allow adjustment 
        """
        self.power_fudge = 1.0 + value / 100.0

    def _load_from_plugins(self, line, reader):
        for b in self.bikes:
            if b.load(line, reader):
                self.ride.header.equipment = b.name()
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
           self.skip (line)

           while True:
               line = reader.next()

               if line == []:
                   break

               self.skip(line)

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

    def _make_root_tag(self):
        """ 
        The header stuff for the TCX XML 
        """
        
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        schemaLocation = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd'

        nsmap={
             'ns5': 'http://www.garmin.com/xmlschemas/ActivityGoals/v1',
             'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
             'ns2': 'http://www.garmin.com/xmlschemas/UserProfile/v2',
             'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
             None: 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
        }

        builder = lxml.builder.ElementMaker(nsmap=nsmap)
        tag = builder.TrainingCenterDatabase()
        tag.attrib["{" + xsi + "}schemaLocation"] = schemaLocation
        
        return tag

    def save_data(self, filename, start_time):
        """ 
        Save the parsed CSV to TCX 
        """
        if self.do_interpolate:
            self.ride.interpolate()
        
        if self.do_physics:
            self.ride.modelDistance(self.physics_mass)

        now = self._format_time(start_time)
        root = self._make_root_tag()

        doc = ET.SubElement(root, "Activities")
        activity = ET.SubElement(doc, "Activity", Sport=self.sport)
        ET.SubElement(activity, "Id").text = now

        lap = ET.SubElement(activity, "Lap", StartTime=now)
        seconds = self.ride.header.time
        ET.SubElement(lap, "TotalTimeSeconds").text = str(seconds)

        meters = float(self.ride.header.distance)
        ET.SubElement(lap, "DistanceMeters").text = str(meters)
        ET.SubElement(lap, "MaximumSpeed").text = "0"
        ET.SubElement(lap, "Calories").text = "0"

        avg_hr = ET.SubElement(lap, "AverageHeartRateBpm")
        ET.SubElement(avg_hr, "Value").text = str(self.ride.header.average_hr)

        max_hr = ET.SubElement(lap, "MaximumHeartRateBpm")
        ET.SubElement(max_hr, "Value").text = str(self.ride.header.max_hr)

        ET.SubElement(lap, "Intensity").text = "Active"
        ET.SubElement(lap, "Cadence").text = "0"
        ET.SubElement(lap, "TriggerMethod").text = "Manual"

        secs_per_sample = self.ride.delta()
        print ("%r %.2f seconds per sample" % (self.ride.header.equipment, secs_per_sample))

        track = ET.SubElement(lap, "Track")

        for i in xrange(0, self.ride.count()):
            point = ET.SubElement(track, "Trackpoint")
            delta_time = start_time + datetime.timedelta(seconds=i * int(secs_per_sample))
            ET.SubElement(point, "Time").text = self._format_time(delta_time)

            hr = ET.SubElement(point, "HeartRateBpm")
            ET.SubElement(hr, "Value").text = self.ride.hr[i]
            hr = ET.SubElement(point, "Cadence").text = self.ride.rpm[i]

            distance = self.ride.distance[i]
            hr = ET.SubElement(point, "DistanceMeters").text = str(distance)
            ext = ET.SubElement(point, "Extensions")
            tpx = ET.SubElement(ext, "TPX", xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2")
            power = float(self.ride.power[i]) * self.power_fudge
            ET.SubElement(tpx, "Watts").text = str(int(power))

        tree = ET.ElementTree(root)
        nice = ET.tostring(tree, xml_declaration=True, encoding='utf-8', pretty_print=True)
        
        with open(filename, "w") as f:
            f.write(nice)

