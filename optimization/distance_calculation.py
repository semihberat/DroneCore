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
        return north, east, distance
    
    @staticmethod
    def get_turn_angle(lat1, lon1, lat2, lon2):
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        return math.radians(g['azi1'])
    
    @staticmethod
    def find_vectors(meters, angle_deg):
        """
        Verilen mesafeyi ve açıyı kullanarak kuzey ve doğu bileşenlerine ayırır.
        
        Args:
            meters (float): Mesafe
            angle_deg (float): Açı (derece cinsinden)
        
        Returns:
            tuple: (north_m, east_m)
        """
        angle_rad = math.radians(angle_deg)
        north_m = meters * math.cos(angle_rad)
        east_m = meters * math.sin(angle_rad)
        return north_m, east_m
    
    @staticmethod
    def find_target_position_by_velocity_and_yaw(lat, lon, velocity, yaw):
        """
        Verilen konum, hız ve yaw açısına göre hedef konumu hesaplar.
        
        Args:
            lat (float): Başlangıç enlemi
            lon
            (float): Başlangıç boylamı
            velocity (float): Hız (m/s)
            yaw (float): Yaw açısı (derece cinsinden)
        Returns:
            tuple: (target_lat, target_lon)
        """
        north_m, east_m = CalculateDistance.find_vectors(velocity, yaw)
        g = Geodesic.WGS84.Direct(lat, lon, yaw, velocity)
        target_lat = g['lat2']
        target_lon = g['lon2']
        return target_lat, target_lon