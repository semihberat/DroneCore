# Drone Core Libraries
import asyncio 
from mavsdk import System
# System Libraries
import sys
import os 
# Custom Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.connect import DroneConnection

async def test_connection():
    """
    Drone bağlantısını test eder
    """
    print("🚁 Drone Bağlantı Testi")
    print("=" * 30)
    
    # Kullanıcıdan bilgileri al
    print("\nDrone bilgilerini girin:")
    drone_id = input("Drone ID (1): ") or "1"
    drone_port = input("Drone portu (udp://:14540): ") or "udp://:14540"
    
    print(f"\n📡 Drone {drone_id} bağlanıyor...")
    
    try:
        # Drone'a bağlan
        drone = DroneConnection()
        await drone.connect(
            sysid=int(drone_id), 
            system_address=drone_port
        )
        
        print("✅ Bağlantı başarılı!")
        print("� 5 saniye telemetri verileri gösteriliyor...")
        
        # 5 saniye bekle
        await asyncio.sleep(5)
        
        print("✅ Test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("� PX4 simülasyonunu başlattınız mı?")

if __name__ == "__main__":
    print("Drone bağlantısını test ediyoruz...")
    asyncio.run(test_connection())