#!/usr/bin/env python

import os
import sys
import subprocess

sizes = (16, 24, 32, 48, 64, 96, 128, 256)

svg = sys.argv[1]
basename, extension = os.path.splitext(svg)
ico = basename + '.ico'
tmp_names = []

for size in sizes:
    png = 'tmp/' + str(size) + '.png'
    tmp_names.append(png)
    subprocess.call(['inkscape', '-z', '-e', png, '-w', str(size), '-h', str(size), svg])

subprocess.call(['convert'] + tmp_names + [ico])

