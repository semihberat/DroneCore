import asyncio
from mavsdk import System
import argparse

class DroneConnection:
    def __init__(self, sysid: int = 1, system_address: str = "udp://:14541"):
        self.drone = System(sysid=sysid)
        self.system_address = system_address
        #status_text_task defined in constructor because we are gonna use it in multiple methods
        self.status_text_task: asyncio.Task = None

    # Connection Method
    async def connect(self):
        print(self.drone._sysid)
        await self.drone.connect(system_address=self.system_address)
        self.status_text_task = asyncio.ensure_future(self.print_status_text(self.drone))

        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break

        print("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            print(f"Health: global={health.is_global_position_ok}, home={health.is_home_position_ok}")
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break

    # Print Status Text Method
    async def print_status_text(self, drone):
        try:
            async for status_text in drone.telemetry.status_text():
                print(f"Status: {status_text.type}: {status_text.text}")
        except asyncio.CancelledError:
            return
        
    async def end_mission(self):
        await asyncio.sleep(1)
        await self.drone.action.land()
        self.status_text_task.cancel()

async def run(sysid, system_address):
    drone_connection = DroneConnection(sysid=sysid)
    await drone_connection.connect(system_address=system_address)
    await asyncio.sleep(5)
    await drone_connection.end_mission()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sysid", type=int, default=1, help="Drone system id")
    parser.add_argument("--system_address", type=str, default="udp://:14541", help="Drone system address")
    args = parser.parse_args()

    asyncio.run(run(args.sysid, args.system_address))




