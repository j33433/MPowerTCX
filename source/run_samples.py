#!/usr/bin/env python

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

        print (csv_full, tcx_full)
        subprocess.call(['./mpowertcx.py', csv_full, tcx_full])