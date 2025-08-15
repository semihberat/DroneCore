import asyncio 
from mavsdk import System 
from services.xbee_service import XbeeService

class DroneStatus:
    """
    📊 Drone Durum Takip Sistemi
    - Real-time telemetri verilerini takip eder
    - GPS pozisyon, hız, yaw açısı gibi kritik verileri günceller
    - Tüm veriler self.current_* değişkenlerinde saklanır
    """
    def __init__(self):
        # 📍 Güncel telemetri verileri (sürekli güncellenir)
        self.current_position = None    # GPS koordinatları (lat, lon, alt)
        self.current_velocity = None    # Hız vektörleri (north, east, down)
        self.current_attitude = None    # Yaw/Pitch/Roll açıları
        self.status_text_task: asyncio.Task = None  # Sistem mesajları task'ı

    async def print_status_text(self, drone):
        """
        💬 Sistem Mesajlarını Takip Et
        - Drone'dan gelen hata/uyarı/bilgi mesajlarını gösterir
        - Arka planda sürekli çalışır
        """
        async for status_text in drone.telemetry.status_text():
            print(f"-- Status: {status_text.type}: {status_text.text}")

    async def update_position(self, drone):
        """
        📍 GPS Pozisyonunu Güncelle
        - Latitude, Longitude, Altitude değerlerini sürekli günceller
        - Navigasyon hesaplamalarında kullanılır
        """
        async for position in drone.telemetry.position():
            self.current_position = position
            print(f"-- Current Position: {self.current_position.latitude_deg}, {self.current_position.longitude_deg}, {self.current_position.absolute_altitude_m}")

    async def print_velocity(self, drone):
        """
        🏃 Hız Vektörlerini Takip Et
        - North/East/Down hız bileşenlerini gösterir
        - Hareket kontrolü için önemli
        """
        async for odom in drone.telemetry.position_velocity_ned():
            self.current_velocity = odom.velocity
            print(f"-- Velocity: {odom.velocity.north_m_s} {odom.velocity.east_m_s} {odom.velocity.down_m_s}")

    async def update_attitude(self, drone):
        """
        🧭 Drone Açılarını Takip Et (Kritik!)
        - Yaw: Pusula yönü (0° = Kuzey)
        - Pitch: Önden yukarı/aşağı eğim
        - Roll: Yanlardan yatış açısı
        """
        async for attitude in drone.telemetry.attitude_euler():
            self.current_attitude = attitude
            print(f"-- Attitude: Yaw={attitude.yaw_deg:.1f}°, Pitch={attitude.pitch_deg:.1f}°, Roll={attitude.roll_deg:.1f}°")

   
            