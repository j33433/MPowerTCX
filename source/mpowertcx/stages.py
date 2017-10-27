import bikes

class Stages(bikes.Bike):
    def load(self, peek, reader):
        if peek[0] == 'Stages_Data':
            self._load(reader)
            return True
            
        return False
        
    def _load(self, reader):
        self.metric = True
        distance = 0.0
        header_found = False
        last_time = 0
        
        for row in reader:
            if row == []:
                pass
            elif row[0] == 'English':
                self.metric = False
            elif row[0] == 'Ride_Totals':
                self._load_header(reader)
                header_found = True
            elif len(row) == 6:
                time = self._parse_time(row[0])
                last_time = time
                
                if time >= 0:
                    # ['Time', 'Miles', 'MPH', 'Watts', 'HR', 'RPM']
                    # TODO: maybe use this method on all file formats.
                    #       Infer distance from MPH.
                    distance += float(row[2]) / (60.0 * 60.0)
                    
                    self.ride.addSample(
                        power=row[3],
                        rpm=row[5],
                        hr=row[4],
                        distance=self.distance(distance)
                    )
                    pass
                else:
                    print ("skip %r" % row)
            else:
                print ("skip %r" % row)
        
        if not header_found:
            print ("stages header missing")
            self.ride.inferHeader(last_time)
        
    def _load_header(self, reader):
        header = {}
        
        for row in reader:
            if len(row):
                header[row[0]] = row[1]
            else:
                break

        parts = header['Time'].split(':')
        h = 0
        m = 0 
        s = 0
        
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2])
        elif len(parts) == 2:
            m = int(parts[0])
            s = int(parts[1])
        elif len(parts) == 2:
            s = int(parts[0])
        
        time = h * 60 * 60 + m * 60 + s    
        
        self.ride.header.setSummary(
            time=time,
            distance=self.distance(float(header["Distance"])),
            average_power=header["Watts_Avg"],
            max_power=header["Watts_Max"],
            average_rpm=header["RPM_Avg"],
            max_rpm=header["RPM_Max"],
            average_hr=header["HR_Avg"],
            max_hr=header["HR_Max"],
            calories=header["KCal"]
        )

    def _parse_time(self, time):
        # I've seen mm:ss or mm:ss:00 so far 
        parts = time.split(':')
        
        if len(parts) == 2 or len(parts) == 3:
            try:
                minutes = int(parts[0])
                seconds = int(parts[1])
                result = minutes * 60 + seconds
            except:
                result = -1
        else:
            result = -1
            
        return result

        