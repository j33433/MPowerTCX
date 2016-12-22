import csv
import sys
import datetime
import xml.etree.cElementTree as ET

class MPower(object):
    def __init__(self, in_filename, out_filename):
        self.in_filename = in_filename
        self.out_filename = out_filename

        # The power meter on my favorite bike is at least 5% high.
        # In that case, this value could be set to 0.95.
        self.power_fudge = 1.0

        # Look in to how Strava uses this
        self.sport = "Virtual Ride"

        # Distance sometimes results in erratic speed values (84 mph)
        self.use_distance = True

    def process(self):
        self.load_csv()
        self.save_data()

    def load_csv(self):
        with open(self.in_filename, 'r') as infile:
            reader = csv.reader(infile, skipinitialspace=True)
            blank = reader.next()
            header = self.load_header(reader)
            data = self.load_data(reader)
            self.ride = {'header': header, 'data': data}

    def load_header(self, reader):
        header = {}
        title = reader.next()
        assert(title[0] == 'RIDE SUMMARY')

        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

        return header

    def load_data(self, reader):
        data = []
        title = reader.next()
        assert(title[0] == 'RIDE DATA')
        keys = reader.next()

        for row in reader:
            if len(row):
                data.append(dict(zip(keys, row)))
            else:
                break

        return data

    def format_time(self, dt):
        return dt.isoformat() + "Z"

    # This low-pass doesn't seem to help much
    def filter_distances(self, dist):
        y = 0.0
        a = 0.25
        ap = 1.0 - a
        filtered = []

        for d in dist:
            y = d * a + y * ap
            filtered.append(y)

        return filtered

    def save_data(self):
        # Using now as the start time and actvity id, since there is no reliable time stamp
        start_time = datetime.datetime.utcnow()
        now = self.format_time(start_time)
        header = self.ride['header']
        data = self.ride['data']

        root = ET.Element("TrainingCenterDatabase")
        root.set("xmlns:ns5", "http://www.garmin.com/xmlschemas/ActivityGoals/v1")
        root.set("xmlns:ns3", "http://www.garmin.com/xmlschemas/ActivityExtension/v2")
        root.set("xmlns:ns2", "http://www.garmin.com/xmlschemas/UserProfile/v2")
        root.set("xmlns", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd")

        doc = ET.SubElement(root, "Activities")
        activity = ET.SubElement(doc, "Activity", Sport=self.sport)
        ET.SubElement(activity, "Id").text = now

        lap = ET.SubElement(activity, "Lap", StartTime=now)
        seconds = float(header['Total Time']) * 60
        ET.SubElement(lap, "TotalTimeSeconds").text = str(seconds)

        if self.use_distance:
            meters = float(header['Total Distance']) * 1609.34
        else:
            meters = 0

        ET.SubElement(lap, "DistanceMeters").text = str(meters)
        ET.SubElement(lap, "MaximumSpeed").text = "0"
        ET.SubElement(lap, "Calories").text = "0"

        avg_hr = ET.SubElement(lap, "AverageHeartRateBpm")
        ET.SubElement(avg_hr, "Value").text = header['AVG HR']

        max_hr = ET.SubElement(lap, "MaximumHeartRateBpm")
        ET.SubElement(max_hr, "Value").text = header['MAX HR']

        ET.SubElement(lap, "Intensity").text = "Active"
        ET.SubElement(lap, "Cadence").text = "0"
        ET.SubElement(lap, "TriggerMethod").text = "Manual"

        # Approximately 3.01, why is not closer to 3? Maybe I/O time.
        secs_per_sample = seconds / float(len(data))

        track = ET.SubElement(lap, "Track")
        i = 0

        for d in data:
            point = ET.SubElement(track, "Trackpoint")
            delta_time = start_time + datetime.timedelta(seconds=i * secs_per_sample)
            ET.SubElement(point, "Time").text = self.format_time(delta_time)

            hr = ET.SubElement(point, "HeartRateBpm")
            ET.SubElement(hr, "Value").text = d['HR']
            hr = ET.SubElement(point, "Cadence").text = d['RPM']

            if self.use_distance:
                distance = float(d['DISTANCE']) * 1609.34
            else:
                distance = 0

            hr = ET.SubElement(point, "DistanceMeters").text = str(distance)
            ext = ET.SubElement(point, "Extensions")
            tpx = ET.SubElement(ext, "TPX", xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2")
            ET.SubElement(tpx, "Speed").text = "0"
            power = float(d['Power']) * self.power_fudge
            ET.SubElement(tpx, "Watts").text = str(power)
            i += 1

        tree = ET.ElementTree(root)
        tree.write(self.out_filename, encoding='utf-8', xml_declaration=True)
