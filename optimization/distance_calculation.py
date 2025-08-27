from geographiclib.geodesic import Geodesic
import math

class CalculateDistance:
    """
    Utilities for GPS-based distance and vector calculations using GeographicLib (WGS84).
    """
    @staticmethod
    def get_lat_lon_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float, float]:
        """
        Calculate north/east/total distance between two GPS coordinates (meters).
        Returns: (north_distance, east_distance, total_distance)
        """
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        distance = g['s12']
        azimuth = math.radians(g['azi1'])
        north = distance * math.cos(azimuth)
        east = distance * math.sin(azimuth)
        return north, east, distance

    @staticmethod
    def get_turn_angle(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate heading angle (radians) from start to target GPS coordinates.
        """
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        return math.radians(g['azi1'])

    @staticmethod
    def find_vectors(meters: float, angle_deg: float) -> tuple[float, float]:
        """
        Convert polar coordinates (meters, angle_deg) to north/east vector components.
        Returns: (north_m, east_m)
        """
        angle_rad = math.radians(angle_deg)
        north_m = meters * math.cos(angle_rad)
        east_m = meters * math.sin(angle_rad)
        return north_m, east_m

    @staticmethod
    def find_target_position_by_velocity_and_yaw(lat: float, lon: float, velocity: float, yaw: float) -> tuple[float, float]:
        """
        Calculate target GPS position given start, velocity, and yaw angle.
        Returns: (target_lat, target_lon)
        """
        north_m, east_m = CalculateDistance.find_vectors(velocity, yaw)
        g = Geodesic.WGS84.Direct(lat, lon, yaw, velocity)
        target_lat = g['lat2']
        target_lon = g['lon2']
        return target_lat, target_lon
    
    @staticmethod
    def find_middle_of_two_points(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
        """
        Find the geographical midpoint between two GPS coordinates.
        Returns: (mid_lat, mid_lon)
        """
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        return mid_lat, mid_lon
    