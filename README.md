# Drone Core - Autonomous Drone Control System

Bu proje, MAVSDK kullanarak otonom drone kontrolü sağlayan bir sistem içerir. Waypoint görevleri, çoklu waypoint misyonları, geometrik pattern uçuş görevleri ve dalga mekaniği tabanlı navigasyon sistemi sunar.

## 🌊 YENİ! Geometrik Pattern Missions

Bu sistem artık aşağıdaki geometrik uçuş pattern'lerini desteklemektedir:

### 🔥 **Triangle Mission (L-Şekli Pattern)**
- Drone'un mevcut yaw açısını baz alan L şekli çizme
- Başlangıç noktasından düz gidiş, sonra 90° dik dönüş
- Gerçek zamanlı telemetri ile yaw-based navigation

### 🔄 **Zigzag Mission (Art Arda L Pattern)**  
- Birden fazla L şeklini art arda çizme sistemi
- Sağ-sol alternatif yön değiştirme
- Configurable L sayısı, mesafe ve yön kontrolü

### 🌀 **Labyrinth Mission (Labirent Navigasyonu)**
- Ana koridor boyunca sağ-sol sapma pattern'i
- Merkez çizgi referanslı yan dallanma sistemi
- Her yan sapma sonrası ana koridora otomatik geri dönüş

### 📊 **Square Wave Mission (Kare Dalga Mekaniği)**
- Matematiksel kare dalga pattern'i: `y = A × square(2π × x / λ)`
- Merkez çizgi referanslı dijital sinyal benzeri hareket
- Dalga boyu, genlik, adım büyüklüğü kontrolü
- ı_ı-ı_ı-ı_ı şeklinde keskin geçişli pattern

### 🌊 **Sine Wave Mission (Sinüs Dalgası)**
- Matematiksel sinüs fonksiyonu ile sürekli dalga
- Merkez çizgiden yumuşak salınım hareketi  
- Continuous wave pattern çizme

## 📁 Proje Yapısı

```
drone-core/
├── missions/
│   ├── waypoint_mission.py      # Tek waypoint görevi (Hold Mode destekli)
│   ├── multiple_waypoint_mission.py  # Çoklu waypoint görevi
│   ├── triangle_mission.py      # 🆕 L-şekli pattern mission
│   ├── zigzag_mission.py        # 🆕 Zigzag pattern mission
│   ├── labyrinth_mission.py     # 🆕 Labirent navigasyon mission
│   ├── square_wave_mission.py   # 🆕 Kare dalga pattern mission
│   └── sine_wave_mission.py     # 🆕 Sinüs dalgası mission
├── models/
│   ├── connect.py               # Drone bağlantı modülü
│   ├── drone_status.py          # Drone durum takibi (YAW/PITCH/ROLL telemetri)
│   └── offboard_control.py      # Offboard kontrol temel sınıfı
├── optimization/
│   ├── distance_calculation.py  # Mesafe ve açı hesaplamaları
│   ├── pid.py                   # PID kontrol
│   └── apf.py                   # Artificial Potential Field
├── test/
│   ├── multiple_waypoint_test.py     # Çoklu waypoint test
│   ├── waypoint_mission_test_simple.py  # Basit waypoint test
│   ├── connection_test.py            # Bağlantı testi
│   └── square_wave_test.py           # 🆕 Kare dalga pattern test
├── test.py                      # 🆕 Coordinate calculation utilities
└── README.md
```

## 🌊 Geometrik Pattern Mission Detayları

### 🔥 Triangle Mission (L-Şekli Pattern)
```python
from missions.triangle_mission import TriangleMission

mission = TriangleMission()
await mission.run_l_shape_mission(
    distance=20,      # Her bacak uzunluğu (metre)
    turn_right=True   # Sağa dönüş (False: sola dönüş)
)
```
**Özellikler:**
- Drone'un mevcut yaw açısını referans alan L şekli
- Başlangıç yönünde düz gidiş, sonra 90° dik dönüş
- Real-time telemetry ile yaw-based navigation

### 🔄 Zigzag Mission (Art Arda L Pattern)
```python
from missions.zigzag_mission import ZigzagMission

mission = ZigzagMission()
await mission.run_zigzag_mission(
    l_count=3,           # Kaç L şekli çizilecek
    l_distance=15,       # Her L'nin bacak uzunluğu
    start_direction=True # İlk L'nin yönü (True: sağ, False: sol)
)
```
**Özellikler:**
- Birden fazla L şeklini art arda çizme
- Sağ-sol alternatif yön değiştirme sistemi
- Configurable L sayısı ve mesafe parametreleri

