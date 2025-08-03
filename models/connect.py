#Drone Core Libraries
import asyncio
from mavsdk import System
import argparse
#System Libraries
import sys
import os
#Custom Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.drone_status import DroneStatus

class DroneConnection(DroneStatus):
    def __init__(self):
        super().__init__()
        self.drone: System = None
        #status_text_task defined in constructor because we are gonna use it in multiple methods

    # Connection Method
    async def connect(self, sysid: int = 1, system_address: str = "udp://:14541", 
                      port: int=50060):
        
        print(f"-- Connecting to drone with System ID: {sysid}")
        self.drone = System(sysid=sysid, port=port)
        await self.drone.connect(system_address=system_address)
        # Connection State
        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break
                    
        # Global Position Estimate
        print("-- Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            print(f"-- Health: global={health.is_global_position_ok}, home={health.is_home_position_ok}")
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break
        # When drone is connected, we can start the tasks
        print("-- Starting telemetry tasks...")
        self.status_text_task = asyncio.ensure_future(self.print_status_text(self.drone))
        self._position_task = asyncio.ensure_future(self.update_position(self.drone))
        self._velocity_task = asyncio.ensure_future(self.print_velocity(self.drone))
        

