# Drone Core Libraries - Temel drone kütüphaneleri
import asyncio
import math
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw)
# System Libraries - Sistem kütüphaneleri
import argparse
import sys
import os
# Custom Libraries - Özel kütüphanelerimiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.distance_calculation import CalculateDistance

class WaypointMission(OffboardControl):
    """
    🗺️ GPS Waypoint Navigation Sistemi
    - GPS koordinatlarına hassas navigasyon (0.5m hassasiyet)
    - 3 katmanlı hız kontrolü (otomatik yavaşlama)
    - Real-time mesafe hesaplaması ve feedback
    - Hold mode desteği (varışta bekleme)
    """
    def __init__(self):
        super().__init__()
        # 📐 GPS hesaplama fonksiyonlarını kısayol olarak tanımla
        self.get_lat_lon_distance = CalculateDistance.get_lat_lon_distance
        self.get_turn_angle = CalculateDistance.get_turn_angle
        self.home_position = None  # 📍 Sabit home referans noktası

    async def initialize_mission(self):
        """
        🏠 Mission Başlatma ve Home Position Kaydetme
        - Parent class'ın initialize_mission'ını çağırır
        - Home position bir kez kaydedilir ve değişmez
        """
        await super().initialize_mission()
        # Home pozisyonu parent class'ta ayarlanır, burada sadece kullanırız
    
    async def go_to_position(self, target_lat, target_lon, target_alt=10.0, hold_time=0.0, target_speed=5.0):
        """
        🎯 GPS Koordinatına Hassas Navigasyon
        - 0.5 metre hassasiyetle hedefe gider
        - 3 katmanlı hız kontrolü (5m+/2-5m/0.5-2m mesafelerine göre)
        - Real-time mesafe feedback
        - Varışta optional hold mode
        
        Args:
            target_lat: Hedef latitude (GPS koordinatı)
            target_lon: Hedef longitude (GPS koordinatı)  
            target_alt: Hedef yükseklik (metre) - varsayılan 10m
            hold_time: Varışta bekleme süresi (saniye) - varsayılan 0
            target_speed: Maksimum hız (m/s) - varsayılan 5m/s
        """
        await asyncio.sleep(0.5)  # Stabilizasyon gecikmesi
        
        # ⚠️ Home position kontrolü (kritik!)
        if self.home_position is None:
            raise Exception("Home pozisyon henüz ayarlanmamış! initialize_mission() çağırın.")
        
        print(f"🎯 Hedefe gidiyor: {target_lat}, {target_lon}, {target_alt}m")
        
        # 🔁 GPS tabanlı navigasyon döngüsü
        while True:
            # 📏 Güncel konumdan hedefe olan mesafeyi hesapla
            target_north, target_east, distance = self.get_lat_lon_distance(
                self.current_position.latitude_deg,     # Güncel latitude
                self.current_position.longitude_deg,    # Güncel longitude
                target_lat, target_lon
            )

            print(f"📏 Kalan mesafe: {distance:.1f}m")
            
            # ✅ Hassas durma kriteri: 0.5 metre
            if distance <= 0.5:
                print("🛑 Hedefe ulaşıldı!")
                # Son pozisyonda tam dur
                await self.drone.offboard.set_velocity_ned(
                    VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                )
                break
            
            # 🚀 Akıllı hız kontrolü (güvenlik sınırı ile)
            max_speed = min(target_speed, 20.0)  # Maksimum 20 m/s güvenlik sınırı
            
            if distance <= 2.0:  # 2 metre kalınca çok yavaş (%20)
                speed_factor = 0.2
                print("🐌 Çok yavaş yaklaşım...")
            elif distance <= 5.0:  # 5 metre kalınca yavaş (%50)
                speed_factor = 0.5
                print("🚶 Yavaş yaklaşım...")
            else:  # Normal hız (%100)
                speed_factor = 1.0
                
            # 📐 Hedefe doğru hız vektörlerini hesapla (normalize edilmiş)
            target_north_vel = (target_north / distance) * max_speed * speed_factor
            target_east_vel = (target_east / distance) * max_speed * speed_factor
                
            # ✈️ Yükseklik kontrolü (yumuşak geçiş)
            target_down_vel = -(self.home_position["alt"] + target_alt - self.current_position.absolute_altitude_m) * 0.3
            
            # 🧭 Hedefe doğru yaw açısını hesapla
            angle_rad = CalculateDistance.get_turn_angle(
                self.current_position.latitude_deg,     # Mevcut pozisyon
                self.current_position.longitude_deg,  
                target_lat, target_lon                  # Hedef pozisyon
            )
            angle_deg = math.degrees(angle_rad)  # Radyandan dereceye çevir
            
            # 🎮 Hesaplanan hız vektörlerini drone'a gönder
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(target_north_vel, target_east_vel, target_down_vel, angle_deg)
            )
            
            await asyncio.sleep(0.1)  # Kontrol döngüsü gecikmesi
     
        # ⏸️ Hold Mode (varışta bekleme)
        if hold_time > 0:
            print(f"⏸️ Hold modunda {hold_time} saniye bekleniyor...")
            await self.hold_mode(hold_time, angle_deg)
            print(f"✅ Hold tamamlandı!")