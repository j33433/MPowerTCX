#!/usr/bin/env python
import argparse
import os
import sys
from datetime import datetime

import dateutil.parser
from mpower import MPower

if __name__ == '__main__':
    if len(sys.argv) == 1:
        from mpowertcxui import runui
        runui()
    else:
        # Run from the command line
        parser = argparse.ArgumentParser(description='Share indoor cycle data with Strava, Golden Cheetah and other apps')
        parser.add_argument('--csv', help='the spin bike file', required=True)
        parser.add_argument('--tcx', help='the output file', required=True)
        parser.add_argument('--time', help='the workout starting time')
        parser.add_argument('--interpolate', help='produce samples at one second intervals', action='store_true')
        parser.add_argument('--model', help='use physics model for speed and distance', metavar='MASS_KG')
        args = parser.parse_args()
        mpower = MPower(args.csv)
        mpower.load_csv()

        date_hint = mpower.get_date_hint()
        
        if args.time is not None:
            stamp = dateutil.parser.parse(args.time)
        elif date_hint is not None:
            stamp = date_hint
        else:
            # Take input file time
            stamp = datetime.fromtimestamp(os.path.getmtime(args.csv))

        if args.model is not None:
            mpower.set_physics(True, float(args.model))

        mpower.set_interpolation(args.interpolate)
        mpower.save_data(args.tcx, stamp)
