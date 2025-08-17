import json
import threading
import time
import logging
import serial
import functools
import sys
import asyncio
import os
from queue import Queue, Full
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.xbee_service import XbeeService

async def drone_mission(lat: int, lon: int, alt: int, command: int) -> None:
    """
    Execute drone mission if command is 1.
    """
    if command != 1:
        logging.info(f"Command {command} - mission not started")
        return
    logging.info("Starting drone mission...")
    try:
        from mavsdk import System
        drone = System(port=50061)
        await drone.connect(system_address="udpin://0.0.0.0:14541")
        logging.info("Waiting for drone to connect...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                logging.info("Connected to drone.")
                break
        logging.info("Waiting for global position estimate...")
        async for health in drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                logging.info("Global position state is good enough for flying.")
                break
        async for terrain_info in drone.telemetry.home():
            absolute_altitude = terrain_info.absolute_altitude_m
            break
        logging.info("Arming drone.")
        await drone.action.arm()
        logging.info("Taking off.")
        await drone.action.set_takeoff_altitude(alt)
        await drone.action.set_current_speed(5.0)
        await drone.action.takeoff()
        takeoff_altitude = None
        for _ in range(10):
            async for position in drone.telemetry.position():
                takeoff_altitude = position.absolute_altitude_m
                logging.info(f"Current altitude: {takeoff_altitude}")
                break
            if takeoff_altitude and takeoff_altitude > (alt - 2):
                break
            await asyncio.sleep(1)
        lat_decimal = lat / 1000000.0
        lon_decimal = lon / 1000000.0
        logging.info(f"Going to location: {lat_decimal}, {lon_decimal}, {alt}m AMSL")
        await drone.action.goto_location(lat_decimal, lon_decimal, alt, 0)
        for _ in range(30):
            async for position in drone.telemetry.position():
                current_lat = position.latitude_deg
                current_lon = position.longitude_deg
                current_alt = position.absolute_altitude_m
                lat_diff = abs(current_lat - lat_decimal)
                lon_diff = abs(current_lon - lon_decimal)
                alt_diff = abs(current_alt - alt)
                logging.info(f"Distance to target: lat={lat_diff}, lon={lon_diff}, alt={alt_diff}")
                if lat_diff < 0.00001 and lon_diff < 0.00001:
                    logging.info("Drone reached target location.")
                    break
            await asyncio.sleep(1)
        logging.info("Landing.")
        await drone.action.land()
        logging.info("Drone mission completed.")
    except Exception as e:
        logging.error(f"Error during drone mission: {e}")

def main() -> None:
    """
    XBeeController test function. Starts XBee device, sends and receives messages.
    """
    import asyncio
    received_data = None
    def custom_message_handler(message_dict: dict) -> None:
        """
        Custom callback to handle received message data.
        """
        nonlocal received_data
        data = message_dict.get("data", "")
        logging.info(f"Received data: {data}")
        try:
            parts = data.split(',')
            if len(parts) == 4:
                lat = int(parts[0])
                lon = int(parts[1])
                alt = int(parts[2])
                command = int(parts[3])
                logging.info(f"Parsed data - Lat: {lat}, Lon: {lon}, Alt: {alt}, Command: {command}")
                if command == 1:
                    logging.info("Command 1 received, starting drone mission...")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(drone_mission(lat, lon, alt, command))
                    loop.close()
                else:
                    logging.info(f"Command {command} - mission not started")
        except ValueError as e:
            logging.error(f"Data parse error: {e}")
        except Exception as e:
            logging.error(f"Message handler error: {e}")
    xbee = XbeeService(message_received_callback=XbeeService.default_message_received_callback, port="/dev/ttyUSB1", baudrate=57600, max_queue_size=100)
    xbee.set_custom_message_handler(custom_message_handler)
    xbee.listen()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        xbee.close()

if __name__ == "__main__":
    logging.info("Starting XBeeController...")
    main()
    logging.info("XBeeController test completed, exiting.")
    sys.exit(0)