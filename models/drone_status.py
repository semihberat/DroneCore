import asyncio 
from mavsdk import System 
from mavsdk.telemetry import Position, VelocityNed, StatusText

class DroneStatus:
    """
    DroneStatus: tracks real-time telemetry and updates critical state variables.
    """
    def __init__(self):
        self.current_position: Position | None = None    # GPS coordinates
        self.current_velocity: VelocityNed | None = None # Velocity vector
        self.current_attitude = None # Yaw/Pitch/Roll
        self.status_text_task: asyncio.Task | None = None

    async def print_status_text(self, drone: System) -> None:
        """
        Print system status messages from drone.
        """
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")

    async def update_position(self, drone: System) -> None:
        """
        Update GPS position.
        """
        async for position in drone.telemetry.position():
            self.current_position = position

    async def print_velocity(self, drone: System) -> None:
        """
        Print velocity vector.
        """
        async for odom in drone.telemetry.position_velocity_ned():
            self.current_velocity = odom.velocity

    async def update_attitude(self, drone: System) -> None:
        """
        Update drone attitude (yaw, pitch, roll).
        """
        async for attitude in drone.telemetry.attitude_euler():
            self.current_attitude = attitude


