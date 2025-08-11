

# 🚁 Drone Core - Otonom Drone Kontrol Sistemi

Bu proje, PX4/MAVSDK kullanarak drone'ları otonom olarak kontrol etmek için geliştirilmiş, tip güvenli ve matematiksel algoritmalara dayalı bir Python kütüphanesidir.

## 🎯 Ana Sistem Bileşenleri

### 📡 **OffboardControl** - Temel Kontrol Sistemi
Drone'un temel hareket fonksiyonlarını ve yükseklik kontrolünü sağlayan merkezi sistem.

#### 🚀 Matematiksel Modeller

**Yükseklik Kontrolü (PID-benzeri P Kontrolcü)**
```
altitude_error = target_altitude_abs - current_altitude
vertical_velocity = altitude_error × altitude_gain
vertical_velocity_ned = -clamp(vertical_velocity, ±max_speed)

Parametreler:
- altitude_gain = 0.8 (duyarlılık katsayısı)
- max_vertical_speed = 2.0 m/s (güvenlik sınırı)
```

**Hız Vektör Hesaplaması**
```
velocity_north = velocity × cos(yaw_radians)
velocity_east = velocity × sin(yaw_radians)
velocity_ned = [velocity_north, velocity_east, vertical_velocity_ned, yaw]
```

#### 🎮 Ana Fonksiyonlar

```python
# Tip güvenli fonksiyon imzaları
async def initialize_mission(self, target_altitude: float) -> bool
async def go_forward(self, velocity: float, yaw: float) -> None
async def go_forward_by_meter(self, forward_distance: float, velocity: float, yaw: float) -> None
async def hold_mode(self, hold_time: float, angle_deg_while_hold: float) -> None
```

**📏 go_forward_by_meter() - Mesafe Bazlı Navigasyon**
- **Hassasiyet**: 1 metre
- **Algoritma**: Real-time GPS mesafe hesaplama
- **Hız Kontrolü**: Hedefe yaklaştıkça otomatik yavaşlama
```python
# Kullanım örneği
await drone.go_forward_by_meter(
    forward_distance=20.0,  # 20 metre git
    velocity=3.0,           # 3 m/s hızla
    yaw=45.0               # 45° yönünde
)
```

**⏱️ hold_mode() - Pozisyon Sabitleme**
- **Amaç**: Belirtilen süre ve açıda sabit kalma
- **Kontrol Döngüsü**: 100ms güncellemelerle pozisyon korunması
```python
# 10 saniye 0° açıda dur
await drone.hold_mode(hold_time=10.0, angle_deg_while_hold=0.0)
```

### 🌐 **SwarmDiscovery** - Keşif Misyon Sistemi  
Arama-kurtarma ve keşif operasyonları için özelleştirilmiş pattern uçuş sistemi.

#### 🔄 Kare Dalga Oscillation Algoritması

**Matematiksel Pattern**
```
Pattern Sequence:
1. Forward: (x, y) → (x + forward_length, y)
2. Left Turn: yaw → yaw + 90°
3. Side Move: (x, y) → (x, y + side_length)  
4. Forward: (x, y) → (x + forward_length, y)
5. Right Turn: yaw → yaw - 90°
6. Side Move: (x, y) → (x, y - side_length)

Tekrar: N döngü (varsayılan: 10)
```

**Kamera FOV Hesaplama**
```
ground_coverage_width = 2 × altitude × tan(horizontal_fov/2)
ground_coverage_height = 2 × altitude × tan(vertical_fov/2)

Optimum yan mesafe = ground_coverage_width × overlap_factor
```

#### 🛸 Fonksiyon Kullanımı

```python
class SwarmDiscovery(OffboardControl):
    async def square_oscillation_by_cam_fov(
        self,
        distance1: float,                    # İleri mesafe (m)
        distance2: float,                    # Yan mesafe (m) 
        velocity: float,                     # Hız (m/s)
        camera_fov_horizontal: float,        # Kamera yatay FOV (derece)
        camera_fov_vertical: float,          # Kamera dikey FOV (derece)
        image_width: int,                    # Görüntü genişliği (pixel)
        image_height: int                    # Görüntü yüksekliği (pixel)
    ) -> None
```

