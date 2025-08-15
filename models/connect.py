# Drone Core Libraries - Temel drone kütüphaneleri
import asyncio
from mavsdk import System
import argparse
# System Libraries - Sistem kütüphaneleri
import sys
import os
# Custom Libraries - Özel kütüphanelerimiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.drone_status import DroneStatus
from services.xbee_service import XbeeService
class DroneConnection(DroneStatus):
    """
    🔗 Drone Bağlantı Yöneticisi
    - MAVSDK ile drone'a bağlantı kurar
    - Telemetri verilerini başlatır
    - Sistem sağlık kontrolü yapar
    """
    def __init__(self, xbee_port = "/dev/ttyUSB0"):
        super().__init__()
        self.drone: System = None  # MAVSDK drone nesnesi
        self.xbee_service = XbeeService(
            message_received_callback=XbeeService.default_message_received_callback,
            port=xbee_port,
            max_queue_size=100
        )  # XBee servisi
        # Status task'ı constructor'da tanımlıyoruz çünkü birden fazla method'da kullanacağız

    async def connect(self, system_address: str, port: int):
        """
        🚁 Drone'a Bağlan
        Args:
            system_address: Drone IP adresi (varsayılan: udp://:14541)
            port: Bağlantı portu (varsayılan: 50060)
        """
        
        # 1️⃣ MAVSDK System objesi oluştur
        self.drone = System(port=port)
        await self.drone.connect(system_address=system_address)
        
        # 2️⃣ Bağlantı durumunu kontrol et
        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break
                    
        # 3️⃣ GPS ve home pozisyon kontrolü (kritik!)
        print("-- Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            print(f"-- Health: global={health.is_global_position_ok}, home={health.is_home_position_ok}")
            # ⚠️ Hem global hem de home position hazır olmalı
            if health.is_global_position_ok and health.is_home_position_ok:
                print("-- Global position estimate OK")
                break
                
        # 4️⃣ Telemetri verilerini sürekli takip et (arka plan task'ları)
        print("-- Starting telemetry tasks...")
        self.status_text_task = asyncio.create_task(self.print_status_text(self.drone))    # Sistem mesajları
        self._position_task = asyncio.create_task(self.update_position(self.drone))        # GPS koordinatları
        self._velocity_task = asyncio.create_task(self.print_velocity(self.drone))         # Hız vektörleri
        self._attitude_task = asyncio.create_task(self.update_attitude(self.drone))        # Yaw/Pitch/Roll açıları
        
        # 5️⃣ XBee servisini başlat (GPS ve telemetri hazır olduktan sonra)
        print("-- Starting XBee service...")
        try:
            self.xbee_service.listen()
            print("✅ XBee service started successfully!")
        except Exception as e:
            print(f"⚠️ XBee service failed to start: {e}")
            print("   Devam ediliyor... (XBee olmadan çalışabilir)")
        
