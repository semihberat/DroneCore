# Drone Core Libraries - Temel drone kütüphaneleri
import asyncio
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw, OffboardError)
# System Libraries - Sistem kütüphaneleri
import sys
import os
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
        self.target_altitude: float | None = None

    async def initialize_mission(self, target_altitude: float) -> bool:
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
            if altitude_diff >= (target_altitude * 0.9):
                print(f"Takeoff OK: {altitude_diff:.1f}m")
                break
            await asyncio.sleep(1)
        await asyncio.sleep(0.1)
        print("Hold mode...")
        await self.drone.action.hold()
        await asyncio.sleep(0.1)
        print("Preparing offboard...")
        current_alt = self.current_position.absolute_altitude_m
        current_yaw = self.current_attitude.yaw_deg if self.current_attitude else self.home_position["yaw"]
        altitude_diff = current_alt - self.home_position["alt"]
        success = False
        for attempt in range(5):
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(0.0, 0.0, -altitude_diff, current_yaw)
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
        print("Ending mission...")
        await asyncio.sleep(1)
        self.status_text_task.cancel()
        self._position_task.cancel()
        self._velocity_task.cancel()
        self._attitude_task.cancel()
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
        altitude_gain = 0.9
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

