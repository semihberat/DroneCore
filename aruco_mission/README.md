# 🍓 ArUco DICT_4X4_50 3D Pozisyon Sistemi

Raspberry Pi üzerinde ArUco marker'larının 3D pozisyon ve oryantasyon tespiti için geliştirilmiş sistem.

## 📋 Özellikler

- ✅ **ArUco DICT_4X4_50** desteği (ID: 0-49)
- ✅ **3D Pozisyon tespiti** (X, Y, Z koordinatları)
- ✅ **3D Oryantasyon** (Roll, Pitch, Yaw açıları) 
- ✅ **Otomatik kamera kalibrasyonu**
- ✅ **Hedef marker filtreleme** (sadece istenen ID)
- ✅ **Gerçek zamanlı görüntü işleme**
- ✅ **libcamera entegrasyonu**

---

## 🛠️ **RASPBERRY PI KAMERA KURULUMU**

### 📌 **Raspberry Pi 4 ve Pi 3 için Detaylı Kurulum**

#### **1️⃣ Sistem Güncellemesi**
```bash
sudo apt update && sudo apt upgrade -y
```

#### **2️⃣ Kamera Modülünü Etkinleştirme**
```bash
# Raspberry Pi yapılandırması açın
sudo raspi-config

# Menüde:
# 3 Interface Options -> I1 Camera -> Yes -> Finish
# Sistemi yeniden başlatın
sudo reboot
```

#### **3️⃣ libcamera Kurulumu (Pi 4 için)**
```bash
# libcamera paketlerini kurun
sudo apt install -y libcamera-apps libcamera-dev

# Kamera testi
libcamera-hello --timeout 5000
```

#### **4️⃣ Eski Pi için raspistill Kurulumu (Pi 3 için)**
```bash
# Eski kamera araçları (Pi 3 ve öncesi için)
sudo apt install -y raspberrypi-kernel-headers

# Kamera testi
raspistill -o test.jpg -t 1000
```

#### **5️⃣ OpenCV Kurulumu**
```bash
# OpenCV ve gerekli paketleri kurun
sudo apt install -y python3-opencv python3-pip

# Python paketleri
pip3 install opencv-python opencv-contrib-python numpy
```

#### **6️⃣ Kamera Bağlantısı Kontrol**
```bash
# Kamera modülünün tanınıp tanınmadığını kontrol edin
vcgencmd get_camera

# Çıktı: supported=1 detected=1 (olmalı)

# libcamera ile test
libcamera-vid --list-cameras

# Kamera ile fotoğraf çekin
libcamera-still -o test_photo.jpg
```

#### **7️⃣ Kamera Çözünürlük ve FPS Ayarları**
```bash
# .bashrc dosyasına ekleyin (opsiyonel)
echo 'export LIBCAMERA_LOG_LEVELS=*:WARNING' >> ~/.bashrc
source ~/.bashrc
```

### ⚠️ **Yaygın Sorunlar ve Çözümler**

#### **Problem 1: "Camera is not enabled"**
```bash
# Çözüm:
sudo raspi-config
# 3 Interface Options -> I1 Camera -> Yes
sudo reboot
```

#### **Problem 2: "Permission denied" Hatası**
```bash
# Kullanıcıyı video grubuna ekleyin
sudo usermod -a -G video $USER
sudo reboot
```

#### **Problem 3: libcamera Komutları Çalışmıyor**
```bash
# Pi 4 için:
sudo apt install --reinstall libcamera-apps

# Pi 3 için (eski sistem):
sudo apt install --reinstall raspberrypi-kernel-headers
```

#### **Problem 4: "No cameras available"**
```bash
# Kamera kablolarını kontrol edin
# Kamerayı yeniden takın
# Sistemi yeniden başlatın
sudo reboot

# Kamera durumunu kontrol edin
dmesg | grep -i camera
```

#### **Problem 5: FPS Düşük veya Takılma**
```bash
# GPU memory'yi artırın
sudo nano /boot/config.txt

# Şu satırı ekleyin:
gpu_mem=128

# Sistemi yeniden başlatın
sudo reboot
```

### 🔧 **Performans Optimizasyonu**

#### **GPU Memory Ayarı**
```bash
sudo nano /boot/config.txt

# Şu satırları ekleyin:
gpu_mem=128
start_x=1
```

#### **Kamera Ayarları**
```bash
# /boot/config.txt dosyasına ekleyin:
camera_auto_detect=1
disable_camera_led=1  # LED'i kapatmak için (opsiyonel)
```

---

## 🚀 **SİSTEM KURULUMU**

### **1️⃣ Proje Kurulumu**
```bash
cd aruco_mission
```

### **2️⃣ Python Gereksinimleri**
```bash
pip3 install opencv-python opencv-contrib-python numpy
```

### **3️⃣ Dosya İzinleri**
```bash
chmod +x *.py
```

---

## 📖 **KULLANIM KILAVUZU**

### **1️⃣ Kamera Kalibrasyonu (İlk Kez - Zorunlu)**
```bash
python3 auto_camera_calibration.py
```

**Adımlar:**
1. ✅ `chessboard_9x6.png` dosyasını yazdırın
2. ✅ Düz bir yüzeye yapıştırın  
3. ✅ Enter'a basın
4. ✅ Satranç tahtasını **farklı açılardan** gösterin:
   - ↔️ Sola-sağa çevirin
   - ↕️ Yukarı-aşağı eğin
   - 🔄 45° döndürün
   - 📏 Yakın-uzak tutun
   - 🎯 Köşelere götürün
