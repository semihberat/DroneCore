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

class DroneFunctionality:
    """
    🎮 Temel Drone Hareket Fonksiyonları
    - Hold mode (durma)
    - İleri gitme 
    - Mesafe tabanlı navigasyon
    """

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
            
    async def go_forward(self, altitude=10.0, velocity=3, yaw=None):
        """
        ➡️ Belirtilen Yönde İleri Git
        Args:
            altitude: Uçuş yüksekliği
            velocity: Hız (m/s)
            yaw: Hareket yönü (None ise home yaw kullanılır)
        """
        # 📐 Hız vektörünü north/east bileşenlerine ayır
        velocity_north_vector, velocity_east_vector = CalculateDistance.find_vectors(
            velocity, 
            yaw if yaw is not None else self.home_position["yaw"]
        )
        
        if yaw is not None:
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(
                    velocity_north_vector,  # Kuzey bileşeni
                    velocity_east_vector,   # Doğu bileşeni
                    0,                      # Yukarı/aşağı hız (0 = sabit yükseklik)
                    yaw                     # Yaw açısı
                )
            )
            
    async def go_forward_by_meter(self, forward_distance=20.0, altitude=10.0, velocity=2, yaw=0.0):
        """
        📏 Belirtilen Mesafe Kadar Git (GPS Tabanlı)
        - Real-time mesafe hesaplaması yapar
        - 1 metre hassasiyetle durur
        - Hedefe yaklaştıkça otomatik yavaşlar
        
        Args:
            forward_distance: Gidilecek mesafe (metre)
            altitude: Uçuş yüksekliği
            velocity: Maksimum hız (m/s)
            yaw: Hareket yönü (derece)
        """
        print(f"🎯 Hedef: {forward_distance}m, Yön: {yaw}°")
        
        # 📍 Başlangıç pozisyonunu kaydet (mesafe referansı için)
        start_lat = self.current_position.latitude_deg
        start_lon = self.current_position.longitude_deg
        
        yaw = yaw if yaw is not None else self.home_position["yaw"]
        
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
                
            # ➡️ Hedefe doğru hareket et
            await self.go_forward(altitude=altitude, velocity=current_velocity, yaw=yaw)
            await asyncio.sleep(0.1)  # Kontrol döngüsü


class OffboardControl(DroneConnection, DroneFunctionality):
    """
    🚁 Ana Offboard Kontrol Sınıfı
    - DroneConnection (bağlantı) + DroneFunctionality (hareket) birleşimi
    - Mission başlatma ve bitirme işlemleri
    - Home position yönetimi
    """
    def __init__(self):
        super().__init__()

    async def initialize_mission(self):
        """
        🚀 Mission Başlatma Süreci (Kritik Sıralama!)
        1️⃣ Arm (motorları çalıştır)
        2️⃣ Home position kaydet 
        3️⃣ Position setpoint ayarla (offboard için gerekli)
        4️⃣ Offboard mode başlat
        5️⃣ Kalkış doğrulaması yap
        """
        print("-- Arming...")
        await self.drone.action.arm()
        await asyncio.sleep(1)
        
        print("-- Setting initial setpoint")
        # 📍 Home pozisyonunu kaydet (tüm navigasyonun referans noktası)
        self.home_position = {
            "lat": self.current_position.latitude_deg,     # Başlangıç latitude
            "lon": self.current_position.longitude_deg,    # Başlangıç longitude  
            "alt": self.current_position.absolute_altitude_m,  # Başlangıç altitude
            "yaw": self.current_attitude.yaw_deg if self.current_attitude else 0.0  # Başlangıç yaw açısı
        }

        # ⚠️ Offboard mode başlamadan önce position setpoint ZORUNLU
        await self.drone.offboard.set_position_ned(
            PositionNedYaw(0.0, 0.0, -10.0, self.home_position["yaw"])  # 10m yukarı çık
        )

        print("-- Starting offboard mode")
        try:
            await self.drone.offboard.start()
        except OffboardError as e:
            print(f"Offboard start failed: {e}")
            return

        # 📊 Kalkış başarı kontrolü
        print("-- Kalkış kontrol ediliyor...")
        start_alt = self.current_position.absolute_altitude_m
        await asyncio.sleep(5)  # 5 saniye bekle (kalkışın tamamlanması için)
        current_alt = self.current_position.absolute_altitude_m
        
        if current_alt - start_alt > 8:  # En az 8 metre yükseldi mi?
            print(f"✅ Kalkış başarılı: {current_alt - start_alt:.1f}m yükseldi")
        else:
            print(f"⚠️ Kalkış eksik: Sadece {current_alt - start_alt:.1f}m yükseldi")
        await asyncio.sleep(1)  # Pozisyon stabilleşsin

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

