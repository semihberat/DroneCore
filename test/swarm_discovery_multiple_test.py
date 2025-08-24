import asyncio
import sys
import os
# Add parent directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.swarm_discovery import SwarmDiscovery

async def test_drone(drone_id: int, system_address: str, port: int, delay: float, xbee_port: str, use_computer_camera:bool = False) -> None:
    """
    Single drone test function.
    Args:
        drone_id: Drone identifier.
        system_address: UDP address (e.g., udp://:14540).
        port: MAVSDK port (e.g., 50060).
        delay: Startup delay in seconds.
    """
    try:
        print(f"Starting drone {drone_id}...")
        if delay > 0:
            print(f"Drone {drone_id} waiting {delay} seconds before start...")
            await asyncio.sleep(delay)
        swarm_drone = SwarmDiscovery(xbee_port=xbee_port, use_computer_camera=use_computer_camera)  # Adjust port as needed
        print(f"Connecting drone {drone_id}: {system_address}, Port: {port}")
        await swarm_drone.connect(system_address=system_address, port=port)
        await swarm_drone.initialize_mission(target_altitude=5.0)
        await swarm_drone.hold_mode(1.0, swarm_drone.home_position["yaw"])
        await swarm_drone.square_oscillation_by_cam_fov(
            distance1=30.0,
            distance2=30.0,
            velocity=1.0,
            camera_fov_horizontal=62,
            camera_fov_vertical=49,
            image_width=800,
            image_height=600
        )
        await swarm_drone.end_mission()
    except Exception as e:
        print(f"Drone {drone_id} ERROR: {e}")
        
async def test_swarm_discovery() -> None:
    """
    Run parallel tests for multiple drones in the swarm.
    """
    tasks = [
        test_drone(
            drone_id=1,
            system_address="udp://:14540",
            port=50060,
            delay=0,
            xbee_port="/dev/ttyUSB0",
            use_computer_camera=True
        ),
        # Add more test_drone calls here for additional drones if needed
    ]
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"General ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_swarm_discovery())
    print("Test completed.")
