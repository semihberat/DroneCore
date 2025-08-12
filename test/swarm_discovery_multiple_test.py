import asyncio
import sys
import os
# 📂 Path ayarları - üst klasördeki modüllere erişim için
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.swarm_discovery import SwarmDiscovery

async def test_drone(drone_id: int, system_address: str, port: int, delay: float):
    """
    🚁 Tek Drone Test Fonksiyonu
    Args:
        drone_id: Drone kimlik numarası (1, 2, etc.)
        system_address: UDP adresi (udp://:14540, udp://:14541)
        port: MAVSDK port (50060, 50061)
        delay: Başlatma gecikmesi (saniye)
    """
    try:
        print(f"🚁 Drone {drone_id} başlatılıyor...")
        
        # Başlatma gecikmesi (drone'ların üst üste çakışmaması için)
        if delay > 0:
            print(f"⏱️ Drone {drone_id} - {delay} saniye bekleniyor...")
            await asyncio.sleep(delay)
        
        # SwarmDiscovery instance oluştur
        swarm_drone = SwarmDiscovery()
        
        print(f"📡 Drone {drone_id} bağlanıyor: {system_address}, Port: {port}")
        
        # 🚀 Mission sırası
        await swarm_drone.connect(system_address=system_address, port=port)  # 1. Bağlan
        await swarm_drone.initialize_mission(target_altitude=5.0)           # 2. Kalk (5m)

        # 1 saniye hold (stabilizasyon)
        await swarm_drone.hold_mode(1.0, swarm_drone.home_position["yaw"])
        
        # SwarmDiscovery pattern başlat
        await swarm_drone.square_oscillation_by_cam_fov(
            distance1=30.0,                    # 25 metre ileri hareket
            distance2=30.0,                    # 25 metre yan kapsama
            velocity=1.0,                      # 1.5 m/s hız
            camera_fov_horizontal=62,          # Pi Cam V2 FOV
            camera_fov_vertical=49,            # Pi Cam V2 FOV  
            image_width=800,                   # 800x600 çözünürlük
            image_height=600
        )

        # Mission bitir
        await swarm_drone.end_mission()

        
    except Exception as e:
        print(f"❌ Drone {drone_id} HATA: {e}")
        
async def test_swarm_discovery():

    # İki drone'u paralel olarak başlat
    tasks = [
        # Drone 1: Ana konum (0,0,0)
        test_drone(
            drone_id=1,
            system_address="udp://:14540", 
            port=50060,
            delay=0  # Hemen başla
        ),
    ]
    
    try:
        # İki drone'u paralel çalıştır
        await asyncio.gather(*tasks)
        
    except Exception as e:
        print(f"\n❌ GENEL HATA: {e}")

if __name__ == "__main__":

    asyncio.run(test_swarm_discovery())
    
    print("\n✅ Test tamamlandı!")
