from geographiclib.geodesic import Geodesic
import math

class CalculateDistance:
    @staticmethod
    def get_lat_lon_distance(lat1, lon1, lat2, lon2):
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        distance = g['s12']
        azimuth = math.radians(g['azi1'])
        north = distance * math.cos(azimuth)
        east = distance * math.sin(azimuth)
        return north, east

    def get_turn_angle(lat1, lon1, lat2, lon2):
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        return math.radians(g['azi1'])