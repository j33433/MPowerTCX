#!/usr/bin/env python

#
# Convert the examples
#

import os
import subprocess

testdir = '../samples'
files = os.listdir(testdir)

def tcx_name(filename, testdir, tag, ext):
    parts = filename.split('.')
    parts.insert(1, tag)
    parts[-1] = ext
    joined = ''.join(parts)
    full = os.path.join(testdir, joined)
    
    return full

for f in files:
    if f.lower().endswith('.csv'):
        csv_full = os.path.join(testdir, f)

        # An arbitrary, fixed time for testing.
        timestamp = '2010-10-19T20:56:35.450686'
        print ('run_samples.py: %r' % (csv_full))

        tcx_full = tcx_name(f, testdir, '', '.tcx')
        args = ['./mpowertcx.py', '--csv', csv_full, '--tcx', tcx_full, '--time', timestamp]
        print ('run_samples.py: %r' % args)
        subprocess.call(args)

        tcx_model = tcx_name(f, testdir, '_model', '.tcx')
        args = ['./mpowertcx.py', '--csv', csv_full, '--tcx', tcx_model, '--time', timestamp, '--model', '70']
        print ('run_samples.py: %r' % args)
        subprocess.call(args)

        tcx_interp = tcx_name(f, testdir, '_interp', '.tcx')
        args = ['./mpowertcx.py', '--csv', csv_full, '--tcx', tcx_interp, '--time', timestamp, '--interpolate']
        print ('run_samples.py: %r' % args)
        subprocess.call(args)
