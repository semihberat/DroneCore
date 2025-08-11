# Drone Core Libraries - Temel drone kütüphaneleri
import asyncio
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw, OffboardError)
# System Libraries - Sistem kütüphaneleri
import sys
import os
# Custom Libraries - Özel kütüphanelerimiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.connect import DroneConnection
from optimization.distance_calculation import CalculateDistance



class OffboardControl(DroneConnection):
    """
    🚁 Ana Offboard Kontrol Sınıfı
    - DroneConnection (bağlantı) + DroneFunctionality (hareket) birleşimi
    - Mission başlatma ve bitirme işlemleri
    - Home position yönetimi
    """
    def __init__(self):
        super().__init__()
        self.target_altitude: float = None

    async def initialize_mission(self, target_altitude: float):
        """
        🚀 Ultra Stabil Takeoff → Offboard Algoritması  
        Problem: PX4 takeoff sonrası offboard geçiş zorluğu
        Çözüm: Hold mode + çoklu deneme sistemi
        """
        self.target_altitude = target_altitude
        print("-- 1️⃣ Arming...")
        await self.drone.action.arm()
        await asyncio.sleep(2)
        
        print("-- 2️⃣ Home position kaydediliyor...")
        self.home_position = {
            "lat": self.current_position.latitude_deg,
            "lon": self.current_position.longitude_deg,
            "alt": self.current_position.absolute_altitude_m,
            "yaw": self.current_attitude.yaw_deg if self.current_attitude else 0.0
        }
        print(f"   Home: Alt={self.home_position['alt']:.1f}m, Yaw={self.home_position['yaw']:.1f}°")

        print(f"-- 3️⃣ Takeoff to {target_altitude}m...")
        await self.drone.action.set_takeoff_altitude(target_altitude)
        await self.drone.action.takeoff()
        
        print("-- 4️⃣ Takeoff tamamlanması bekleniyor...")
        # Takeoff tamamlanana kadar bekle
        for i in range(30):  # 30 saniye max
            current_alt = self.current_position.absolute_altitude_m
            altitude_diff = current_alt - self.home_position["alt"]
            
            if altitude_diff >= (target_altitude * 0.8):  # %80'ine ulaştı
                print(f"✅ Takeoff OK: {altitude_diff:.1f}m")
                break
            
            print(f"   Yükseliyor: {altitude_diff:.1f}m / {target_altitude}m")
            await asyncio.sleep(1)
        
        await asyncio.sleep(3)  # Stabilizasyon
        
        print("-- 5️⃣ HOLD mode - pozisyon sabitleme...")
        # KRITIK: Hold mode ile pozisyonu sabitle
        await self.drone.action.hold()
        await asyncio.sleep(2)
        
        print("-- 6️⃣ Offboard geçiş hazırlığı...")
        # Mevcut pozisyonu al
        current_alt = self.current_position.absolute_altitude_m
        current_yaw = self.current_attitude.yaw_deg if self.current_attitude else self.home_position["yaw"]
        altitude_diff = current_alt - self.home_position["alt"]
        
        print(f"   Mevcut: Alt={current_alt:.1f}m, Diff={altitude_diff:.1f}m, Yaw={current_yaw:.1f}°")
        
        # Offboard başlatma - 5 deneme
        success = False
        for attempt in range(5):
            print(f"   Offboard deneme {attempt + 1}/5...")
            
            # Position setpoint gönder
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(0.0, 0.0, -altitude_diff, current_yaw)
            )
            await asyncio.sleep(0.5)
            
            try:
                await self.drone.offboard.start()
                print("✅ Offboard mode başarılı!")
                success = True
                break
            except OffboardError as e:
                print(f"   Deneme {attempt + 1} fail: {e}")
                await asyncio.sleep(1)
        
        if not success:
            print("❌ Offboard geçiş başarısız!")
            return False
        
        await asyncio.sleep(2)
        print("🎮 Mission hazır - offboard aktif!")
        return True

    async def end_mission(self):
        """
        🛬 Mission Sonlandırma
        - Arka plan task'larını durdur
        - Offboard mode'u kapat
        - İniş yap
        """
        print("-- Ending mission...")
        await asyncio.sleep(1)
        
        # 🔌 Telemetri task'larını durdur
        self.status_text_task.cancel()
        self._position_task.cancel()
        self._velocity_task.cancel()
        
        print("-- Mission ended. Stopping offboard control.")
        try:
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error stopping offboard: {e}")
            
        # 🛬 İniş yap
        await self.drone.action.land()

    async def hold_mode(self, hold_time: float, angle_deg_while_hold: float):
        """
        🛑 Sabit Konumda Dur
        Args:
            hold_time: Durma süresi (saniye)
            angle_deg_while_hold: Durma sırasında korunacak yaw açısı
        """
        print(f"Hold modunda {hold_time} saniye bekleniyor...")
        hold_start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - hold_start_time) < hold_time:
            # 🎯 Hız sıfır ama yaw açısını koru
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, angle_deg_while_hold)
            )
            await asyncio.sleep(0.1)  # Kontrol döngüsü gecikmesi
            
    async def go_forward(self, velocity: float, yaw: float):
        """
        ➡️ Belirtilen Yönde İleri Git
        Args:
            velocity: Hız (m/s)
            yaw: Hareket yönü
        """
        # 📐 Hız vektörünü north/east bileşenlerine ayır
        velocity_north_vector, velocity_east_vector = CalculateDistance.find_vectors(
            velocity, 
            yaw
        )
        
        # 📏 Yükseklik kontrolü - hedef yükseklik ile güncel yükseklik farkı
        current_altitude = self.current_position.absolute_altitude_m
        target_altitude_abs = self.home_position["alt"] + self.target_altitude
        altitude_error = target_altitude_abs - current_altitude
        
        # 🎯 Yükseklik hız kontrolü (PID benzeri)
        max_vertical_speed = 2.0  # Maksimum dikey hız (m/s)
        altitude_gain = 0.8       # Yükseklik kazançı (duyarlılık)
        
        # Hata büyüklüğüne göre dikey hız hesapla
        vertical_velocity = altitude_error * altitude_gain
        
        # Hızı sınırla
        vertical_velocity = max(-max_vertical_speed, min(max_vertical_speed, vertical_velocity))
        
        # NED koordinat sisteminde: negatif = yukarı, pozitif = aşağı
        vertical_velocity_ned = -vertical_velocity
        
        await self.drone.offboard.set_velocity_ned(
            VelocityNedYaw(
                velocity_north_vector,  # Kuzey bileşeni
                velocity_east_vector,   # Doğu bileşeni
                vertical_velocity_ned,  # Yukarı/aşağı hız (yükseklik kontrolü)
                yaw                     # Yaw açısı
            )
        )
            
    async def go_forward_by_meter(self, forward_distance: float, velocity: float, yaw: float):
        """
        📏 Belirtilen Mesafe Kadar Git (GPS Tabanlı)
        - Real-time mesafe hesaplaması yapar
        - 1 metre hassasiyetle durur
        - Hedefe yaklaştıkça otomatik yavaşlar
        
        Args:
            forward_distance: Gidilecek mesafe (metre)
            velocity: Maksimum hız (m/s)
            yaw: Hareket yönü (derece)
        """
        print(f"🎯 Hedef: {forward_distance}m, Yön: {yaw}°")
        
        # 📍 Başlangıç pozisyonunu kaydet (mesafe referansı için)
        start_lat = self.current_position.latitude_deg
        start_lon = self.current_position.longitude_deg
        
        while True:
            # 📏 Başlangıçtan şu ana kadar gidilen mesafeyi hesapla
            current_distance = CalculateDistance.get_lat_lon_distance(
                start_lat, start_lon,                           # Başlangıç noktası
                self.current_position.latitude_deg,             # Güncel nokta
                self.current_position.longitude_deg
            )[2]  # [2] = toplam mesafe
            
            remaining_distance = forward_distance - current_distance
            print(f"📏 Gidilen: {current_distance:.1f}m, Kalan: {remaining_distance:.1f}m")
            
            # 🛑 Durma kriteri: 1 metre hassasiyet
            if remaining_distance <= 1.0:
                print("🛑 Hedefe ulaşıldı!")
                # Son pozisyonda tam dur
                await self.drone.offboard.set_velocity_ned(
                    VelocityNedYaw(0.0, 0.0, 0.0, yaw)
                )
                break
                
            # 🐌 Hız kontrolü: Hedefe yaklaştıkça yavaşla
            if remaining_distance <= velocity:
                current_velocity = velocity * (velocity*0.1)  # %30 hızına düş
                print("🐌 Yavaşlıyor...")
            else:
                current_velocity = velocity
                
            # ➡️ Hedefe doğru hareket et (yükseklik kontrolü dahil)
            await self.go_forward(velocity=current_velocity, yaw=yaw)
            await asyncio.sleep(0.1)  # Kontrol döngüsü

