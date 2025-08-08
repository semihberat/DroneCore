# Drone Core Libraries
import asyncio
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw, OffboardError)
# System Libraries
import sys
import os
# Custom Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.connect import DroneConnection
from optimization.distance_calculation import CalculateDistance

class DroneFunctionality:

    async def hold_mode(self, hold_time: float, angle_deg_while_hold: float):
        print(f"Hold modunda {hold_time} saniye bekleniyor...")
        hold_start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - hold_start_time) < hold_time:
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, angle_deg_while_hold)  # Son açıyı koru
            )
            await asyncio.sleep(0.1)  # Control loop delay
            
    async def go_forward(self,altitude = 10.0, velocity = 3, yaw = None):
        velocity_north_vector, velocity_east_vector = CalculateDistance.find_vectors(velocity, yaw if yaw is not None else self.home_position["yaw"])
        if yaw is not None:
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(
                    velocity_north_vector,
                    velocity_east_vector,
                    -altitude,
                    yaw
                )
            )
    async def go_forward_by_meter(self, forward_distance=20.0, altitude=10.0, velocity=3, yaw=0.0):
        time = forward_distance / velocity
        start_time = asyncio.get_event_loop().time()
        print("time:", time)
        yaw = yaw if yaw is not None else self.home_position["yaw"]
        while (asyncio.get_event_loop().time() - start_time) < time:
            stop_factor = velocity * 1
            await self.go_forward(altitude=altitude, velocity=velocity, yaw=yaw)
            if CalculateDistance.get_lat_lon_distance(
                self.current_position.latitude_deg,
                self.current_position.longitude_deg,
                self.home_position["lat"],
                self.home_position["lon"]
            )[2] > forward_distance - stop_factor:
                await self.go_forward(altitude=altitude, velocity=velocity * 0.5, yaw=yaw)  # Yavaşla
            await asyncio.sleep(0.1)  # Control loop delay
        
    async def set_home_position(self):
        """Home pozisyonunu kaydet"""
        if self.home_position is None:
            self.home_position = {
                "lat": self.current_position.latitude_deg,
                "lon": self.current_position.longitude_deg,
                "alt": self.current_position.absolute_altitude_m,
                "yaw": self.current_attitude.yaw_deg if self.current_attitude else 0.0
            }
            print(f"🏠 Home pozisyon kaydedildi: {self.home_position['lat']}, {self.home_position['lon']}")
        else:
            print("Home pozisyonu zaten ayarlanmış.")

    

class OffboardControl(DroneConnection, DroneFunctionality):
    def __init__(self):
        super().__init__()

    async def initialize_mission(self):
        print("-- Arming...")
        await self.drone.action.arm()
        await asyncio.sleep(1)
        print("-- Setting initial setpoint")
        # Kalkışta 10 metre yukarıya çık
        await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -10.0, 0.0))

        self.home_position = {
            "lat": self.current_position.latitude_deg ,
            "lon": self.current_position.longitude_deg,
            "alt": self.current_position.absolute_altitude_m,
            "yaw": self.current_attitude.yaw_deg if self.current_attitude else 0.0
        }

        print("-- Starting offboard mode")
        try:
            await self.drone.offboard.start()
        except OffboardError as e:
            print(f"Offboard start failed: {e}")
            return

        # Basit kalkış kontrolü
        print("-- Kalkış kontrol ediliyor...")
        start_alt = self.current_position.absolute_altitude_m
        await asyncio.sleep(5)  # 5 saniye bekle
        current_alt = self.current_position.absolute_altitude_m
        
        if current_alt - start_alt > 8:  # En az 8 metre yükseldi mi?
            print(f"✅ Kalkış başarılı: {current_alt - start_alt:.1f}m yükseldi")
        else:
            print(f"⚠️ Kalkış eksik: Sadece {current_alt - start_alt:.1f}m yükseldi")

        
        await asyncio.sleep(1)  # Pozisyon stabilleşsin
        await self.set_home_position()

    async def end_mission(self):
        print("-- Ending mission...")
        await asyncio.sleep(1)
        
        self.status_text_task.cancel()
        self._position_task.cancel()
        self._velocity_task.cancel()
        print("-- Mission ended. Stopping offboard control.")
        try:
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error stopping offboard: {e}")
        await self.drone.action.land()

