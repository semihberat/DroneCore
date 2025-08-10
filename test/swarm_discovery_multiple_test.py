import asyncio
import sys
import os
# 📂 Path ayarları - üst klasördeki modüllere erişim için
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.swarm_discovery import SwarmDiscovery

async def test_drone(drone_id, system_address, port, delay=0):
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

        print(f"✅ Drone {drone_id} mission başladı!")
        
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
        
        print(f"🎯 Drone {drone_id} pattern tamamlandı!")
        
        # Mission bitir
        await swarm_drone.end_mission()
        print(f"🛬 Drone {drone_id} mission tamamlandı!")
        
    except Exception as e:
        print(f"❌ Drone {drone_id} HATA: {e}")
        
async def test_multiple_swarm_discovery():
    """
    🚁🚁 İki Drone'lu SwarmDiscovery Test
    
    Drone Konfigürasyonu:
    - Drone 1: udp://:14540, Port 50060 (0,0,0 konumunda)
    - Drone 2: udp://:14541, Port 50061 (0,15,0 konumunda)
    
    PX4 Başlatma Komutları:
    Terminal 1 (Drone 1 - ArUco World):
    PX4_HOME_LAT=41.0082 PX4_HOME_LON=28.9784 PX4_HOME_ALT=100.0 PX4_GZ_WORLD=aruco make px4_sitl gz_x500
    
    Terminal 2 (Drone 2 - ArUco World, 15m doğuda):
    PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_HOME_LAT=41.0082 PX4_HOME_LON=28.9784 PX4_HOME_ALT=100.0 PX4_GZ_WORLD=aruco PX4_GZ_MODEL_POSE="0,15,0,0,0,0" PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i 1
    
    ArUco Marker Features:
    🎯 Ground-level markers for camera detection
    📷 Pi Camera V2 FOV optimized for marker recognition
    🔍 Multiple marker IDs for navigation reference
    
    GPS Seçenekleri:
    İstanbul: LAT=41.0082 LON=28.9784 ALT=100.0
    Ankara: LAT=39.9334 LON=32.8597 ALT=850.0  
    Zurich: LAT=47.3977420 LON=8.5455940 ALT=488.0
    """
    
    print("🚁🚁 MULTIPLE SWARM DISCOVERY TEST BAŞLIYOR")
    print("=" * 60)
    print("📍 Drone 1: (0,0,0) konumu - udp://:14540 - Port: 50060")
    print("📍 Drone 2: (0,15,0) konumu - udp://:14541 - Port: 50061")
    print("=" * 60)
    
    # İki drone'u paralel olarak başlat
    tasks = [
        # Drone 1: Ana konum (0,0,0)
        test_drone(
            drone_id=1,
            system_address="udp://:14540", 
            port=50060,
            delay=0  # Hemen başla
        ),
        
        # Drone 2: 15m doğuda (0,15,0)
        test_drone(
            drone_id=2,
            system_address="udp://:14541",
            port=50061, 
            delay=2  # 2 saniye sonra başla
        )
    ]
    
    try:
        # İki drone'u paralel çalıştır
        await asyncio.gather(*tasks)
        
        print("\n🎉 TÜM DRONE'LAR BAŞARIYLA TAMAMLANDI!")
        
    except Exception as e:
        print(f"\n❌ GENEL HATA: {e}")

async def test_single_drone():
    """
    🚁 Tek Drone Test (Debug için)
    """
    print("🚁 TEK DRONE SWARM DISCOVERY TEST")
    print("=" * 40)
    
    await test_drone(
        drone_id=1,
        system_address="udp://:14540",
        port=50060,
        delay=0
    )

if __name__ == "__main__":
    print("🔄 SWARM DISCOVERY MULTIPLE DRONE TEST")
    print("=" * 50)
    
    # Kullanıcı seçimi
    choice = input("Test tipi seçin (1: Tek drone, 2: Çift drone): ").strip()
    
    if choice == "1":
        print("🚁 Tek drone testi başlatılıyor...")
        asyncio.run(test_single_drone())
    else:
        print("🚁🚁 Çift drone testi başlatılıyor...")
        asyncio.run(test_multiple_swarm_discovery())
    
    print("\n✅ Test tamamlandı!")
