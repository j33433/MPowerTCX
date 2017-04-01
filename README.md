# MPowerTCX
Share indoor cycle data with Strava, Golden Cheetah and other apps

![Schwinn MPower Console](docs/components.png)

## Downloads

Find the latest release for Windows and OS X here: https://github.com/j33433/MPowerTCX/releases

## What it Does
This software converts the CSV data produced by indoor cycling consoles to TCX format.

The TCX file can be uploaded to most cycling data viewers.

### Support

Contact j33433@gmail.com

### Supported Consoles
1. MPower Echelon and Echelon 2 for Schwinn A.C. Cycles
1. Stages Indoor Cycles

### Supported Fields
1. Power
1. Cadence
1. Heart Rate
1. Speed

### Tested With
1. Strava
1. Golden Cheetah
1. Garmin Connect

## Getting the CSV Data
1. Insert the USB thumb drive into the slot at the top of the console
1. Work out
1. Stop pedalling
1. Press "AVG/MAX" for 5 seconds
1. The USB logo will flash a few times. Wait for the flashing to stop and remove the drive
1. The removable drive should now contain a file named something like MPower1.csv

## Problems with USB Thumb Drives
Some consoles reject or even crash when a newer model USB drive is used. A 1GB drive is your best bet.

If the USB logo fails to flash at the end of a ride, or the unit shuts off (crashes), you probably have an incompatible drive.

## Problems with Files
I only have one model of indoor bike. It's possible that your bike produces a different file format.

If you file doesn't work, feel free to send it my way.

## Converting your workout file to TCX

### Step 1 - Click "Load CSV..." to select your workout file

![Step 1](docs/mp1.png)

### Step 2 - If the file loads correctly, you will see this

![Step 2](docs/mp2.png)

### Step 3 - Adjust and click "Save TCX..." 

In this example the power meter on the bike reads too high by about 4%. The power values are adjusted down by using a negative value. 

By default, the workout time will be set to the timestamp on the CSV file. If you want to set a custom time, uncheck "Use File Time as Workout Time" and adjust the time.

![Step 3](docs/mp3.png)

### Step 4 - Done. Now you have a TCX file.

![Step 4](docs/mp4.png)


