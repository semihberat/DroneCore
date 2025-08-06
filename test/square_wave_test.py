import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.square_wave_mission import SquareWaveMission

def get_user_inputs():
    print("🌊 Kare Dalga Misyonu Başlatılıyor...")
    print("=" * 50)
    
    sysid = input("System ID girin (varsayılan: 1): ").strip()
    sysid = int(sysid) if sysid else 1
    
    system_address = input("System address girin (varsayılan: udp://:14540): ").strip()
    system_address = system_address if system_address else "udp://:14540"
    
    port = input("Port girin (varsayılan: 50060): ").strip()
    port = int(port) if port else 50060
    
    print("\n🌊 Kare Dalga Parametreleri:")
    
    wave_length = input("Dalga boyu (metre, varsayılan: 80): ").strip()
    wave_length = int(wave_length) if wave_length else 80
    
    amplitude = input("Dalga genliği (metre, varsayılan: 20): ").strip()
    amplitude = int(amplitude) if amplitude else 20
    
    total_distance = input("Toplam mesafe (metre, varsayılan: 240): ").strip()
    total_distance = int(total_distance) if total_distance else 240
    
    step_size = input("Adım büyüklüğü (metre, varsayılan: 5): ").strip()
    step_size = int(step_size) if step_size else 5
    
    altitude = input("Uçuş yüksekliği (metre, varsayılan: 15): ").strip()
    altitude = int(altitude) if altitude else 15
    
    hold_time = input("Her noktada bekleme süresi (saniye, varsayılan: 0.5): ").strip()
    hold_time = float(hold_time) if hold_time else 0.5
    
    wave_count = total_distance / wave_length
    
    print(f"\n📋 Kare Dalga Misyon Özeti:")
    print(f"🔗 System ID: {sysid}")
    print(f"🔗 Address: {system_address}")
    print(f"🔗 Port: {port}")
    print(f"🌊 Dalga boyu: {wave_length}m")
    print(f"📏 Genlik: ±{amplitude}m (merkez çizgiden sapma)")
    print(f"➡️ Toplam mesafe: {total_distance}m")
    print(f"👣 Adım büyüklüğü: {step_size}m")
    print(f"🔄 Yaklaşık dalga sayısı: {wave_count:.1f}")
    print(f"📏 Yükseklik: {altitude}m")
    print(f"⏰ Bekleme süresi: {hold_time}s")
    print(f"\n💡 Pattern: ı_ı-ı_ı-ı_ı (merkez referanslı kare dalga)")
    
    return {
        'sysid': sysid,
        'system_address': system_address, 
        'port': port,
        'wave_length': wave_length,
        'amplitude': amplitude,
        'total_distance': total_distance,
        'step_size': step_size,
        'altitude': altitude,
        'hold_time': hold_time
    }

async def main():
    user_inputs = get_user_inputs()
    if user_inputs is None:
        return
    
    confirm = input("\nMisyonu başlatmak istiyor musunuz? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'evet', 'e']:
        print("Misyon iptal edildi.")
        return
    
    try:
        mission = SquareWaveMission()
        
        # Drone'a bağlan ve yaw açısını al
        await mission.connect(system_address=user_inputs['system_address'], port=user_inputs['port'])
        await mission.initialize_mission()
        
        # Şu anki konumu ve yaw açısını al
        await asyncio.sleep(2)  # Yaw açısının stabilleşmesi için bekle
        
        start_lat = mission.current_position.latitude_deg
        start_lon = mission.current_position.longitude_deg
        
        if mission.current_attitude is None:
            print("⚠️ Yaw açısı henüz alınamadı, varsayılan 0° kullanılıyor...")
            current_yaw = 0.0
        else:
            current_yaw = mission.current_attitude.yaw_deg
        
        print(f"🏠 Başlangıç noktası (merkez): {start_lat:.6f}, {start_lon:.6f}")
        print(f"🧭 Merkez çizgi yönü (yaw): {current_yaw:.1f}°")
        
        # Kare dalga waypoint'lerini hesapla
        waypoints = mission.calculate_square_wave_path(
            start_lat, start_lon, current_yaw,
            user_inputs['wave_length'], user_inputs['amplitude'],
            user_inputs['total_distance'], user_inputs['step_size']
        )
        
        print(f"\n🌊 {len(waypoints)} waypoint hesaplandı, misyon başlatılıyor...")
        
        # Misyonu çalıştır
        await mission.run_square_wave_mission(waypoints, user_inputs['system_address'], user_inputs['port'])
        
        print("🎉 Kare dalga misyonu başarıyla tamamlandı!")
        
    except Exception as e:
        import traceback
        print(f"❌ Misyon hatası: {e}")
        print("Hata detayları:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
