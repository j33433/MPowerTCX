#!/usr/bin/env python

#
# Convert the examples
#

import os
import subprocess

testdir = '../samples'
files = os.listdir(testdir)

for f in files:
    if f.lower().endswith('.csv'):
        parts = f.split('.')
        parts[-1] = '.tcx'
        tcx = ''.join(parts)
        csv_full = os.path.join(testdir, f)
        tcx_full = os.path.join(testdir, tcx)

        # An arbitrary, fixed time for testing.
        timestamp = '2010-10-19T20:56:35.450686'
        print ('run_samples.py: %r' % (csv_full))
        args = ['./mpowertcx.py', '--csv', csv_full, '--tcx', tcx_full, '--time', timestamp, '--model', '70']
        print ('run_samples.py: %r' % args)
        subprocess.call(args)
