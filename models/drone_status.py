import asyncio 
from mavsdk import System 

class DroneStatus:
    def __init__(self):
        self.current_position = None
        self.current_velocity = None
        self.status_text_task: asyncio.Task = None

    async def print_status_text(self, drone):
        async for status_text in drone.telemetry.status_text():
            print(f"-- Status: {status_text.type}: {status_text.text}")

    async def update_position(self, drone):
        async for position in drone.telemetry.position():
            self.current_position = position
            print(f"-- Current Position: {self.current_position.latitude_deg}, {self.current_position.longitude_deg}, {self.current_position.absolute_altitude_m}")

    async def print_velocity(self, drone):
        async for odom in drone.telemetry.position_velocity_ned():
            self.current_velocity = odom.velocity
            print(f"-- Velocity: {odom.velocity.north_m_s} {odom.velocity.east_m_s} {odom.velocity.down_m_s}")