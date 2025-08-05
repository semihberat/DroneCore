# Drone Core - Autonomous Drone Control System

Bu proje, MAVSDK kullanarak otonom drone kontrolü sağlayan bir sistem içerir. Waypoint görevleri, çoklu waypoint misyonları ve drone navigasyonu için gerekli araçları sunar.

## 📁 Proje Yapısı

```
drone-core/
├── missions/
│   ├── waypoint_mission.py      # Tek waypoint görevi
│   └── multiple_waypoint_mission.py  # Çoklu waypoint görevi
├── models/
│   ├── connect.py               # Drone bağlantı modülü
│   ├── drone_status.py          # Drone durum takibi
│   ├── offboard_control.py      # Offboard kontrol temel sınıfı
│   └── xbee_communication.py    # XBee haberleşme
├── optimization/
│   ├── distance_calculation.py  # Mesafe ve açı hesaplamaları
│   ├── pid.py                   # PID kontrol
│   └── apf.py                   # Artificial Potential Field
├── test/
│   ├── multiple_waypoint_mission.py  # Çoklu waypoint test
│   ├── waypoint_mission_test_simple.py  # Basit waypoint test
│   └── connection_test.py       # Bağlantı testi
└── README.md
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