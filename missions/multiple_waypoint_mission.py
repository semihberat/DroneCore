import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.waypoint_mission import WaypointMission

class MultipleWaypointMission(WaypointMission):
    def __init__(self):
        super().__init__()
    
    # waypoint_mission method to handle multiple waypoints
    async def multiple_waypoint_mission(self, waypoints: list[tuple[float, float, float, float]]):
        if not waypoints:
            print("No waypoints provided.")
            return
        
        for i, waypoint in enumerate(waypoints, 1):
            target_lat, target_lon, target_alt, hold_time, travel_time = waypoint
            print(f"🎯 Waypoint {i}/{len(waypoints)}: {target_lat}, {target_lon}, {target_alt}m")
            await self.go_to_position(target_lat, target_lon, target_alt, hold_time, travel_time)
            await asyncio.sleep(0.2)

    async def run_waypoint_mission(self, waypoints, sysid=1, system_address="udp://:14540"):
        await self.connect(sysid=sysid, system_address=system_address)
        await self.initialize_mission()
        await self.multiple_waypoint_mission(waypoints)
        await self.end_mission()

