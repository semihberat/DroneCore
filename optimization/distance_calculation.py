from geographiclib.geodesic import Geodesic
import math

class CalculateDistance:
    """
    📐 GPS Koordinat Hesaplama Utilities
    - GeographicLib (WGS84) kullanarak hassas mesafe hesaplamaları
    - Koordinat dönüşümleri ve vektör hesaplamaları
    - Drone navigasyonu için kritik GPS matematik fonksiyonları
    """
    
    @staticmethod
    def get_lat_lon_distance(lat1, lon1, lat2, lon2):
        """
        📏 İki GPS Koordinat Arası Mesafe ve Yön Hesaplama
        - WGS84 geodetik sistem kullanarak hassas hesaplama
        - North/East bileşenlerini ayrı ayrı döndürür
        
        Args:
            lat1, lon1: Başlangıç koordinatları (derece)
            lat2, lon2: Hedef koordinatları (derece)
            
        Returns:
            tuple: (north_distance, east_distance, total_distance)
            - north_distance: Kuzey yönündeki mesafe (metre)
            - east_distance: Doğu yönündeki mesafe (metre)  
            - total_distance: Toplam mesafe (metre)
        """
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        distance = g['s12']         # Toplam mesafe (metre)
        azimuth = math.radians(g['azi1'])  # Yön açısı (radyan)
        
        # Mesafeyi north/east bileşenlerine ayır
        north = distance * math.cos(azimuth)
        east = distance * math.sin(azimuth)
        return north, east, distance
    
    @staticmethod
    def get_turn_angle(lat1, lon1, lat2, lon2):
        """
        🧭 İki Koordinat Arası Yön Açısını Hesapla
        - Başlangıç noktasından hedef noktaya olan açıyı döndürür
        
        Args:
            lat1, lon1: Başlangıç koordinatları
            lat2, lon2: Hedef koordinatları
            
        Returns:
            float: Yön açısı (radyan cinsinden)
        """
        g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
        return math.radians(g['azi1'])
    
    @staticmethod
    def find_vectors(meters, angle_deg):
        """
        📐 Mesafe ve Açıyı North/East Bileşenlerine Ayır
        - Polar koordinatları (mesafe, açı) Kartezyen koordinatlara (north, east) dönüştürür
        - Drone hareket vektörleri için kullanılır
        
        Args:
            meters (float): Toplam mesafe (metre)
            angle_deg (float): Yön açısı (derece cinsinden, 0° = Kuzey)
        
        Returns:
            tuple: (north_m, east_m)
            - north_m: Kuzey yönündeki bileşen (metre)
            - east_m: Doğu yönündeki bileşen (metre)
        """
        angle_rad = math.radians(angle_deg)
        north_m = meters * math.cos(angle_rad)
        east_m = meters * math.sin(angle_rad)
        return north_m, east_m
    
    @staticmethod
    def find_target_position_by_velocity_and_yaw(lat, lon, velocity, yaw):
        """
        🎯 Hız ve Yaw'a Göre Hedef Pozisyon Hesapla
        - Mevcut konumdan belirtilen hız ve yaw ile hareket edildiğinde varılacak noktayı hesaplar
        - Real-time navigation için kullanılır
        
        Args:
            lat (float): Başlangıç enlemi (derece)
            lon (float): Başlangıç boylamı (derece) 
            velocity (float): Hız (m/s)
            yaw (float): Yaw açısı (derece, 0° = Kuzey)
            
        Returns:
            tuple: (target_lat, target_lon) - Hedef GPS koordinatları
        """
        # Hızı north/east bileşenlerine ayır
        north_m, east_m = CalculateDistance.find_vectors(velocity, yaw)
        g = Geodesic.WGS84.Direct(lat, lon, yaw, velocity)
        target_lat = g['lat2']
        target_lon = g['lon2']
        return target_lat, target_lon