### 🌀 Labyrinth Mission (Labirent Navigasyonu)
```python
from missions.labyrinth_mission import LabyrinthMission

mission = LabyrinthMission()
await mission.run_labyrinth_mission(
    main_distance=50,    # Ana koridor uzunluğu
    branch_distance=15,  # Yan dalların uzunluğu
    branch_count=4       # Toplam yan dal sayısı
)
```
**Özellikler:**
- Ana koridor boyunca sağ-sol sapma pattern'i
- Merkez çizgi referanslı yan dallanma
- Her yan sapma sonrası ana koridora geri dönüş

### 📊 Square Wave Mission (Kare Dalga Mekaniği)
```python
from missions.square_wave_mission import SquareWaveMission

mission = SquareWaveMission()
waypoints = mission.calculate_square_wave_path(
    lat=current_lat, lon=current_lon, yaw=current_yaw,
    wave_length=80,      # Dalga boyu (metre)
    amplitude=20,        # Dalga genliği (metre)
    total_distance=240,  # Toplam mesafe
    step_size=5          # Adım büyüklüğü (metre)
)
await mission.run_square_wave_mission(waypoints)
```
**Özellikler:**
- Matematiksel kare dalga: `y = A × square(2π × x / λ)`
- Merkez çizgi referanslı dijital sinyal pattern
- Configurable dalga boyu, genlik ve çözünürlük

### 🌊 Sine Wave Mission (Sinüs Dalgası)
```python
from missions.sine_wave_mission import SineWaveMission

mission = SineWaveMission()
waypoints = mission.calculate_sine_wave_path(
    lat=current_lat, lon=current_lon, yaw=current_yaw,
    wave_length=60,      # Dalga boyu (metre)
    amplitude=15,        # Dalga genliği (metre)
    total_distance=180,  # Toplam mesafe
    step_size=3          # Adım büyüklüğü (metre)
)
await mission.run_sine_wave_mission(waypoints)
```
**Özellikler:**
- Matematiksel sinüs fonksiyonu ile sürekli dalga
- Yumuşak salınım hareketi pattern'i
- Continuous wave çizme sistemi

## 🔧 Coordinate Calculation Utilities (test.py)

```python
# Perpendicular waypoint hesaplama
new_lat, new_lon = calculate_perpendicular_waypoint(
    current_lat, current_lon, target_lat, target_lon, 
    distance=20, turn_right=True
)

# Yeni pozisyon hesaplama
new_lat, new_lon = calculate_new_position(
    lat, lon, bearing_deg, distance_m
)

# İki nokta arası açı hesaplama
angle = get_turn_angle(lat1, lon1, lat2, lon2)
```

## 🚁 Waypoint Mission Sistemi

### WaypointMission (missions/waypoint_mission.py)

**Temel Özellikler:**
- ✅ **Dinamik navigasyon**: Her waypoint için güncel konumdan hedefe mesafe hesabı
- ✅ **Hız kontrolü**: `target_speed` parametresi ile hız ayarı (maksimum 20 m/s güvenlik sınırı)
- ✅ **Akıllı yaklaşma**: Hedefe 1 metre yaklaştığında durma
- ✅ **Hold Mode**: Hedefe varış sonrası belirlenen süre boyunca pozisyonda kalma
- ✅ **Precision Navigation**: Nokta atışı hedefe varış sistemi
- ✅ **Home pozisyon kaydı**: Başlangıç konumunu referans olarak kullanma
- ✅ **Açı hesabı**: Güncel konumdan hedefe doğru dinamik açı hesaplaması

**Parametre Açıklamaları:**
```python
async def go_to_position(self, target_lat, target_lon, target_alt=10.0, hold_time=5.0, target_speed=5.0):
```
- `target_lat, target_lon`: Hedef GPS koordinatları
- `target_alt`: Hedef yükseklik (metre)
- `hold_time`: Hedefe ulaştıktan sonra bekleme süresi (saniye) - **YENİ!**
- `target_speed`: Hedefe gitme hızı (m/s, maksimum 20 m/s)

**Hold Mode Özellikleri:**
- 🎯 **Precision Hold**: Hedefe varış sonrası tam pozisyonda kalma
- ⏰ **Timer Control**: Hassas zamanlama ile hold süresi kontrolü  
- 🔄 **Position Stabilization**: Küçük sapmalar için otomatik düzeltme
- 🧭 **Angle Preservation**: Hold sırasında son açının korunması
- 🚁 **Offboard Maintenance**: Hold süresince sürekli kontrol sinyali

### MultipleWaypointMission (missions/multiple_waypoint_mission.py)

**Temel Özellikler:**
- ✅ **Sıralı waypoint gezimi**: Waypoint'ler arasında düzgün geçiş
- ✅ **5 parametreli tuple desteği**: (lat, lon, alt, hold_time, travel_time)
- ✅ **Dinamik hız kontrolü**: Her waypoint için farklı hız ayarı
- ✅ **Hold Mode Entegrasyonu**: Her waypoint'te belirlenen süre bekleme
- ✅ **Otomatik misyon yönetimi**: Bağlantı, kalkış, navigasyon ve iniş

