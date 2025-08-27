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

# Global XBee service instance
xbee = None

def custom_message_handler(message_dict: dict) -> None:
    """
    Custom callback to handle received message data.
    """
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
                logging.info("Command 1 received - sending feedback and starting drone mission...")
                # Feedback gönder (command=2)
                send_feedback_message(xbee, lat, lon, alt)
                # Drone misyonunu başlat
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(drone_mission(lat, lon, alt, command))
                loop.close()
                
            elif command == 2:
                logging.info("Feedback received - message confirmed!")
                # Feedback alındı log'u                
            else:
                logging.info(f"Command {command} - no action taken")
                
    except ValueError as e:
        logging.error(f"Data parse error: {e}")
    except Exception as e:
        logging.error(f"Message handler error: {e}")

def send_feedback_message(xbee_service: XbeeService, lat: int, lon: int, alt: int) -> None:
    """
    Send feedback message (command=2) to confirm message received.
    """
    try:
        feedback_message = f"{lat},{lon},{alt},2"
        logging.info(f"Sending feedback: {feedback_message}")
        
        # XBee ile feedback gönder
        if xbee_service:
            success = xbee_service.send_broadcast_message(feedback_message, False)
            if success:
                logging.info("Feedback sent successfully!")
            else:
                logging.error("Feedback send failed!")
        else:
            logging.error("XBee service not available for feedback")
            
    except Exception as e:
        logging.error(f"Feedback message error: {e}")

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
        drone = System()
        await drone.connect(system_address="serial:///dev/ttyACM0:57600")
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
                
            
        async for home in drone.telemetry.home():
            home_abs_alt = home.absolute_altitude_m
            logging.info(f"Home altitude (AMSL): {home_abs_alt:.2f} m")
            break

        async for terrain_info in drone.telemetry.home():
            absolute_altitude = terrain_info.absolute_altitude_m
            break
        logging.info("Arming drone.")
        await drone.action.arm()
        logging.info("Taking off to 5m above ground.")
        await drone.action.set_takeoff_altitude(5.0)
        await drone.action.takeoff()
  
        
        # Drone en az 3 metre irtifaya ulaşana kadar bekle

        takeoff_reached = False
        for _ in range(20):  # max 20 sn bekle
            async for position in drone.telemetry.position():
                relative_alt = position.absolute_altitude_m - home_abs_alt
                logging.info(f"Relative altitude: {relative_alt:.2f} m")
                break

            if relative_alt >= 3.0:
                logging.info("Takeoff altitude reached ?")
                takeoff_reached = True
                break
            await asyncio.sleep(1)
        if not takeoff_reached:
            logging.error("Takeoff failed: relative altitude not reached!")
            return
        lat_decimal = lat / 1000000.0
        lon_decimal = lon / 1000000.0
        target_altitude = home_abs_alt+ 5
        logging.info(f"Hedef konuma gidiliyor: {lat_decimal}, {lon_decimal}, {target_altitude}m AMSL (deniz seviyesinden)")
        await drone.action.goto_location(lat_decimal, lon_decimal, target_altitude, 0)
        await drone.action.set_current_speed(1.5)
        for _ in range(30):
            async for position in drone.telemetry.position():
                current_lat = position.latitude_deg
                current_lon = position.longitude_deg
                home_abs_alt = position.absolute_altitude_m
                lat_diff = abs(current_lat - lat_decimal)
                lon_diff = abs(current_lon - lon_decimal)
                alt_diff = abs(home_abs_alt - alt)
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
    # Global xbee değişkeni
    global xbee
    
    xbee = XbeeService(message_received_callback=XbeeService.default_message_received_callback, port="/dev/ttyUSB0", baudrate=57600, max_queue_size=100)
    xbee.set_custom_message_handler(custom_message_handler)
    xbee.listen()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if xbee:
            xbee.close()

if __name__ == "__main__":
    logging.info("Starting XBeeController...")
    main()
    logging.info("XBeeController test completed, exiting.")
    sys.exit(0)