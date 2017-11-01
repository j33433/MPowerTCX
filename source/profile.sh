#!/bin/bash

~/.local/bin/kernprof -l ./mpowertcx.py --csv ../samples/1122.csv --tcx tmp.tcx --interpolate
python -m line_profiler mpowertcx.py.lprof

