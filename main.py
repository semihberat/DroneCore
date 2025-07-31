import asyncio

from models.connect import DroneConnection 


class OffboardControl(DroneConnection):
    def __init__(self, sysid: int = 1, system_address: str = "udp://:14541"):
        super().__init__(sysid=sysid, system_address=system_address)
        self.current_position = None

    async def update_position(self):
        async for position in self.drone.telemetry.position():
            self.current_position = position
            print(f"Current Position: {self.current_position.latitude_deg}, {self.current_position.longitude_deg}, {self.current_position.absolute_altitude_m}")
            
    async def formation_control(self):
        # Implement formation control logic here
        pass

    async def run_mission(self):
        await self.connect()
        self._position_task = asyncio.ensure_future(self.update_position())
       
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