#
# Base class for equipment
# 
class Bike(object):
    metric = False
    ride = None
    
    def __init__(self, ride):
        self.ride = ride
    
    def load(self, reader):
        raise NotImplementedError(self.__class__.__name__)

    def distance(self, d):
        if self.metric:
            return d * 1000.0
        else:
            return d * 1609.34
