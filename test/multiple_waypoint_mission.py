import asyncio 
import sys 
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.multiple_waypoint_mission import MultipleWaypointMission

def get_user_inputs():
    """
    Kullanıcıdan interaktif olarak drone parametrelerini ve waypoint'leri alır.
    """
    print("🚁 Multiple Waypoint Mission Başlatılıyor...")
    print("=" * 50)
    
    # Drone parametreleri
    print("\n📡 Drone Bağlantı Ayarları:")
    sysid = input("System ID girin (varsayılan: 1): ").strip()
    sysid = int(sysid) if sysid else 1
    
    system_address = input("System address girin (varsayılan: udp://:14540): ").strip()
    system_address = system_address if system_address else "udp://:14540"
    
    # Waypoint seçenekleri
    print("\n📍 Waypoint Seçenekleri:")
    print("💡 Örnek waypoint'ler:")
    print("   1. 47.399061,8.542257,10,5")
    print("   2. 47.400129,8.547922,10,5") 
    print("   3. 47.395815,8.545304,10,5")
    
    use_examples = input("\nÖrnek waypoint'leri kullanmak istiyor musunuz? (y/n): ").strip().lower()
    
    waypoints = []
    
    if use_examples in ['y', 'yes', 'evet', 'e']:
        # Örnek waypoint'leri yükle
        waypoints = [
            (47.399061, 8.542257, 10, 5),
            (47.400129, 8.547922, 10, 5),
            (47.395815, 8.545304, 10, 5)
        ]
        print("✅ Örnek waypoint'ler yüklendi!")
        for i, wp in enumerate(waypoints, 1):
            print(f"   {i}. {wp[0]}, {wp[1]}, {wp[2]}m, {wp[3]}s")
    else:
        # Manuel waypoint girişi
        print("\n📍 Manuel Waypoint Girişi:")
        print("Format: lat,lon,alt,hold_time (örn: 47.397701,8.547730,10.0,3)")
        print("Waypoint girişini bitirmek için boş bırakın")
        
        waypoint_count = 1
        
        while True:
            waypoint_input = input(f"Waypoint {waypoint_count}: ").strip()
            if not waypoint_input:
                break
            try:
                parts = waypoint_input.split(',')
                if len(parts) >= 4:
                    lat, lon, alt, hold_time = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
                elif len(parts) == 3:
                    lat, lon, alt = float(parts[0]), float(parts[1]), float(parts[2])
                    hold_time = 5.0  # Varsayılan bekleme süresi
                else:
                    raise ValueError("Geçersiz format")
                    
                waypoints.append((lat, lon, alt, hold_time))
                print(f"✅ Waypoint {waypoint_count} eklendi: ({lat}, {lon}, {alt}m, {hold_time}s)")
                waypoint_count += 1
            except ValueError:
                print("❌ Hatalı format! Format: lat,lon,alt,hold_time (örn: 47.397701,8.547730,10.0,3)")
                continue
    
    if not waypoints:
        print("❌ Hiç waypoint girilmedi!")
        return None, None, None
    
    print(f"\n📋 Toplam {len(waypoints)} waypoint eklendi")
    print("🚀 Misyon başlatılıyor...")
    
    return sysid, system_address, waypoints

async def main():
    """
    Ana fonksiyon - kullanıcı girişlerini alır ve misyonu başlatır
    """
    # Kullanıcıdan girdileri al
    user_inputs = get_user_inputs()
    
    if user_inputs[0] is None:  # İptal edildi
        return
    
    sysid, system_address, waypoints = user_inputs
    
    # Onay al
    print("\n" + "=" * 50)
    print("📋 MISYON ÖZETİ:")
    print(f"🔗 System ID: {sysid}")
    print(f"🔗 Address: {system_address}")
    print(f"📍 Waypoint sayısı: {len(waypoints)}")
    for i, wp in enumerate(waypoints, 1):
        print(f"   {i}. {wp[0]}, {wp[1]}, {wp[2]}m, {wp[3]}s")
    
    confirm = input("\nMisyonu başlatmak istiyor musunuz? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'evet', 'e']:
        print("Misyon iptal edildi.")
        return
    
    # Misyonu çalıştır
    try:
        mission = MultipleWaypointMission()
        await mission.run_waypoint_mission(waypoints, sysid=sysid, system_address=system_address)
        print("🎉 Misyon başarıyla tamamlandı!")
    except Exception as e:
        print(f"❌ Misyon hatası: {e}")

if __name__ == "__main__":
    asyncio.run(main())