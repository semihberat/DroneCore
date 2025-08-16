import time
import logging
import sys
import asyncio
from queue import Queue, Full
from services.xbee_service import XbeeService

class DroneMission:
    def __init__(self, port=50061, system_address="udpin://0.0.0.0:14541", max_speed=5.0, tolerance=0.00001, timeout=30):
        self.port = port
        self.system_address = system_address
        self.max_speed = max_speed
        self.tolerance = tolerance
        self.timeout = timeout
        from mavsdk import System
        self.drone = System(port=self.port)

    async def connect(self):
        await self.drone.connect(system_address=self.system_address)
        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break
        print("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position state is good enough for flying.")
                break

    async def arm_and_takeoff(self):
        print("-- Arming")
        await self.drone.action.arm()
        print("-- Taking off")
        await self.drone.action.set_maximum_speed(self.max_speed)
        await self.drone.action.takeoff()

    async def goto_location(self, lat, lon):
        lat_decimal = lat / 1000000.0
        lon_decimal = lon / 1000000.0
        print(f"-- Going to location: {lat_decimal}, {lon_decimal}")
        await self.drone.action.goto_location(lat_decimal, lon_decimal, 0, 0)

    async def wait_until_arrival(self, lat, lon):
        lat_decimal = lat / 1000000.0
        lon_decimal = lon / 1000000.0
        for i in range(self.timeout):
            async for position in self.drone.telemetry.position():
                current_lat = position.latitude_deg
                current_lon = position.longitude_deg
                lat_diff = abs(current_lat - lat_decimal)
                lon_diff = abs(current_lon - lon_decimal)
                print(f"Hedefe kalan mesafe: lat={lat_diff}, lon={lon_diff}")
                if lat_diff < self.tolerance and lon_diff < self.tolerance:
                    print("✅ Drone tam hedefe ulaştı!")
                    return True
            await asyncio.sleep(1)
        print("❌ Hedefe varılamadı (timeout)")
        return False

    async def land(self):
        print("-- Landing")
        await self.drone.action.land()
        logging.info("Drone misyonu tamamlandı!")

    async def run_mission(self, lat, lon, command):
        if command != 1:
            logging.info(f"Komut {command} - misyon başlatılmıyor")
            return
        logging.info("Drone misyonu başlatılıyor...")
        await self.connect()
        await self.arm_and_takeoff()
        await self.goto_location(lat, lon)
        await self.wait_until_arrival(lat, lon)
        await self.land()

def main():
    """
    XBeeController test fonksiyonu.
    Bu fonksiyon, XBee cihazını başlatır, mesaj gönderir ve dinler.
    """
    import asyncio
    
    # Gelen mesaj datasını saklamak için değişken
    received_data = None
    
    # DroneMission nesnesini oluştur
    drone_mission = DroneMission()

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
                    loop.run_until_complete(drone_mission.run_mission(lat, lon, command))
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

# Test kodu
async def test_drone_mission():
    # Örnek lat/lon/command
    lat = 41023456  # 41.023456
    lon = 29012345  # 29.012345
    command = 1
    mission = DroneMission()
    await mission.run_mission(lat, lon, command)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # XBeeController başlatılıyor...
    main()
    # asyncio.run(test_drone_mission())
    logging.info("XBeeController testinin tüm adımları tamamlandı, çıkılıyor.")
    sys.exit(0)