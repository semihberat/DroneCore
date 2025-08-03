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
        await asyncio.sleep(1)  # Pozisyon stabilleşsin
        self.home_position = {
            "lat": self.current_position.latitude_deg,
            "lon": self.current_position.longitude_deg,
            "alt": self.current_position.absolute_altitude_m
        }
        print(f"🏠 Home pozisyon kaydedildi: {self.home_position['lat']}, {self.home_position['lon']}")

    async def go_to_position(self, target_lat, target_lon, target_alt=10.0, hold_time=5.0):
        await asyncio.sleep(0.5)
        
        # ✅ Sabit home referansı kullan
        if self.home_position is None:
            raise Exception("Home pozisyon henüz ayarlanmamış! initialize_mission() çağırın.")
        
        # Hedefin NED koordinatını SABİT home'dan hesapla
        target_north, target_east = self.get_lat_lon_distance(
            self.home_position["lat"], self.home_position["lon"],  # ✅ Sabit referans
            target_lat, target_lon
        )

        while True:
            # ✅ DÜZELTME: Güncel konumdan hedefe açı hesapla
            angle_rad = CalculateDistance.get_turn_angle(
                self.current_position.latitude_deg,    # ✅ Güncel konum
                self.current_position.longitude_deg,   # ✅ Güncel konum  
                target_lat, target_lon                 # Hedef
            )
            angle_deg = math.degrees(angle_rad)
            
            await self.drone.offboard.set_position_velocity_ned(
                PositionNedYaw(target_north, target_east, -target_alt, angle_deg),
                VelocityNedYaw(0.0, 0.0, 0.0, angle_deg)
            )
        
            # Güncel konumdan hedefe mesafe
            north_err, east_err = self.get_lat_lon_distance(
                self.current_position.latitude_deg,
                self.current_position.longitude_deg,
                target_lat,
                target_lon
            )
            
            down_err = -(self.home_position["alt"] + target_alt - self.current_position.absolute_altitude_m)
            await asyncio.sleep(0.1)
            
            if abs(north_err) < 1.0 and abs(east_err) < 1.0 and abs(down_err) < 0.5:
                print(f"✅ Hedefe ulaşıldı: {target_lat}, {target_lon}, {target_alt}m")
                await asyncio.sleep(hold_time)
                return