**Waypoint Format:**
```python
waypoints = [
    (47.399061, 8.542257, 10, 5, 20),  # lat, lon, alt, hold_time, speed
    (47.400129, 8.547922, 10, 5, 40),  # 5 saniye hold + 40 m/s hız
    (47.395815, 8.545304, 10, 5, 60)   # Her waypoint'te hold mode aktif
]
```

## 🎯 Hold Mode Sistemi

**Hold Mode Nedir?**
Drone hedefe vardıktan sonra belirlenen süre boyunca o pozisyonda sabit kalır.

**Hold Mode Teknikleri:**
1. **Velocity Control Hold** (Basit):
   ```python
   VelocityNedYaw(0.0, 0.0, 0.0, angle_deg)  # Hız sıfırlama
   ```

2. **Position Control Hold** (Önerilen):
   ```python
   PositionNedYaw(target_north, target_east, target_down, angle_deg)
   ```

3. **Stabilization Hold** (En güvenli):
   - Sürekli pozisyon kontrol ve düzeltme
   - Rüzgar ve diğer etkilere karşı dirençli

**Hold Timer:**
```python
hold_start_time = asyncio.get_event_loop().time()
while (asyncio.get_event_loop().time() - hold_start_time) < hold_time:
    # Hold logic
```

## 🧪 Test Kullanımı

### 1. Çoklu Waypoint Testi
```bash
cd drone-core
python3 test/multiple_waypoint_mission.py
```

**Test Özellikleri:**
- **Etkileşimli kullanım**: System ID ve adres girişi
- **Örnek waypoint'ler**: Hazır test koordinatları
- **Manuel waypoint girişi**: Özel koordinat tanımlama
- **Misyon özeti**: Başlamadan önce kontrol

**Kullanım Adımları:**
1. System ID girin (varsayılan: 1)
2. System address girin (varsayılan: udp://:14540)
3. Örnek waypoint'leri kullanın veya manuel girin
4. Misyon özetini kontrol edin
5. Misyonu onaylayın

**Manuel Waypoint Format:**
```
Format: lat,lon,alt,hold_time,travel_time
Örnek: 47.397701,8.547730,10.0,3,10
```

### 2. Basit Waypoint Testi
```bash
cd drone-core
python3 test/waypoint_mission_test_simple.py
```

**Özellikler:**
- Tek waypoint testi
- Basit kullanım
- Hızlı test için ideal

### 3. Bağlantı Testi
```bash
cd drone-core
python3 test/connection_test.py
```

## 🔧 Sistem Gereksinimleri

```bash
# MAVSDK kurulumu
pip install mavsdk

# Geographiclib kurulumu (mesafe hesaplamaları için)
pip install geographiclib
```

## 📊 Hız ve Zaman Kontrolü

**Hız Hesaplaması:**
- `target_speed` parametresi direkt olarak drone hızını kontrol eder
- Güvenlik sınırı: 20 m/s maksimum
- Hedefe yakınken otomatik yavaşlama
- 1 metre altında hassas yaklaşma

**Örnek Hız Ayarları:**
- `target_speed=5.0`: Normal hız (5 m/s)
- `target_speed=10.0`: Hızlı hareket (10 m/s)
- `target_speed=2.0`: Yavaş hareket (2 m/s)

## 🚀 Başlangıç

1. **PX4 Simulator başlatın**
2. **Test dosyasını çalıştırın**
3. **Waypoint'leri tanımlayın**
4. **Misyonu başlatın**

## 🔍 Hata Ayıklama

**Yaygın Hatalar:**
- `COMMAND_DENIED`: Simulatör arm edilemiyor
- `too many values to unpack`: Waypoint parametresi uyumsuzluğu
- `Connection failed`: MAVSDK bağlantı problemi

**Çözümler:**
- Simulatörün doğru çalıştığından emin olun
- Waypoint formatını kontrol edin
- System address'i doğrulayın (udp://:14540)

## 📈 Güncellemeler

### 🆕 6 Ağustos 2025 - Hold Mode Implementation
- ✅ **Hold Mode Sistemi**: Hedefe varış sonrası pozisyon tutma
- ✅ **Precision Navigation**: Nokta atışı hedefe varış
- ✅ **Position Stabilization**: Hold sırasında stabilizasyon
- ✅ **Timer Control**: Hassas hold süresi kontrolü

### 📋 4 Ağustos 2025 - Waypoint System Updates  
- ✅ **Dinamik navigasyon** sistemi
- ✅ **5 parametreli waypoint** desteği
- ✅ **Test sistemi** güncellemeleri
- ✅ **Hata ayıklama** iyileştirmeleri

Detaylı güncellemeler `last_commit.txt` dosyasında takip edilmektedir.