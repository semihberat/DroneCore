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

class DroneConnection(DroneStatus):
    """
    🔗 Drone Bağlantı Yöneticisi
    - MAVSDK ile drone'a bağlantı kurar
    - Telemetri verilerini başlatır
    - Sistem sağlık kontrolü yapar
    """
    def __init__(self):
        super().__init__()
        self.drone: System = None  # MAVSDK drone nesnesi
        # Status task'ı constructor'da tanımlıyoruz çünkü birden fazla method'da kullanacağız

    async def connect(self, system_address: str = "udp://:14541", 
                      port: int=50060):
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
        self.status_text_task = asyncio.ensure_future(self.print_status_text(self.drone))    # Sistem mesajları
        self._position_task = asyncio.ensure_future(self.update_position(self.drone))        # GPS koordinatları
        self._velocity_task = asyncio.ensure_future(self.print_velocity(self.drone))         # Hız vektörleri
        self._attitude_task = asyncio.ensure_future(self.update_attitude(self.drone))        # Yaw/Pitch/Roll açıları
        

