import asyncio
import sys
import os
# Add parent directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.swarm_discovery import SwarmDiscovery
from optimization.distance_calculation import CalculateDistance



async def test_drone(drone_id: int, system_address: str, port: int, delay: float, 
                     xbee_port: str, drone_purpose: str, use_computer_camera:bool = False) -> None:
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
        #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

        set_lat_lon_parms = [
            (40.7445114, 30.3380595),
            (40.7445943, 30.3386202),
            (40.7440583, 30.3381680),
            (40.7441384, 30.3387387)
        ]
        swarm_drone.set_lat_lon_yaw(
            *set_lat_lon_parms
        )
        
        vertical_edge_length = CalculateDistance.get_lat_lon_distance(
            set_lat_lon_parms[0][0], set_lat_lon_parms[0][1],
            set_lat_lon_parms[1][0], set_lat_lon_parms[1][1]
        )[2] # [north, east, vertical]

        horizontal_edge_length = CalculateDistance.get_lat_lon_distance(
            set_lat_lon_parms[0][0], set_lat_lon_parms[0][1],
            set_lat_lon_parms[2][0], set_lat_lon_parms[2][1]
        )[2] # [north, east, vertical]

        #=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        
        await swarm_drone.initialize_mission(target_altitude=10.0, drone_purpose=drone_purpose)
     
        await swarm_drone.hold_mode(1.0, swarm_drone.home_position["yaw"])
        await swarm_drone.square_oscillation_by_cam_fov(
            distance1=vertical_edge_length,
            distance2=horizontal_edge_length,
            velocity=1.0,
            camera_fov_horizontal=62,
            camera_fov_vertical=49,
            image_width=800,
            image_height=600
        )
        await swarm_drone.end_mission()
    except Exception as e:
        print(f"Drone {drone_id} ERROR: {e}")

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=        
        
async def test_swarm_discovery(testing: bool, instance: int) -> None:
    """
    Run parallel tests for multiple drones in the swarm.
    """
    if instance < 1:
        raise ValueError("instance parametresi pozitif olmalı!")
    
    tasks = [
        test_drone(
            drone_id=1,
            system_address=f"udp://:14540" if testing else f"serial:///dev/ttyACM0:57600",
            port=50060,
            delay=10,
            xbee_port="/dev/ttyUSB0",
            use_computer_camera=True,
            drone_purpose="middle"
        ),
        test_drone(
            drone_id=2,
            system_address=f"udp://:14541" if testing else f"serial:///dev/ttyACM0:57600",
            port=50061,
            delay=0,
            xbee_port="/dev/ttyUSB1",
            use_computer_camera=False,
            drone_purpose="not middle"
        ) 
        
    ]
    # Start all drone tests concurrently
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"General ERROR: {e}")




if __name__ == "__main__":
    asyncio.run(test_swarm_discovery(testing = True, instance = 2))
    print("Test completed.")
