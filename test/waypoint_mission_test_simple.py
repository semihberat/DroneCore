# Drone Core Libraries
import asyncio
# System Libraries
import sys
import os
# Custom Libraries - Path ayarı
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.waypoint_mission import WaypointMission

async def test_waypoint_mission():
    """
    Tek waypoint testi - Çok basit!
    """
    print("🚁 Tek Waypoint Testi")
    print("=" * 25)
    
    # Drone bilgileri
    print("\n✈️  Drone ayarları:")
    drone_id = input("Drone ID (1): ") or "1"
    drone_port = input("Drone portu (udp://:14540): ") or "udp://:14540"
    
    # Tek waypoint al
    print("\n📍 Tek waypoint gir:")
    print("Format: enlem,boylam,yükseklik,bekleme (örnek: 47.399,8.542,10,5)")
    waypoint = input("Waypoint: ") or "47.399076,8.542354,10,5"
    
    # Waypoint'i hazırla
    try:
        parts = waypoint.split(',')
        if len(parts) >= 4:
            lat, lon, alt, hold_time = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
        else:
            lat, lon, alt, hold_time = float(parts[0]), float(parts[1]), float(parts[2]), 5.0
        
        print(f"✅ Hedef: {lat}, {lon}, {alt}m - {hold_time}s bekle")
    except:
        print("❌ Hatalı format! Varsayılan kullanılıyor...")
        lat, lon, alt, hold_time = 47.399076, 8.542354, 10.0, 5.0
    
    try:
        # Mission başlat
        mission = WaypointMission()
        
        print("🔗 Bağlanıyor...")
        await mission.connect(sysid=int(drone_id), system_address=drone_port)
        
        print("🛫 Kalkıyor...")
        await mission.initialize_mission()
        
        print(f"📍 {lat}, {lon}, {alt}m hedefine gidiyor...")
        await mission.go_to_position(lat, lon, alt, hold_time)
        
        print("🛬 İniyor...")
        await mission.end_mission()
        print("✅ Tamamlandı! 🎉")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    print("🎮 Basit Tek Waypoint Testi")
    asyncio.run(test_waypoint_mission())
