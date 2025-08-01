import asyncio
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw, OffboardError)
from connect import DroneConnection
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


class OffboardControl(DroneConnection):
    def __init__(self, sysid: int = 1, system_address: str = "udp://:14541"):
        super().__init__(sysid=sysid, system_address=system_address)
        self.get_lat_lon_distance = CalculateDistance.get_lat_lon_distance
        self.home_lat = None
        self.home_lon = None
        self.home_alt = None

    async def go_to_position(self, target_lat, target_lon, target_alt=10.0):
        if self.current_position is None:
            print("Current position not available.")
            return
        
        # Kalkış anındaki pozisyonu referans al
        if self.home_lat is None or self.home_lon is None or self.home_alt is None:
            self.home_lat = self.current_position.latitude_deg
            self.home_lon = self.current_position.longitude_deg
            self.home_alt = self.current_position.absolute_altitude_m

        # Hedefin NED koordinatını bir kez hesapla
        target_north, target_east = self.get_lat_lon_distance(
            self.home_lat, self.home_lon,
            target_lat, target_lon
        )

        while True:
            # Hedefe sabit pozisyon gönder
            await self.drone.offboard.set_position_velocity_ned(
                PositionNedYaw(target_north, target_east, -target_alt, 0.0),
                VelocityNedYaw(0.0, 0.0, 0.0, 0.0)
            )

            # Hedefe ne kadar yakınız, güncel konumdan hesapla
            north_err, east_err = self.get_lat_lon_distance(
                self.current_position.latitude_deg,
                self.current_position.longitude_deg,
                target_lat,
                target_lon
            )

            down_err = -(self.home_alt + target_alt - self.current_position.absolute_altitude_m)
            await asyncio.sleep(0.1)
            if abs(north_err) < 1.0 and abs(east_err) < 1.0 and abs(down_err) < 0.5:
                print("Already at the target position and altitude.")
                return

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

    async def run_mission(self, target_lat=47.397704, target_lon=8.547740):
        await self.connect()
        await self.initialize_mission()
        await asyncio.sleep(1)
        await self.go_to_position(target_lat, target_lon)
        await self.end_mission()

async def run(sysid, system_address):
    offboard_control = OffboardControl(sysid=sysid, system_address=system_address)
    await offboard_control.run_mission()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sysid", type=int, default=1, help="Drone system id")
    parser.add_argument("--system_address", type=str, default="udp://:14541", help="Drone system address")
    args = parser.parse_args()
    asyncio.run(run(args.sysid, args.system_address))