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

# ---- LOGGING ----
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# ---- PATHS & IMPORTS ----
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.xbee_service import XbeeService  # mevcut projene göre doğru import

# =========================
#  DRONE MISSION (SAFE)
# =========================
async def drone_mission(lat: int, lon: int, alt_unused: int, command: int) -> None:
    """
    Güvenli kalkış + güvenli irtifa garanti edilmeden goto/mission başlatmaz.
    Gelen alt parametresi kullanılmıyor (gerçek hayat standardına uygun).
    """
    # Komut kontrolü
    if command != 1:
        logging.info(f"Command {command} - mission not started")
        return

    # Sabitler (güvenlik)
    MIN_SAFE_TAKEOFF_REL_ALT = 5.0   # kalkışta ulaşılması gereken minimum relative (AGL) irtifa (m)
    CRUISE_REL_ALT = 10.0           # seyir relative (AGL) irtifa (m) - goto bu irtifada uçacak
    TAKEOFF_TIMEOUT_SEC = 30        # kalkışta güvenli irtifaya ulaşma süresi
    CONNECT_TIMEOUT_SEC = 20        # bağlantı bekleme süresi
    HEALTH_TIMEOUT_SEC = 30         # global position/home ready süresi
    GOTO_TIMEOUT_SEC = 120          # goto hedef civarına gelme izleme süresi
    TARGET_PROXIMITY_DEG = 1e-5     # ~1e-5 derece ~ 1.1 m (enlemlerde). İhtiyaca göre ayarla.
    ALT_PROXIMITY_M = 2.0           # AMSL yakınlık eşiği (m)

    # MAVSDK
    try:
        from mavsdk import System
        from mavsdk.telemetry import Position
    except Exception as e:
        logging.error(f"MAVSDK import error: {e}")
        return

    logging.info("Starting drone mission (safe mode)...")

    # Drone sistemini başlat & bağlan
    try:
        drone = System(port=50061)
        await drone.connect(system_address="udpin://0.0.0.0:14541")
    except Exception as e:
        logging.error(f"Drone connect() failed: {e}")
        return

    # Bağlantı bekle (timeout'lı)
    logging.info("Waiting for drone to connect...")
    connected = False
    start = time.time()
    async for state in drone.core.connection_state():
        if state.is_connected:
            connected = True
            logging.info("Connected to drone.")
            break
        if time.time() - start > CONNECT_TIMEOUT_SEC:
            logging.error("Connection timeout. Aborting mission.")
            return
    if not connected:
        logging.error("Connection could not be established.")
        return

    # Global position & home hazır olana kadar bekle (timeout'lı)
    logging.info("Waiting for global position estimate and home position...")
    health_ok = False
    start = time.time()
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            health_ok = True
            logging.info("Global position state is good enough for flying.")
            break
        if time.time() - start > HEALTH_TIMEOUT_SEC:
            logging.error("Health timeout (global/home not ready). Aborting mission.")
            return
    if not health_ok:
        logging.error("Health not OK. Aborting.")
        return

    # Home absolute altitude (AMSL) al
    try:
        home_abs_amsl = None
        async for home in drone.telemetry.home():
            home_abs_amsl = home.absolute_altitude_m
            break
        if home_abs_amsl is None:
            logging.error("Could not get home absolute altitude. Aborting.")
            return
        logging.info(f"Home AMSL: {home_abs_amsl:.2f} m")
    except Exception as e:
        logging.error(f"Get home altitude error: {e}")
        return

    # Arm & Takeoff
    try:
        logging.info("Arming drone.")
        await drone.action.arm()

        logging.info(f"Taking off to {MIN_SAFE_TAKEOFF_REL_ALT:.1f}m AGL (safe takeoff).")
        await drone.action.set_takeoff_altitude(MIN_SAFE_TAKEOFF_REL_ALT)
        await drone.action.set_current_speed(2.5)  # kalkışta daha güvenli hız
        await drone.action.takeoff()
    except Exception as e:
        logging.error(f"Arm/Takeoff error: {e}")
        # Emniyet için inmeyi dene
        try:
            await drone.action.land()
        except Exception:
            pass
        return

    # Güvenli irtifaya ulaşıldığını doğrula (relative altitude)
    logging.info("Verifying safe takeoff altitude...")
    reached_safe_alt = False
    start = time.time()
    current_rel_alt = 0.0
    while time.time() - start < TAKEOFF_TIMEOUT_SEC:
        try:
            async for pos in drone.telemetry.position():
                current_rel_alt = pos.relative_altitude_m
                logging.info(f"Current relative altitude: {current_rel_alt:.2f} m")
                break
            if current_rel_alt >= MIN_SAFE_TAKEOFF_REL_ALT:
                logging.info("Safe takeoff altitude reached.")
                reached_safe_alt = True
                break
        except Exception as e:
            logging.warning(f"Telemetry read error (takeoff check): {e}")
        await asyncio.sleep(0.5)

    if not reached_safe_alt:
        logging.error("Takeoff failed - did not reach safe altitude. Landing & aborting.")
        try:
            await drone.action.land()
        except Exception:
            pass
        return

    # Giden mesajdaki alt kullanılmıyor (standard gereği). Sabit CRUISE_REL_ALT kullanıyoruz.
    lat_decimal = lat / 1_000_000.0
    lon_decimal = lon / 1_000_000.0
    target_amsl = home_abs_amsl + CRUISE_REL_ALT  # hedef AMSL, sabit seyir AGL'ye göre

    logging.info(
        f"Hedef konuma gidiliyor: lat={lat_decimal:.7f}, lon={lon_decimal:.7f}, "
        f"{target_amsl:.2f} m AMSL (CRUISE_REL_ALT={CRUISE_REL_ALT} m AGL)."
    )

    # GOTO (AMSL)
    try:
        await drone.action.goto_location(lat_decimal, lon_decimal, target_amsl, 0)
    except Exception as e:
        logging.error(f"goto_location error: {e}")
        try:
            await drone.action.land()
        except Exception:
            pass
        return

    # Hedefe yakınlığı izle (timeout'lı)
    logging.info("Tracking progress towards target...")
    arrived = False
    start = time.time()
    while time.time() - start < GOTO_TIMEOUT_SEC:
        try:
            async for position in drone.telemetry.position():
                current_lat = position.latitude_deg
                current_lon = position.longitude_deg
                current_alt_amsl = position.absolute_altitude_m
                lat_diff = abs(current_lat - lat_decimal)
                lon_diff = abs(current_lon - lon_decimal)
                alt_diff = abs(current_alt_amsl - target_amsl)

                logging.info(
                    f"Δ lat={lat_diff:.7f}, lon={lon_diff:.7f}, alt={alt_diff:.2f} m"
                )
                if (lat_diff < TARGET_PROXIMITY_DEG and
                    lon_diff < TARGET_PROXIMITY_DEG and
                    alt_diff < ALT_PROXIMITY_M):
                    logging.info("Drone reached target location (within thresholds).")
                    arrived = True
                break
            if arrived:
                break
        except Exception as e:
            logging.warning(f"Telemetry read error (goto check): {e}")
        await asyncio.sleep(1.0)

    # İniş
    try:
        logging.info("Landing.")
        await drone.action.land()
        logging.info("Drone mission completed.")
    except Exception as e:
        logging.error(f"Landing error: {e}")