**🎯 Kullanım Senaryosu**
```python
# Arama-kurtarma misyonu
await swarm_drone.square_oscillation_by_cam_fov(
    distance1=30.0,                     # 30m ileri git
    distance2=25.0,                     # 25m yan hareket
    velocity=2.0,                       # 2 m/s hız
    camera_fov_horizontal=62,           # Pi Camera V2 FOV
    camera_fov_vertical=49,
    image_width=800,                    # HD çözünürlük
    image_height=600
)
```

## 🔧 Teknik Özellikler

### 📊 **Tip Güvenli Sistem**
Tüm fonksiyonlar Python type hints ile güçlendirilmiş:
```python
# Eski (güvensiz) yaklaşım
async def connect(self, system_address="udp://:14540", port=50060):

# Yeni (tip güvenli) yaklaşım  
async def connect(self, system_address: str, port: int):
```

### 🎛️ **Default-Free Parametre Sistemi**
Tüm parametreler explicit olarak belirtilmeli:
```python
# ❌ Eski kullanım (default değerlerle)
await drone.initialize_mission()

# ✅ Yeni kullanım (explicit parametre)
await drone.initialize_mission(target_altitude=10.0)
```

### 📐 **GPS Hassasiyet Algoritmaları**

**Mesafe Hesaplama (GeographicLib)**
```python
def get_lat_lon_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple:
    """
    WGS84 ellipsoid üzerinde hassas mesafe hesaplama
    Returns: (north_distance, east_distance, total_distance)
    """
```

**Açı Hesaplama**
```python
bearing = atan2(east_distance, north_distance)
yaw_angle = degrees(bearing)  # Radyandan dereceye dönüşüm
```

## 🚀 Hızlı Başlangıç

### 1️⃣ **Temel OffboardControl Kullanımı**
```python
from models.offboard_control import OffboardControl

drone = OffboardControl()
await drone.connect(system_address="udp://:14540", port=50060)
await drone.initialize_mission(target_altitude=15.0)

# 20 metre kuzey yönünde git
await drone.go_forward_by_meter(
    forward_distance=20.0,
    velocity=3.0, 
    yaw=0.0  # Kuzey yönü
)

await drone.end_mission()
```

### 2️⃣ **SwarmDiscovery Keşif Misyonu**
```python
from missions.swarm_discovery import SwarmDiscovery

swarm = SwarmDiscovery()
await swarm.connect(system_address="udp://:14540", port=50060)
await swarm.initialize_mission(target_altitude=20.0)

# Kare dalga pattern (10 döngü)
await swarm.square_oscillation_by_cam_fov(
    distance1=50.0,      # 50m ileri
    distance2=30.0,      # 30m yan
    velocity=2.5,        # 2.5 m/s
    camera_fov_horizontal=62,
    camera_fov_vertical=49,
    image_width=1920,
    image_height=1080
)

await swarm.end_mission()
```

## 📈 **Performans Metrikleri**

| Özellik | Değer | Algoritma |
|---------|-------|-----------|
| Navigasyon Hassasiyeti | 1.0m | GPS mesafe hesaplama |
| Yükseklik Kontrolü | ±0.5m | P kontrolcü (gain=0.8) |
| Maksimum Dikey Hız | 2.0 m/s | Güvenlik sınırlaması |
| Kontrolcü Frekansı | 10 Hz | 100ms döngü periyodu |
| GPS Güncelleme | Real-time | GeographicLib WGS84 |

## 🧮 **Matematiksel Referanslar**

**NED Koordinat Sistemi**
- **North**: Pozitif kuzey yönü
- **East**: Pozitif doğu yönü  
- **Down**: Pozitif aşağı yönü (negatif = yukarı)

**Yaw Açı Dönüşümü**
```
yaw_ned = -yaw_aircraft  # Aircraft yaw'dan NED yaw'a
```

**Hız Vektör Bileşenleri**
```
v_north = |v| × cos(θ)
v_east = |v| × sin(θ)
```

Bu sistem, matematiksel doğruluk, tip güvenliği ve kod kalitesi prensipleriyle geliştirilmiş, profesyonel drone kontrol operasyonları için optimize edilmiştir. 🎯
