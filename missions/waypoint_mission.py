#Drone Core Libraries
import asyncio
import math
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw)
#System Libraries
import argparse
import sys
import os
#Custom Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.distance_calculation import CalculateDistance

class WaypointMission(OffboardControl):
    def __init__(self):
        super().__init__()
        self.get_lat_lon_distance = CalculateDistance.get_lat_lon_distance
        self.get_turn_angle = CalculateDistance.get_turn_angle
        self.home_position = None  # ✅ Sabit home referansı

    async def initialize_mission(self):
        """Mission başlatıldığında home pozisyonunu kaydet"""
        await super().initialize_mission()
        # Home pozisyonunu bir kez kaydet ve değiştirme
    
    async def go_to_position(self, target_lat, target_lon, target_alt=10.0, hold_time=0.0, target_speed=5.0):
        await asyncio.sleep(0.5)
        
        # ✅ Sabit home referansı kullan
        if self.home_position is None:
            raise Exception("Home pozisyon henüz ayarlanmamış! initialize_mission() çağırın.")
        
        print(f"🎯 Hedefe gidiyor: {target_lat}, {target_lon}, {target_alt}m")
        
        # ✅ Her waypoint için güncel konumdan hedefe mesafe ve hız hesapla
        while True:
            # Güncel konumdan hedefe mesafe
            target_north, target_east, distance = self.get_lat_lon_distance(
                self.current_position.latitude_deg,  # ✅ Güncel konum
                self.current_position.longitude_deg, # ✅ Güncel konum
                target_lat, target_lon
            )

            # ✅ travel_time parametresine göre hız hesapl
            # a
            max_speed = min(target_speed, 20.0)  # Maksimum 20 m/s güvenlik sınırı
            optimal_stop_distance = max_speed * 1.0
            
            if distance > optimal_stop_distance:  # Eğer mesafe 5 saniyelik hızdan büyükse
                target_north_vel = (target_north / distance) * max_speed
                target_east_vel = (target_east / distance) * max_speed
            else:
                target_north_vel = target_north * 0.1  # Yakınken yavaşla
                target_east_vel = target_east * 0.1
                
            target_down_vel = -(self.home_position["alt"] + target_alt - self.current_position.absolute_altitude_m) * 0.5
            
            # ✅ DÜZELTME: Güncel konumdan hedefe açı hesapla
            angle_rad = CalculateDistance.get_turn_angle(
                self.current_position.latitude_deg,    # ✅ Güncel konum
                self.current_position.longitude_deg,   # ✅ Güncel konum  
                target_lat, target_lon                 # Hedef
            )
            angle_deg = math.degrees(angle_rad)
            
            # ✅ Güncel drone yaw açısını da göster
            current_yaw = self.current_attitude.yaw_deg if self.current_attitude else "N/A"
            print(f"🧭 Hedef açı: {angle_deg:.1f}°, Güncel yaw: {current_yaw}°")
            
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(target_north_vel, target_east_vel, target_down_vel, angle_deg)
            )
            if distance < optimal_stop_distance:
                break
     
        print(f"⏸️ Hold modunda {hold_time} saniye bekleniyor...")
        hold_start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - hold_start_time) < hold_time:
            # Sıfır velocity ile pozisyonda kal
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, angle_deg)  # Son açıyı koru
            )
            await asyncio.sleep(0.1)
        
        print(f"✅ Hold tamamlandı!")

        await self.hold_mode(hold_time, angle_deg)