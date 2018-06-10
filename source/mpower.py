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
import xml_templates
import mako.template 
import mako.runtime

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
        self._parts = re.split("\r\r\n|\r\n|\n|\r", stream.read().replace('\0', ''))
        
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

    def save_data(self, filename, start_time):
        """ 
        Save the parsed CSV to TCX 
        """
        if self.do_interpolate:
            self.ride.interpolate()
        
        if self.do_physics:
            self.ride.modelDistance(self.physics_mass)

#        template = mako.template.Template(xml_templates.training_center_database, default_filters=['unicode', 'x'])
        template = mako.template.Template(xml_templates.training_center_database, default_filters=[])
        now = self._format_time(start_time)
        
        header = dict(
            id=now, 
            start_time=now, 
            total_time=str(self.ride.header.time),
            distance_meters=str(float(self.ride.header.distance)),
            average_heart_rate=str(self.ride.header.average_hr),
            maximum_heart_rate=str(self.ride.header.max_hr), 
            sport=self.sport
        )
        
        secs_per_sample = self.ride.delta()
        points = []
        
        for i in xrange(0, self.ride.count()):
            delta_time = start_time + datetime.timedelta(seconds=i * int(secs_per_sample))
            power = float(self.ride.power[i]) * self.power_fudge
            
            point = dict(
                time=self._format_time(delta_time), 
                bpm=self.ride.hr[i], 
                cadence=self.ride.rpm[i], 
                distance_meters=str(self.ride.distance[i]),
                watts=str(int(power))
            )
            
            points.append(point)
      
        with open(filename, 'w') as out:
            context = mako.runtime.Context(out, points=points, header=header)
            template.render_context(context)

