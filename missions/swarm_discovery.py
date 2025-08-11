import asyncio
import sys
import os
# 📂 Path ayarları - üst klasördeki modüllere erişim için
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.distance_calculation import CalculateDistance
from mavsdk.offboard import VelocityNedYaw
from optimization.drone_vision_calculator import DroneVisionCalculator

class SwarmDiscovery(OffboardControl):
    """
    🔄 Swarm Discovery - Kare Dalga Oscillation Misyonu
    - 10 döngülük kare pattern uçuş
    - İleri → Sol → İleri → Sağ hareket dizisi
    - Drone-relative yaw açı hesaplamaları
    """
    def __init__(self):
        super().__init__()
            
    async def square_oscillation_by_meters(self, long_distance=50.0, short_distance=50.0, 
                                            velocity=10.0, repeat_count=10):
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
        for cycle in range(repeat_count):

            # 1️⃣ İleri git (başlangıç yönünde)
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)  # Stabilizasyon için kısa bekleme
            # 2️⃣ Sol 90° dön + yan hareket
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)  # Stabilizasyon için kısa bekleme
            # 3️⃣ İleri git (180° ters yönde)  
            await self.go_forward_by_meter(long_distance, velocity, current_yaw + 180.0)
            await self.hold_mode(1.0, current_yaw + 180.0)
            # 4️⃣ Sağ 90° dön + yan hareket (döngüyü tamamla)
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)
        
        if current_yaw + 90 != self.home_position["yaw"]:
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)  # Stabilizasyon için kısa bekleme
            

        await asyncio.sleep(1)  # Döngüler arası stabilizasyon
        
        print("✅ Square Oscillation tamamlandı!")

    async def square_oscillation_by_cam_fov(self, 
                                                distance1=30.0, 
                                                distance2=30.0,                               
                                                velocity=2.0,
                                                camera_fov_horizontal=62,
                                                camera_fov_vertical=49,
                                                image_width=1920,
                                                image_height=1080):
        drone_vision_calculator = DroneVisionCalculator(
            camera_fov_horizontal=camera_fov_horizontal,  # Pi Cam V2
            camera_fov_vertical=camera_fov_vertical,    # Pi Cam V2
            image_width=image_width,           # Önerilen çözünürlük
            image_height=image_height           # 4:3 oran
        )

        await self.square_oscillation_by_meters(
            long_distance=distance1,  # 50 metre ileri
            short_distance=drone_vision_calculator.calculate_ground_coverage(self.target_altitude)["width_m"] / 2,  # Yarım genişlik
            repeat_count = int(distance2 /(drone_vision_calculator.calculate_ground_coverage(self.target_altitude)["width_m"] / 2)/2),  # Yarım genişlik

            velocity=velocity,
        
        )
        
async def test_swarm_discovery():
    """
    🧪 Swarm Discovery Test Fonksiyonu
    - SwarmDiscovery class'ını test eder
    - Kullanıcıdan drone port bilgisi alır
    - Tam bir mission döngüsü çalıştırır
    """
    swarmdiscovery = SwarmDiscovery()  # 20 metre yükseklik
    
    # 🔌 Kullanıcıdan bağlantı bilgisi al
    drone_port = input("Drone portu (udp://:14540): ") or "udp://:14540"
    
    # 🚀 Mission sırası
    await swarmdiscovery.connect(system_address=drone_port, port=50060)        # 1. Bağlan
    await swarmdiscovery.initialize_mission(target_altitude=15.0)  # 2. Mission başlat
    await swarmdiscovery.hold_mode(1.0, swarmdiscovery.home_position["yaw"])                     # 2. Kalk
    await swarmdiscovery.square_oscillation_by_cam_fov(
        distance1=30.0,  # 50 metre ileri
        distance2=30.0,     # 10 metre yan
        velocity= 1.0,         # 2 m/s hız
        camera_fov_horizontal=62,  # Pi Cam V2
        camera_fov_vertical=49,    # Pi Cam V2
        image_width=800,           # Önerilen çözünürlük
        image_height=600           # 4:3 oran
    )          # 3. Pattern uç
    await swarmdiscovery.end_mission()                            # 4. İn

if __name__ == "__main__":
    # 🎯 Ana çalıştırma noktası
    asyncio.run(test_swarm_discovery()) 