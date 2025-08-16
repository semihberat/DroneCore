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

async def drone_mission(lat, lon, alt, command):
    """
    Drone misyon fonksiyonu
    """
    if command != 1:
        logging.info(f"Komut {command} - misyon başlatılmıyor")
        return
    
    logging.info("Drone misyonu başlatılıyor...")
    
    try:
        from mavsdk import System
        
        drone = System(port=50061)
        await drone.connect(system_address="udpin://0.0.0.0:14541")

        print("Waiting for drone to connect...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break

        print("Waiting for drone to have a global position estimate...")
        async for health in drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position state is good enough for flying.")
                break

        print("Fetching amsl altitude at home location....")
        async for terrain_info in drone.telemetry.home():
            absolute_altitude = terrain_info.absolute_altitude_m
            break

        print("-- Arming")
        await drone.action.arm()

        print("-- Taking off")
        await drone.action.set_takeoff_altitude(alt)
        await drone.action.set_current_speed(5.0)  # Maksimum hız
        await drone.action.takeoff()

        # Takeoff sonrası drone'un havada olduğunu doğrula
        takeoff_altitude = None
        for i in range(10):
            async for position in drone.telemetry.position():
                takeoff_altitude = position.absolute_altitude_m
                print(f"Current altitude: {takeoff_altitude}")
                break
            if takeoff_altitude and takeoff_altitude > (alt - 2):  # Hedefe yakınsa
                break
            await asyncio.sleep(1)

        # Koordinatlara git
        lat_decimal = lat / 1000000.0  # Koordinatları decimal'e çevir
        lon_decimal = lon / 1000000.0

        print(f"-- Going to location: {lat_decimal}, {lon_decimal}, {alt}m (deniz seviyesinden)")
        await drone.action.goto_location(lat_decimal, lon_decimal, alt, 0)


        # Hedefe hassas varış kontrolü
        for i in range(30):  # 30 saniyeye kadar bekle
            async for position in drone.telemetry.position():
                current_lat = position.latitude_deg
                current_lon = position.longitude_deg
                current_alt = position.absolute_altitude_m
                lat_diff = abs(current_lat - lat_decimal)
                lon_diff = abs(current_lon - lon_decimal)
                alt_diff = abs(current_alt - alt)
                print(f"Hedefe kalan mesafe: lat={lat_diff}, lon={lon_diff}, alt={alt_diff}")
                # Nokta atışı için toleransları küçült
                if lat_diff < 0.00001 and lon_diff < 0.00001:
                    print("✅ Drone tam hedefe ulaştı!")
                    break
            await asyncio.sleep(1)

        print("-- Landing")
        await drone.action.land()

        logging.info("Drone misyonu tamamlandı!")
        
    except Exception as e:
        logging.error(f"Drone misyonu sırasında hata: {e}")

def main():
    """
    XBeeController test fonksiyonu.
    Bu fonksiyon, XBee cihazını başlatır, mesaj gönderir ve dinler.
    """
    import asyncio
    
    # Gelen mesaj datasını saklamak için değişken
    received_data = None
    
    def custom_message_handler(message_dict):
        """
        Gelen mesajların datasını yakalayan özel callback fonksiyonu.
        """
        nonlocal received_data
        data = message_dict.get("data", "")
        logging.info(f"Yakalanan data: {data}")
        
        # Data formatını parse et: lat,lon,alt,command
        try:
            parts = data.split(',')
            if len(parts) == 4:
                lat = int(parts[0])
                lon = int(parts[1]) 
                alt = int(parts[2])
                command = int(parts[3])
                
                logging.info(f"Parse edilen data - Lat: {lat}, Lon: {lon}, Alt: {alt}, Command: {command}")
                
                if command == 1:
                    logging.info("Komut 1 alındı, drone misyonu başlatılıyor...")
                    # Async fonksiyonu çalıştır
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(drone_mission(lat, lon, alt, command))
                    loop.close()
                else:
                    logging.info(f"Komut {command} - misyon başlatılmıyor")
                    
        except ValueError as e:
            logging.error(f"Data parse hatası: {e}")
        except Exception as e:
            logging.error(f"Message handler hatası: {e}")
    
    xbee = XbeeService(message_received_callback=XbeeService.default_message_received_callback, port = "/dev/ttyUSB1", baudrate=57600, max_queue_size=100)
    xbee.set_custom_message_handler(custom_message_handler)
    xbee.listen()
    
    # Test mesajı gönder
    try:
        while True:
            # xbee.send_broadcast_message("oto mesaj", construct_message=True)
            time.sleep(1)
    except KeyboardInterrupt:
        xbee.close()

if __name__ == "__main__":
    logging.info("XBeeController başlatılıyor...")
    main()
    logging.info("XBeeController testinin tüm adımları tamamlandı, çıkılıyor.")
    sys.exit(0)