# Drone Core Libraries
import asyncio
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw, OffboardError)
# System Libraries
import sys
import os
# Custom Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.connect import DroneConnection

class OffboardControl(DroneConnection):
    def __init__(self):
        super().__init__()

    async def initialize_mission(self):
        print("-- Arming...")
        await self.drone.action.arm()
        await asyncio.sleep(1)
        print("-- Setting initial setpoint")
        # Kalkışta 10 metre yukarıya çık
        await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -10.0, 0.0))

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
# ...existing code...
    
    async def end_mission(self):
        print("-- Ending mission...")
        await asyncio.sleep(1)
        await self.drone.action.land()
        self.status_text_task.cancel()
        self._position_task.cancel()
        self._velocity_task.cancel()
        print("-- Mission ended. Stopping offboard control.")
        try:
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error stopping offboard: {e}")


