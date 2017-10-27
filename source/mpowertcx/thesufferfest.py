import bikes

class TheSufferfest(bikes.Bike):
    def load(self, peek, reader):
        if peek == ['ticks', 'time', 'power', 'cadence', 'heartRate', 'speed', 'targetPower', 'targetHeartRateZone', 'targetCadence', 'targetRpe']:
            self._load(reader)
            return True
            
        return False
        
    def _load(self, reader):
        last_time = 0.0
        
        for row in reader:
            if len(row):
                time = float(row[1])
                last_time = time
                
                self.ride.addSample(
                    power=row[2],
                    rpm=row[3],
                    hr=row[4]
                )
                
        self.ride.inferHeader(last_time)
    
    
