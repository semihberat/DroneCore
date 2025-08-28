# Drone Core Libraries - Temel drone kütüphaneleri
import asyncio
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw, OffboardError)
# System Libraries - Sistem kütüphaneleri
import sys
import os
import math
# Custom Libraries - Özel kütüphanelerimiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.connect import DroneConnection
from optimization.distance_calculation import CalculateDistance

class OffboardControl(DroneConnection):
    """
    OffboardControl: Combines connection and movement logic for missions.
    """
    def __init__(self):
        super().__init__()
        self.left_down_corner: tuple[float, float] | None = None
        self.left_up_corner: tuple[float, float] | None = None
        self.right_down_corner: tuple[float, float] | None = None
        self.right_up_corner: tuple[float, float] | None = None
        self.mission_ending = False  # Mission sonlandırma flag'i

    def set_lat_lon_yaw(self, left_down: tuple[float, float], left_up: tuple[float, float], 
                              right_down: tuple[float, float], right_up: tuple[float, float]) -> None:
        self.left_down_corner = left_down
        self.left_up_corner = left_up
        self.right_down_corner = right_down
        self.right_up_corner = right_up
        
    async def goto_location(self, lat: float, lon: float, target_alt: float, goto_yaw: float) -> None:
        await self.drone.action.goto_location(lat, lon, target_alt, goto_yaw)
        await self.drone.action.set_current_speed(1.5)
        for _ in range(30):
            async for position in self.drone.telemetry.position():
                current_lat = position.latitude_deg
                current_lon = position.longitude_deg
                home_abs_alt = position.absolute_altitude_m
                lat_diff = abs(current_lat - lat)
                lon_diff = abs(current_lon - lon)
                alt_diff = abs(home_abs_alt - target_alt)
                print(f"Distance to target: lat={lat_diff}, lon={lon_diff}, alt={alt_diff}")
                if lat_diff < 0.00001 and lon_diff < 0.00001:
                    print("Drone reached target location.")
                    break
            await asyncio.sleep(0.5)

    async def initialize_mission(self, target_altitude: float, drone_purpose: str) -> bool:
        """
        Stable takeoff and offboard transition with multiple attempts.
        """
        self.target_altitude = target_altitude
        print("Arming...")
        await self.drone.action.arm()
        await asyncio.sleep(2)
        print("Saving home position...")
        self.home_position = {
            "lat": self.current_position.latitude_deg,
            "lon": self.current_position.longitude_deg,
            "alt": self.current_position.absolute_altitude_m,
            "yaw": self.current_attitude.yaw_deg if self.current_attitude else 0.0
        }
        print(f"Home: Alt={self.home_position['alt']:.1f}m, Yaw={self.home_position['yaw']:.1f}°")
        print(f"Takeoff to {target_altitude}m...")
        await self.drone.action.set_takeoff_altitude(target_altitude)
        await self.drone.action.takeoff()
        print("Waiting for takeoff completion...")
        while True:
            current_alt = self.current_position.absolute_altitude_m
            altitude_diff = current_alt - self.home_position["alt"]
            if altitude_diff >= (target_altitude * 0.95):
                print(f"Takeoff OK: {altitude_diff:.1f}m")
                break
            await asyncio.sleep(0.5)
        print("Hold mode...")
        print("hata buradan kaynaklanabilir:",self.left_down_corner, self.left_up_corner, self.right_down_corner, self.right_up_corner)
        if drone_purpose != "middle":
            goto_yaw = CalculateDistance.get_turn_angle(self.left_down_corner[0], self.left_down_corner[1], 
                                                                    self.left_up_corner[0], self.left_up_corner[1])
            
            goto_yaw = math.degrees(goto_yaw)
            self.home_position["yaw"] = goto_yaw
            await self.goto_location(self.left_down_corner[0], self.left_down_corner[1], self.home_position["alt"] + self.target_altitude, goto_yaw)
        
        else:
            up_corners_middle = CalculateDistance.find_middle_of_two_points(
                self.left_up_corner[0], self.left_up_corner[1],
                self.right_up_corner[0], self.right_up_corner[1]
            )
            down_corners_middle = CalculateDistance.find_middle_of_two_points(
                self.left_down_corner[0], self.left_down_corner[1],
                self.right_down_corner[0], self.right_down_corner[1]
            )
            goto_yaw = CalculateDistance.get_turn_angle(
                down_corners_middle[0], down_corners_middle[1],
                up_corners_middle[0], up_corners_middle[1]
            )
            goto_yaw = math.degrees(goto_yaw)
            self.home_position["yaw"] = goto_yaw
            await self.goto_location(down_corners_middle[0], down_corners_middle[1], 
                                     self.home_position["alt"] + self.target_altitude, goto_yaw)
           
        await self.drone.action.hold()
        await asyncio.sleep(0.1)
        print("Preparing offboard...")
        current_alt = self.current_position.absolute_altitude_m
        altitude_diff = current_alt - self.home_position["alt"]
        success = False
        
        for attempt in range(5):
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0, self.home_position["yaw"])
            )
            await asyncio.sleep(0.5)
            try:
                await self.drone.offboard.start()
                print("Offboard mode OK.")
                success = True
                break
            except OffboardError as e:
                print(f"Offboard attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)
        if not success:
            print("Offboard transition failed!")
            return False
        await asyncio.sleep(2)
        print("Mission ready - offboard active.")
        return True

    async def end_mission(self) -> None:
        """
        End mission, stop telemetry tasks and offboard mode, then land.
        """
        # Eğer mission zaten sonlandırılıyorsa çık
        if self.mission_ending:
            print("Mission already ending, skipping...")
            return
        
        self.mission_ending = True
        print("Ending mission...")
        await asyncio.sleep(1)
        
        # Task'ları güvenli şekilde iptal et
        if hasattr(self, 'status_text_task') and self.status_text_task and not self.status_text_task.done():
            try:
                self.status_text_task.cancel()
            except Exception as e:
                print(f"Error canceling status_text_task: {e}")
        
        if hasattr(self, '_position_task') and self._position_task and not self._position_task.done():
            try:
                self._position_task.cancel()
            except Exception as e:
                print(f"Error canceling _position_task: {e}")
        
        if hasattr(self, '_velocity_task') and self._velocity_task and not self._velocity_task.done():
            try:
                self._velocity_task.cancel()
            except Exception as e:
                print(f"Error canceling _velocity_task: {e}")
        
        if hasattr(self, '_attitude_task') and self._attitude_task and not self._attitude_task.done():
            try:
                self._attitude_task.cancel()
            except Exception as e:
                print(f"Error canceling _attitude_task: {e}")
        
        print("Mission ended. Stopping offboard control.")
        try:
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error stopping offboard: {e}")
        await self.drone.action.land()

    async def hold_mode(self, hold_time: float, angle_deg_while_hold: float) -> None:
        """
        Hold position for a given time and yaw angle.
        """
        hold_start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - hold_start_time) < hold_time:
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, angle_deg_while_hold)
            )
            await asyncio.sleep(0.1)

    async def go_forward(self, velocity: float, yaw: float) -> None:
        """
        Move forward with given velocity and yaw.
        """
        velocity_north_vector, velocity_east_vector = CalculateDistance.find_vectors(
            velocity, 
            yaw
        )
        current_altitude = self.current_position.absolute_altitude_m
        target_altitude_abs = self.home_position["alt"] + self.target_altitude
        altitude_error = target_altitude_abs - current_altitude
        max_vertical_speed = 2.0
        altitude_gain = 0.8
        vertical_velocity = altitude_error * altitude_gain
        vertical_velocity = max(-max_vertical_speed, min(max_vertical_speed, vertical_velocity))
        vertical_velocity_ned = -vertical_velocity
        await self.drone.offboard.set_velocity_ned(
            VelocityNedYaw(
                velocity_north_vector,
                velocity_east_vector,
                vertical_velocity_ned,
                yaw
            )
        )

    async def go_forward_by_meter(self, forward_distance: float, velocity: float, yaw: float) -> None:
        """
        Move forward by a given distance (GPS-based).
        Args:
            forward_distance: distance to move (meters)
            velocity: max speed (m/s)
            yaw: movement direction (degrees)
        """
        start_lat = self.current_position.latitude_deg
        start_lon = self.current_position.longitude_deg
        while True:
            current_distance = CalculateDistance.get_lat_lon_distance(
                start_lat, start_lon,
                self.current_position.latitude_deg,
                self.current_position.longitude_deg
            )[2]
            remaining_distance = forward_distance - current_distance
            if remaining_distance <= 1.0:
                await self.drone.offboard.set_velocity_ned(
                    VelocityNedYaw(0.0, 0.0, 0.0, yaw)
                )
                break
            if remaining_distance <= velocity:
                current_velocity = velocity * 0.3
            else:
                current_velocity = velocity
            await self.go_forward(velocity=current_velocity, yaw=yaw)
            await asyncio.sleep(0.1)