5. ✅ 20 fotoğraf otomatik çekilir
6. ✅ `camera_calibration.pkl` oluşur

### **2️⃣ ArUco 3D Tespit**
```bash
python3 realtime_camera_viewer.py
```

**Adımlar:**
1. ✅ Hedef marker ID girin (0-49 arası)
2. ✅ Oluşturulan marker'ı yazdırın
3. ✅ 5cm boyutunda kesin
4. ✅ Kameraya gösterin

---

## 🎯 **SİSTEM ÖZELLİKLERİ**

### **ArUco Ayarları**
- **Sözlük:** DICT_4X4_50
- **ID Aralığı:** 0-49
- **Marker Boyutu:** 5cm (varsayılan)

### **3D Bilgiler**
- **Pozisyon:** X, Y, Z (cm cinsinden)
- **Rotasyon:** Roll, Pitch, Yaw (derece)
- **Mesafe:** Kameradan marker'a
- **3D Eksenler:** Görsel olarak marker üzerinde

### **Filtre Sistemi**
- ✅ Sadece hedef ID tanınır
- ❌ Diğer marker'lar görmezden gelinir
- 🎯 Konsola detaylı bilgi yazdırılır

---

## 🎮 **KONTROLLER**

### **Kamera Penceresi**
- **ESC:** Çıkış
- **S:** Screenshot al
- **SPACE:** Marker görüntüsü kaydet

---

## 📁 **DOSYA YAPISI**

```
📁 aruco_mission/
├── 📄 auto_camera_calibration.py     # Kamera kalibrasyonu
├── 📄 realtime_camera_viewer.py      # ArUco 3D tespit
├── 📄 camera_calibration.pkl         # Kişisel kalibrasyon (otomatik)
├── 📄 chessboard_9x6.png            # Satranç tahtası (otomatik)
├── 📄 target_marker_id_X.png        # Hedef marker (otomatik)
├── 📁 calibration_images/           # Kalibrasyon fotoğrafları
└── 📄 README.md                     # Bu dosya
```

---

## 🔧 **SORUN GİDERME**

### **"Kamera başlatılamadı" Hatası**
```bash
# Kamera modülünü yeniden etkinleştirin
sudo raspi-config
# 3 Interface Options -> I1 Camera -> Yes
sudo reboot

# Kamera durumunu kontrol edin
vcgencmd get_camera
libcamera-vid --list-cameras
```

### **"Permission denied" Hatası**
```bash
# Kullanıcı izinlerini düzenleyin
sudo usermod -a -G video $USER
sudo reboot
```

### **"No cameras available" Hatası**
```bash
# Kamera kablolarını kontrol edin
# /boot/config.txt dosyasını kontrol edin
sudo nano /boot/config.txt

# Şu satırların olduğundan emin olun:
camera_auto_detect=1
start_x=1
gpu_mem=128
```

### **Düşük FPS veya Takılma**
```bash
# GPU memory'yi artırın
sudo nano /boot/config.txt
# gpu_mem=128 ekleyin

# Çözünürlüğü düşürün (koda bunu ekleyin):
pipe_path = self.start_camera_stream(width=320, height=240, fps=15)
```

### **"Marker tespit edilmiyor"**
- ✅ Marker'ı düz yüzeye yapıştırın
- ✅ İyi aydınlatma sağlayın  
- ✅ Marker boyutunu 5cm yapın
- ✅ Kameraya odaklanmasını bekleyin
- ✅ Hedef ID'yi doğru girin (0-49 arası)

---

## 📊 **BAŞARIM TAVSİYELERİ**

### **Kalibrasyon İçin**
- 🎯 **20+ farklı pozisyon** kullanın
- 🔄 **Satranç tahtasını döndürün**
- 📏 **Farklı mesafeler** deneyin
- 🎯 **Köşelere** götürün
- ⏱️ **Her pozisyonda 2 saniye** bekleyin

### **Tespit İçin**
- 🔆 **İyi aydınlatma** sağlayın
- 📐 **Düz yüzey** kullanın
- 📏 **5cm marker boyutu** kullanın
- 🎯 **Doğru hedef ID** seçin
- 📱 **Sabit tutun**

---

## 📞 **DESTEK**

### **Log Dosyaları**
```bash
# Sistem logları kontrol edin
dmesg | grep -i camera
journalctl -u libcamera

# ArUco sistemi debug için:
python3 realtime_camera_viewer.py > debug.log 2>&1
```

### **Test Komutları**
```bash
# Kamera testi
libcamera-hello --timeout 5000
libcamera-still -o test.jpg

# OpenCV testi
python3 -c "import cv2; print(cv2.__version__)"

# ArUco testi
python3 -c "import cv2; print('ArUco:', hasattr(cv2, 'aruco'))"
```

---

## 🎉 **BİTTİ!**

Bu kurulum rehberi ile Raspberry Pi'nizde ArUco 3D pozisyon sistemi çalışır durumda olacak. Herhangi bir sorunla karşılaştığınızda yukarıdaki sorun giderme bölümünü kontrol edin.

**İyi çalışmalar!** 🚀
