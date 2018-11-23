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

import mpower

#
# Base class for equipment
#


class Bike(object):
    metric = False
    ride = None

    def __init__(self, ride):
        self.ride = ride

    def load(self, reader):
        raise NotImplementedError(self.__class__.__name__)

    def name(self):
        return "---"

    def distance(self, d):
        if self.metric:
            return d * 1000.0
        else:
            return d * 1609.34

    def skip(self, s):
        if mpower.MPower.debug:
            print("skip %r" % s)
