import asyncio
import sys
import os
# 📂 Path ayarları - üst klasördeki modüllere erişim için
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.distance_calculation import CalculateDistance
from mavsdk.offboard import VelocityNedYaw

class SwarmDiscovery(OffboardControl):
    """
    🔄 Swarm Discovery - Kare Dalga Oscillation Misyonu
    - 10 döngülük kare pattern uçuş
    - İleri → Sol → İleri → Sağ hareket dizisi
    - Drone-relative yaw açı hesaplamaları
    """
    def __init__(self):
        super().__init__()
            
    async def square_oscillation_by_meters(self, forward_length=50.0, side_length=10.0, altitude=10.0, velocity=2.0):
        """
        🟦 Kare Dalga Oscillation Pattern
        - 4 adımlık hareket dizisini 10 kez tekrarlar
        - Her hareket GPS tabanlı mesafe kontrolü ile yapılır
        
        Args:
            forward_length: İleri hareket mesafesi (metre) - varsayılan 50m
            side_length: Yan hareket mesafesi (metre) - varsayılan 10m  
            altitude: Uçuş yüksekliği (metre) - varsayılan 10m
            velocity: Hareket hızı (m/s) - varsayılan 2m/s
        
        Pattern:
        1️⃣ İleri (forward_length metre)
        2️⃣ Sol 90° + yan hareket (side_length metre)  
        3️⃣ İleri (forward_length metre)
        4️⃣ Sağ 90° + yan hareket (side_length metre)
        """
        print("🔄 Square Oscillation başlıyor...")
        
        # 🧭 Home yaw açısını referans al (drone-relative hesaplamalar için)
        current_yaw = self.home_position["yaw"]
        
        # 🔁 10 döngü kare dalga pattern
        for cycle in range(10):
            print(f"🔢 Döngü {cycle + 1}/10")
            
            # 1️⃣ İleri git (başlangıç yönünde)
            await self.go_forward_by_meter(forward_length, altitude, velocity, current_yaw)
            
            # 2️⃣ Sol 90° dön + yan hareket
            await self.go_forward_by_meter(side_length, altitude, velocity, current_yaw + 90.0)
            
            # 3️⃣ İleri git (180° ters yönde)  
            await self.go_forward_by_meter(forward_length, altitude, velocity, current_yaw + 180.0)
            
            # 4️⃣ Sağ 90° dön + yan hareket (döngüyü tamamla)
            await self.go_forward_by_meter(side_length, altitude, velocity, current_yaw + 270.0)

        await asyncio.sleep(1)  # Döngüler arası stabilizasyon
        
        print("✅ Square Oscillation tamamlandı!")
        
async def test_swarm_discovery():
    """
    🧪 Swarm Discovery Test Fonksiyonu
    - SwarmDiscovery class'ını test eder
    - Kullanıcıdan drone port bilgisi alır
    - Tam bir mission döngüsü çalıştırır
    """
    swarmdiscovery = SwarmDiscovery()
    
    # 🔌 Kullanıcıdan bağlantı bilgisi al
    drone_port = input("Drone portu (udp://:14540): ") or "udp://:14540"
    
    # 🚀 Mission sırası
    await swarmdiscovery.connect(system_address=drone_port)        # 1. Bağlan
    await swarmdiscovery.initialize_mission()                      # 2. Kalk
    await swarmdiscovery.square_oscillation_by_meters()            # 3. Pattern uç
    await swarmdiscovery.end_mission()                            # 4. İn

if __name__ == "__main__":
    # 🎯 Ana çalıştırma noktası
    asyncio.run(test_swarm_discovery()) 