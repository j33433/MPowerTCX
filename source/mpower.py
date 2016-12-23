import csv
import sys
import datetime
import xml.etree.cElementTree as ET


class RideHeader(object):
    def __init__(self):
        pass

    def setSummary(self, time=0, distance=0, avg_power=0, max_power=0, avg_rpm=0, max_rpm=0, avg_hr=0, max_hr=0, calories=0):
        self.time = time
        self.distance = distance
        self.avg_power = avg_power
        self.max_power = max_power
        self.avg_rpm = avg_rpm
        self.max_rpm = max_rpm
        self.avg_hr = avg_hr
        self.max_hr = max_hr
        self.calories = calories


class Ride(object):
    def __init__(self):
        self.power = []
        self.rpm = []
        self.hr = []
        self.distance = []
        self.header = RideHeader()

    def addSample(self, power=0, rpm=0, hr=0, distance=0):
        self.power.append(str(power))
        self.rpm.append(str(rpm))
        self.hr.append(str(hr))
        self.distance.append(str(distance))

    def count(self):
        return len(self.power)


class MPower(object):
    def __init__(self, in_filename):
        self.in_filename = in_filename
        self.out_filename = None

        # The power meter on my favorite bike is at least 5% high.
        # In that case, this value could be set to 0.95.
        self.power_fudge = 1.0

        # Look in to how Strava uses this
        self.sport = "Virtual Ride"

        # Distance sometimes results in erratic speed values (84 mph)
        self.use_distance = True

        self.ride = Ride()

    def set_include_speed_data(self, value):
        self.use_distance = value

    def set_power_adjust(self, value):
        self.power_fudge = 1.0 + value / 100.0

    def load_csv(self):
        with open(self.in_filename, 'r') as infile:
            reader = csv.reader(infile, skipinitialspace=True)

            try:
                while True:
                    line = reader.next()

                    if line == []:
                        pass
                    elif line == ['RIDE SUMMARY', '']:
                        self.load_v2_header(reader)
                    elif line == ['RIDE DATA', '']:
                        self.load_v2_data(reader)
                    else:
                       print ("skip %r" % line)

                       while True:
                           line = reader.next()

                           if line == []:
                               break

                           print ("skip %r" % line)
            except StopIteration:
                print ("done reading")

    def load_v2_header(self, reader):
        header = {}

        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

        self.ride.header.setSummary(
            time=float(header["Total Time"]) * 60.0,
            distance=float(header["Total Distance"]) * 1609.34,
            avg_power=header["AVG Power"],
            max_power=header["MAX Power"],
            avg_rpm=header["AVG RPM"],
            max_rpm=header["MAX RPM"],
            avg_hr=header["AVG HR"],
            max_hr=header["MAX HR"],
            calories=header["CAL"]
        )

    def load_v2_data(self, reader):
        keys = reader.next()

        for row in reader:
            if len(row):
                data = dict(zip(keys, row))
                self.ride.addSample(
                    power=data["Power"],
                    rpm=data["RPM"],
                    hr=data["HR"],
                    distance=float(data["DISTANCE"]) * 1609.34
                )
            else:
                break

    def format_time(self, dt):
        return dt.isoformat() + "Z"

    def save_xml_cruft(self, root):
        root.set("xmlns:ns5", "http://www.garmin.com/xmlschemas/ActivityGoals/v1")
        root.set("xmlns:ns3", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")
        root.set("xmlns:ns2", "http://www.garmin.com/xmlschemas/UserProfile/v2")
        root.set("xmlns", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd")

    def save_data(self, filename, start_time):
        print ("use distance %r, power fudge %r" % (self.use_distance, self.power_fudge))
        now = self.format_time(start_time)

        root = ET.Element("TrainingCenterDatabase")
        self.save_xml_cruft(root)

        doc = ET.SubElement(root, "Activities")
        activity = ET.SubElement(doc, "Activity", Sport=self.sport)
        ET.SubElement(activity, "Id").text = now

        lap = ET.SubElement(activity, "Lap", StartTime=now)
        seconds = self.ride.header.time
        ET.SubElement(lap, "TotalTimeSeconds").text = str(seconds)

        if self.use_distance:
            meters = float(self.ride.header.distance)
        else:
            meters = 0

        ET.SubElement(lap, "DistanceMeters").text = str(meters)
        ET.SubElement(lap, "MaximumSpeed").text = "0"
        ET.SubElement(lap, "Calories").text = "0"

        avg_hr = ET.SubElement(lap, "AverageHeartRateBpm")
        ET.SubElement(avg_hr, "Value").text = self.ride.header.avg_hr

        max_hr = ET.SubElement(lap, "MaximumHeartRateBpm")
        ET.SubElement(max_hr, "Value").text = self.ride.header.max_hr

        ET.SubElement(lap, "Intensity").text = "Active"
        ET.SubElement(lap, "Cadence").text = "0"
        ET.SubElement(lap, "TriggerMethod").text = "Manual"

        secs_per_sample = seconds / self.ride.count()
        track = ET.SubElement(lap, "Track")

        for i in xrange(0, self.ride.count()):
            point = ET.SubElement(track, "Trackpoint")
            delta_time = start_time + datetime.timedelta(seconds=i * secs_per_sample)
            ET.SubElement(point, "Time").text = self.format_time(delta_time)

            hr = ET.SubElement(point, "HeartRateBpm")
            ET.SubElement(hr, "Value").text = self.ride.hr[i]
            hr = ET.SubElement(point, "Cadence").text = self.ride.rpm[i]

            if self.use_distance:
                distance = self.ride.distance[i]
            else:
                distance = 0

            hr = ET.SubElement(point, "DistanceMeters").text = str(distance)
            ext = ET.SubElement(point, "Extensions")
            tpx = ET.SubElement(ext, "TPX", xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2")
            ET.SubElement(tpx, "Speed").text = "0"
            power = float(self.ride.power[i]) * self.power_fudge
            ET.SubElement(tpx, "Watts").text = str(power)
            i += 1

        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
