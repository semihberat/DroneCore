import asyncio
import sys
import os
# Add parent directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.drone_vision_calculator import DroneVisionCalculator
from aruco_mission.realtime_camera_viewer import RealtimeCameraViewer
from aruco_mission.computer_camera_test import ComputerCameraTest
import threading
from mavsdk.offboard import VelocityNedYaw
from services.xbee_service import XbeeService

RealtimeCameraViewer = ComputerCameraTest

class SwarmDiscovery(OffboardControl):
    """
    SwarmDiscovery mission: square oscillation flight and ArUco-based precision landing.
    """
    def __init__(self, xbee_port: str = None):
        super().__init__()
        self.pi_cam = RealtimeCameraViewer()
        self.mission_completed = False
        self.xbee_service = XbeeService(
            message_received_callback=XbeeService.default_message_received_callback,
            port=xbee_port,
            max_queue_size=100,
            baudrate=57600
        )

    async def connect(self, system_address: str, port: int):
        await super().connect(system_address=system_address, port=port)
        print("-- Starting XBee service...")
        try:
            self.xbee_service.listen()
            print("✅ XBee service started successfully!")
        except Exception as e:
            print(f"⚠️ XBee service failed to start: {e}")
            print("   Continuing without XBee...")

    async def square_oscillation_by_meters(self, long_distance: float, short_distance: float, velocity: float, repeat_count: int):
        """
        Square oscillation pattern flight.
        Args:
            long_distance: forward movement (meters)
            short_distance: side movement (meters)
            velocity: movement speed (m/s)
            repeat_count: number of cycles
        """
        print("Square Oscillation started...")
        current_yaw = self.home_position["yaw"]
        for cycle in range(repeat_count):
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)
            await self.go_forward_by_meter(long_distance, velocity, current_yaw + 180.0)
            await self.hold_mode(1.0, current_yaw + 180.0)
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)
        if current_yaw + 90 != self.home_position["yaw"]:
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)
        await asyncio.sleep(1)
        print("Square Oscillation finished!")

    async def square_oscillation_by_cam_fov(
        self,
        distance1: float,
        distance2: float,
        velocity: float,
        camera_fov_horizontal: float,
        camera_fov_vertical: float,
        image_width: int,
        image_height: int
    ):
        """
        Square oscillation flight based on camera FOV and ArUco detection.
        """
        drone_vision_calculator = DroneVisionCalculator(
            camera_fov_horizontal=camera_fov_horizontal,
            camera_fov_vertical=camera_fov_vertical,
            image_width=image_width,
            image_height=image_height
        )
        threading.Thread(target=self.pi_cam.show_camera_with_detection, ).start()
        ground_coverage = drone_vision_calculator.calculate_ground_coverage(self.target_altitude)
        short_distance = ground_coverage["width_m"] / 2
        repeat_count = int(distance2 / short_distance / 2)
        sqosc_async_thread = asyncio.create_task(
            self.square_oscillation_by_meters(
                long_distance=distance1,
                short_distance=short_distance,
                repeat_count=repeat_count,
                velocity=velocity
            )
        )
        while not sqosc_async_thread.done() and not self.pi_cam.is_found:
            await asyncio.sleep(0.1)
        if self.pi_cam.is_found:
            sqosc_async_thread.cancel()
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
            )
            await self.hold_mode(1.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
            print("ArUco found! Precision landing started...")
            while not self.pi_cam.is_centered and not self.mission_completed:
                x, y, z = self.pi_cam.get_averaged_position()
                # Only print if not centered
                if abs(x) > 0.02 or abs(y) > 0.02:
                    print(f"Correction: X={x:.2f} Y={y:.2f}")
                    correction_speed = 0.5
                    move_x = x * correction_speed
                    move_y = y * correction_speed
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(move_x, move_y, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                    )
                    await asyncio.sleep(0.2)
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                    )
                    await asyncio.sleep(0.2)
                else:
                    print("ArUco centered!")
                    break
            if self.pi_cam.is_centered:
                print("Precision landing complete. Sending XBee message...")
                lat_scaled = int(self.current_position.latitude_deg * 1000000)
                lon_scaled = int(self.current_position.longitude_deg * 1000000)
                alt_scaled = int(self.current_position.absolute_altitude_m * 10)
                simple_message = f"{lat_scaled},{lon_scaled},{alt_scaled},1"
                print(f"XBee message: {simple_message}")
                try:
                    if hasattr(self, 'xbee_service') and self.xbee_service:
                        success = False
                        for attempt in range(10):  # Try up to 10 times
                            result = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self.xbee_service.send_broadcast_message,
                                simple_message,
                                False
                            )
                            if result:
                                print(f"✅ XBee message sent on attempt {attempt+1}")
                                success = True
                                break
                            else:
                                print(f"⚠️ Attempt {attempt+1} failed, retrying...")
                                await asyncio.sleep(0.1)  # Wait 100ms
                        if success:
                            self.mission_completed = True
                        else:
                            print("❌ XBee message failed after 10 attempts.")
                            self.mission_completed = True  # End mission anyway
                    else:
                        print("XBee service not found.")
                        self.mission_completed = True
                except Exception as e:
                    print(f"XBee error: {e}")
                    self.mission_completed = True
                print("Mission complete.")
                await asyncio.sleep(1)
                await self.go_forward_by_meter(5.0, 1.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                await self.end_mission()
            else:
                print("ArUco not centered.")
        if self.mission_completed:
            print("Mission complete - XBee message sent.")
        else:
            print("Mission failed - ArUco not found or not centered.")
        print("Mission finished!")



