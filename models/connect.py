import asyncio
from mavsdk import System
import argparse
from drone_status import DroneStatus

class DroneConnection(DroneStatus):
    def __init__(self, sysid: int = 1, system_address: str = "udp://:14541"):
        super().__init__()
        self.drone = System(sysid=sysid)
        self.system_address = system_address
        #status_text_task defined in constructor because we are gonna use it in multiple methods

    # Connection Method
    async def connect(self):
        print(self.drone._sysid)
        await self.drone.connect(system_address=self.system_address)
        
        # Connection State
        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break
                    
        # Global Position Estimate
        print("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            print(f"Health: global={health.is_global_position_ok}, home={health.is_home_position_ok}")
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break
        # When drone is connected, we can start the tasks
        print("Starting telemetry tasks...")
        self.status_text_task = asyncio.ensure_future(self.print_status_text(self.drone))
        self._position_task = asyncio.ensure_future(self.update_position(self.drone))
        self._velocity_task = asyncio.ensure_future(self.print_velocity(self.drone))

    # Print Status Text Method
        
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




