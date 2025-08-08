import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from missions.waypoint_mission import WaypointMission
from geographiclib.geodesic import Geodesic

class SquareWaveMission(WaypointMission):
    def __init__(self):
        super().__init__()
    
    def calculate_square_wave_path(self, start_lat, start_lon, current_yaw_deg, wave_length, amplitude, total_distance, step_size):
        """
        Merkez çizgi referanslı kare dalga (square wave) path hesaplar
        
        Args:
            start_lat, start_lon: Başlangıç noktası (merkez çizgi üzerinde)
            current_yaw_deg: Drone'un mevcut yaw açısı (merkez çizgi yönü)
            wave_length: Dalga boyu (metre) - bir tam dalganın uzunluğu
            amplitude: Dalga genliği (metre) - merkez çizgiden maksimum sapma
            total_distance: Toplam mesafe (metre)
            step_size: Adım büyüklüğü (metre)
        
        Returns:
            list: Tüm waypoint'lerin listesi
        """
        geod = Geodesic.WGS84
        
        waypoints = []
        
        # Ana ilerleme yönü (merkez çizgi)
        main_bearing = current_yaw_deg
        # Yan salınım yönleri
        right_bearing = main_bearing + 90  # Sağ (pozitif)
        left_bearing = main_bearing - 90   # Sol (negatif)
        
        # İlk nokta (merkez çizgi üzerinde başlangıç)
        waypoints.append((start_lat, start_lon, "START-MERKEZ", main_bearing, 0))
        
        # Adım sayısını hesapla
        num_steps = int(total_distance / step_size)
        
        for i in range(1, num_steps + 1):
            # Merkez çizgi üzerindeki ilerleme pozisyonu
            forward_distance = i * step_size
            
            # Kare dalga fonksiyonu ile yan sapma hesapla
            # Bir dalga boyu içindeki pozisyon (0-1 arası)
            position_in_wave = (forward_distance % wave_length) / wave_length
            
            # Kare dalga: 0-0.5 arası +1, 0.5-1 arası -1
            if position_in_wave < 0.5:
                square_value = 1.0  # Pozitif yarım
            else:
                square_value = -1.0  # Negatif yarım
            
            # Yan sapma miktarı
            side_displacement = square_value * amplitude
            
            # Önce merkez çizgi üzerinde ilerle
            center_result = geod.Direct(start_lat, start_lon, main_bearing, forward_distance)
            center_lat, center_lon = center_result['lat2'], center_result['lon2']
            
            # Sonra yan tarafta sapma yap
            if side_displacement > 0:  # Pozitif = sağa
                side_bearing = right_bearing
                label = f"S{i}-SAĞ({side_displacement:.1f}m)"
            elif side_displacement < 0:  # Negatif = sola
                side_bearing = left_bearing
                side_displacement = abs(side_displacement)  # Mesafe her zaman pozitif
                label = f"S{i}-SOL({side_displacement:.1f}m)"
            else:  # Sıfır = merkez çizgi üzerinde
                side_bearing = main_bearing
                side_displacement = 0
                label = f"S{i}-MERKEZ"
            
            # Final pozisyon
            if side_displacement > 0:
                final_result = geod.Direct(center_lat, center_lon, side_bearing, side_displacement)
                final_lat, final_lon = final_result['lat2'], final_result['lon2']
            else:
                final_lat, final_lon = center_lat, center_lon
            
            waypoints.append((final_lat, final_lon, label, side_bearing, square_value))
        
        return waypoints
    
    async def run_square_wave_mission(self, waypoints, system_address="udp://:14540", port=50060):
        """
        Kare dalga misyonu çalıştır
        """
        await self.connect(system_address=system_address, port=port)
        await self.initialize_mission()
        
        print(f"� Kare dalga misyonu başlatılıyor ({len(waypoints)} waypoint)...")
        
        # Waypoint'leri sırayla ziyaret et (başlangıç hariç)
        for i, (lat, lon, label, bearing, square_val) in enumerate(waypoints[1:], 1):
            await self.go_to_position(lat, lon, 15, 0.5, 8)
        
        print("🎉 Kare dalga misyonu tamamlandı!")
        await self.drone.action.land()