# =========================
#  MAIN + XBee LISTENER
# =========================
def main() -> None:
    """
    XBeeController test. XBee mesajını dinler, 'lat,lon,alt,command' formatını parse eder.
    command==1 ise güvenli mission başlatır. 'alt' DEĞERİ YOK SAYILIR.
    """
    received_data = None

    def custom_message_handler(message_dict: dict) -> None:
        """
        XBee'den gelen data callback'i.
        Beklenen format (string): "lat,lon,alt,command"
        lat/lon: 1e6 ölçeğinde integer
        alt: kullanılmıyor (sadece legacy uyumluluk için)
        command: 1 -> mission başlat
        """
        nonlocal received_data
        data = message_dict.get("data", "")
        logging.info(f"Received data: {data}")

        try:
            parts = [p.strip() for p in data.split(",")]
            if len(parts) == 4:
                lat = int(parts[0])
                lon = int(parts[1])
                alt_ignored = int(parts[2])
                command = int(parts[3])
                logging.info(
                    f"Parsed data - Lat: {lat}, Lon: {lon}, Alt(ignored): {alt_ignored}, Command: {command}"
                )

                if command == 1:
                    logging.info("Command 1 received, starting SAFE drone mission...")
                    # Callback içinden ayrı event loop aç
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(drone_mission(lat, lon, alt_ignored, command))
                    finally:
                        loop.close()
                else:
                    logging.info(f"Command {command} - mission not started")
            else:
                logging.warning("Unexpected data format. Expected: 'lat,lon,alt,command'")
        except ValueError as e:
            logging.error(f"Data parse error: {e}")
        except Exception as e:
            logging.error(f"Message handler error: {e}")

    # XBee servisini başlat
    xbee = XbeeService(
        message_received_callback=XbeeService.default_message_received_callback,
        port="/dev/ttyUSB1",
        baudrate=57600,
        max_queue_size=100,
    )
    xbee.set_custom_message_handler(custom_message_handler)
    xbee.listen()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Closing XBee...")
        xbee.close()
    except Exception as e:
        logging.error(f"Main loop error: {e}")
        try:
            xbee.close()
        except Exception:
            pass


if __name__ == "__main__":
    logging.info("Starting XBeeController (SAFE mission logic enabled)...")
    main()
    logging.info("XBeeController test completed, exiting.")
    sys.exit(0)
