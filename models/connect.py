# Drone Core Libraries - Temel drone kütüphaneleri
import asyncio
from mavsdk import System
import argparse
# System Libraries - Sistem kütüphaneleri
import sys
import os
# Custom Libraries - Özel kütüphanelerimiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.drone_status import DroneStatus

class DroneConnection(DroneStatus):
    """
    DroneConnection: manages MAVSDK connection and telemetry tasks.
    """
    def __init__(self):
        super().__init__()
        self.drone: System = None
        # Status tasks are initialized in constructor for reuse.

    async def connect(self, system_address: str, port: int):
        """
        Connect to drone and start telemetry tasks.
        Args:
            system_address: Drone IP address (e.g. udp://:14541)
            port: MAVSDK port (e.g. 50060)
        """
        self.drone = System(port=port)
        await self.drone.connect(system_address=system_address)
        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("Drone connected.")
                break
        print("Waiting for global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("Global position OK.")
                break
        print("Starting telemetry tasks...")
        self.status_text_task = asyncio.create_task(self.print_status_text(self.drone))
        self._position_task = asyncio.create_task(self.update_position(self.drone))
        self._velocity_task = asyncio.create_task(self.print_velocity(self.drone))
        self._attitude_task = asyncio.create_task(self.update_attitude(self.drone))


