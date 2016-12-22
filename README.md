# MPowerTCX
Share Schwinn A.C. indoor cycle data with Strava, GoldenCheetah and other apps

![Schwinn MPower Console](docs/components.png)

## What it Does
This software converts the CSV data produced by MPower Echelon2 consoles to TCX format

The TCX file can then be uploaded to Strava, imported into GoldenCheetah or used with any number of other 
applications that support TCX

### Supported Fields
1. Power (watts)
1. Cadence
1. Heart Rate
1. Speed (as estimated by Schwinn)

## Getting the MPower CSV Data
1. Insert the USB thumb drive into the slot at the top of the MPower unit
1. Spin so hard you break the pedals off!
1. Stop pedalling
1. Press "AVG/MAX" for 5 seconds
1. The USB logo will flash a few times. Wait for the flashing to stop and remove the drive
1. The removable drive should now contain a file named MPower.csv

## Problems with USB Thumb Drives
This MPower Console appears to reject or even crash when a newer model USB drive is used. A 1GB drive is your best bet

If the USB logo fails to flash at the end of a ride, or the unit shuts off (crashes), you probably have an incompatible drive

## Problems with Files
I only have one model of indoor bike. It's possible that your bike produces a different file format

If you file doesn't work, feel free to send it my way

## Project Queue
1. Convert Echelon 1 file format
1. Document UI
1. Package executables for Widows and Mac
