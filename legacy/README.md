# Legacy Python Version

This is the original MPowerTCX desktop app, written in Python with PySide2 (Qt).
It has been superseded by a Rust rewrite. The conversion engine, CLI, and
web frontend now live in the project root under `crates/` and `web/`.

These files are kept for reference. They are not maintained.

## What was here

- `source/` - Python conversion engine, PySide2 GUI, equipment parsers
- `images/` - Screenshots and icons for the desktop app
- `requirements.txt` - Python dependencies (Mako, numpy, scipy, PySide2)
- `INSTRUCTIONS.md` - Desktop app instructions

The original README follows below.

---

<img align="right" src="images/mpowertcx%20simpler.png"/>

## About MPowerTCX
This application converts CSV files produced by stationary bikes to TCX format. The results can imported into fitness tracking tools such as Strava, TrainingPeaks, Garmin Connect and Golden Cheetah.

## Downloads
Downloads are discontinued and have been replaced by the online version!

### [Try it here at https://upload.bike](https://upload.bike)

### Support
* [Click Here for Instructions](INSTRUCTIONS.md)
* Email upload.bike@gmail.com
* [Strava Club](https://www.strava.com/clubs/MPowerTCX)

<image src="images/mpowertcx%20console%20reflect.png" align="right"/>

### Works With
* MPower Echelon and Echelon 2 for Schwinn A.C. Cycles
* Stages Indoor Cycles
* The Sufferfest and Wahoo SYSTM CSV files
* Email Us Your Unsupported Files

### Supported Fields

Field  | Status
-----|----- 
Power | Supported
Cadence | Supported
Heart Rate | Supported
Speed | Supported
Laps | Coming Soon

<img src="images/mpowertcx%20advanced.png" align="right"/>

### Advanced Features
* An Optional Physics Model to Fix Missing or Poorly Estimated Speed
* Upsampling for Improved Compatibility
