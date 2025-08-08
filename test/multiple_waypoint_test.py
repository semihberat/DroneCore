import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.multiple_waypoint_mission import MultipleWaypointMission

def get_user_inputs():
    print("🚁 Multiple Waypoint Mission Başlatılıyor...")
    print("=" * 50)
    
    sysid = input("System ID girin (varsayılan: 1): ").strip()
    sysid = int(sysid) if sysid else 1
    
    system_address = input("System address girin (varsayılan: udp://:14540): ").strip()
    system_address = system_address if system_address else "udp://:14540"
    
    port = input("Port girin (varsayılan: 50060): ").strip()
    port = int(port) if port else 50060
    
    print("\n📍 Waypoint Seçenekleri:")
    print("💡 Örnek waypoint'ler:")
    print("   1. 47.399061,8.542257,10,5,10")
    print("   2. 47.400129,8.547922,10,5,10")
    print("   3. 47.395815,8.545304,10,5,10")
    
    use_examples = input("\nÖrnek waypoint'leri kullanmak istiyor musunuz? (y/n): ").strip().lower()
    
    waypoints = []
    
    if use_examples in ['y', 'yes', 'evet', 'e']:
        waypoints = [
            (47.397840, 8.548052, 10, 15, 18),
            (47.397840, 8.550701371461741, 10, 15, 18),
            (47.395815, 8.545304, 10, 15, 18)
        ]
        print("✅ Örnek waypoint'ler yüklendi!")
        for i, wp in enumerate(waypoints, 1):
            print(f"   {i}. {wp[0]}, {wp[1]}, {wp[2]}m, {wp[3]}s, {wp[4]}s")
    else:
        print("\n📍 Manuel Waypoint Girişi:")
        print("Format: lat,lon,alt,hold_time,travel_time (örn: 47.397701,8.547730,10.0,3,10)")
        print("Waypoint girişini bitirmek için boş bırakın")
        
        waypoint_count = 1
        while True:
            waypoint_input = input(f"Waypoint {waypoint_count}: ").strip()
            if not waypoint_input:
                break
            try:
                parts = waypoint_input.split(',')
                if len(parts) == 5:
                    lat, lon, alt, hold_time, travel_time = map(float, parts)
                else:
                    raise ValueError("Geçersiz format")
                waypoints.append((lat, lon, alt, hold_time, travel_time))
                print(f"✅ Waypoint {waypoint_count} eklendi: ({lat}, {lon}, {alt}m, {hold_time}s, {travel_time}s)")
                waypoint_count += 1
            except ValueError:
                print("❌ Hatalı format! Format: lat,lon,alt,hold_time,travel_time (örn: 47.397701,8.547730,10.0,3,10)")
                continue
    
    if not waypoints:
        print("❌ Hiç waypoint girilmedi!")
        return None, None, None, None
    
    print(f"\n📋 Toplam {len(waypoints)} waypoint eklendi")
    print("🚀 Misyon başlatılıyor...")
    
    return sysid, system_address, port, waypoints

async def main():
    user_inputs = get_user_inputs()
    if user_inputs[0] is None:
        return
    
    sysid, system_address, port, waypoints = user_inputs
    
    print("\n" + "=" * 50)
    print("📋 MISYON ÖZETİ:")
    print(f"🔗 System ID: {sysid}")
    print(f"🔗 Address: {system_address}")
    print(f"� Port: {port}")
    print(f"�📍 Waypoint sayısı: {len(waypoints)}")
    for i, wp in enumerate(waypoints, 1):
        print(f"   {i}. {wp[0]}, {wp[1]}, {wp[2]}m, {wp[3]}s, {wp[4]}s")
    
    confirm = input("\nMisyonu başlatmak istiyor musunuz? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'evet', 'e']:
        print("Misyon iptal edildi.")
        return
    
    try:
        mission = MultipleWaypointMission()
        await mission.run_waypoint_mission(waypoints, system_address=system_address, port=port)
        print("🎉 Misyon başarıyla tamamlandı!")
    except Exception as e:
        import traceback
        print(f"❌ Misyon hatası: {e}")
        print("Hata detayları:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())