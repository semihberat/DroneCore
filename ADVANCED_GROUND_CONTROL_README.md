# DroneCore Advanced Ground Control Station

[TkinterMapView](https://github.com/TomSchimansky/TkinterMapView.git) kütüphanesi kullanılarak geliştirilmiş profesyonel drone ground control uygulaması.

## 🚀 **Öne Çıkan Özellikler**

### **Harita Arayüzü**
- **Doğrudan Tkinter Entegrasyonu**: Harita doğrudan uygulama penceresi içinde görüntülenir
- **Çoklu Harita Türü**: OpenStreetMap, Google Maps, Google Satellite, Watercolor, Toner
- **Gerçek Zamanlı Güncelleme**: Harita değişiklikleri anında yansır
- **Zoom ve Pan**: Fare ile harita üzerinde gezinme

### **Koordinat Yönetimi**
- **Latitude/Longitude Girişi**: Hassas koordinat belirleme
- **Adres Arama**: Adres yazarak otomatik koordinat bulma
- **Koordinat Kopyalama**: Sağ tık ile koordinatları panoya kopyalama
- **Koordinat Doğrulama**: Geçerli koordinat aralığı kontrolü

### **Marker Sistemi**
- **Dinamik Marker Ekleme**: Harita merkezine veya tıklanan noktaya marker ekleme
- **Marker Renklendirme**: Farklı renklerle marker kategorilendirme
- **Marker Metinleri**: Her marker için açıklayıcı metin
- **Toplu Marker Yönetimi**: Tüm markerları tek tıkla temizleme

### **Path (Rota) Sistemi**
- **Marker Bazlı Path**: Markerlar arasında otomatik rota oluşturma
- **Path Özelleştirme**: Renk, kalınlık ve stil ayarları
- **Path Yönetimi**: Path ekleme, silme ve düzenleme

### **Mission Yönetimi**
- **Mission Kaydetme**: Tüm harita verilerini JSON formatında kaydetme
- **Mission Yükleme**: Kaydedilen missionları geri yükleme
- **Veri Dışa Aktarma**: Koordinat, marker ve path verilerini dışa aktarma

## 🛠️ **Kurulum**

### **Gereksinimler**
```bash
pip install -r requirements.txt
```

### **Çalıştırma**
```bash
python ground_control_advanced.py
```

## 📖 **Kullanım Kılavuzu**

### **Temel Harita Kontrolü**
1. **Koordinat Girişi**: Latitude ve Longitude alanlarına koordinatları girin
2. **Git Butonu**: "Git" butonuna tıklayarak haritayı o koordinatlara taşıyın
3. **Adres Arama**: "Adres Ara" alanına adres yazın ve "Adres Ara" butonuna tıklayın

### **Harita Türü Değiştirme**
- **Harita Türü** dropdown menüsünden istediğiniz harita türünü seçin:
  - `osm`: OpenStreetMap (varsayılan)
  - `google_normal`: Google Maps
  - `google_satellite`: Google Satellite
  - `watercolor`: Sanatsal su boyası stili
  - `toner`: Siyah-beyaz toner stili

### **Marker İşlemleri**
1. **Marker Ekleme**: "Marker Ekle" butonu ile harita merkezine marker ekleyin
2. **Sağ Tık Marker**: Harita üzerinde sağ tıklayarak "Buraya Marker Ekle" seçin
3. **Marker Temizleme**: "Markerları Temizle" butonu ile tüm markerları silin

### **Path (Rota) Oluşturma**
1. **Marker Ekleme**: En az 2 marker ekleyin
2. **Path Oluşturma**: "Path Oluştur" butonuna tıklayın
3. **Path Temizleme**: "Pathleri Temizle" butonu ile pathleri silin

### **Mission Yönetimi**
1. **Mission Kaydetme**: "Mission Kaydet" butonu ile mevcut durumu JSON dosyasına kaydedin
2. **Mission Yükleme**: "Mission Yükle" butonu ile kaydedilen missionı geri yükleyin

### **Fare Kontrolleri**
- **Sol Tık**: Koordinatları giriş alanlarına kopyalar
- **Sağ Tık**: Context menüsü açar (Marker ekleme, koordinat kopyalama)
- **Fare Tekerleği**: Zoom in/out
- **Fare Sürükleme**: Haritayı kaydırma

## 🔧 **Teknik Detaylar**

### **Kullanılan Kütüphaneler**
- **TkinterMapView**: Ana harita widget'ı
- **tkinter**: GUI framework
- **json**: Mission veri formatı
- **threading**: Asenkron adres arama

### **Harita Sunucuları**
- **OpenStreetMap**: `https://a.tile.openstreetmap.org/{z}/{x}/{y}.png`
- **Google Maps**: `https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga`
- **Google Satellite**: `https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga`
- **Watercolor**: `http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png`
- **Toner**: `http://a.tile.stamen.com/toner/{z}/{x}/{y}.png`

### **Veri Formatları**
- **Koordinat Sistemi**: WGS84 (GPS standardı)
- **Mission Formatı**: JSON
- **Marker Verileri**: Pozisyon, metin, renk
- **Path Verileri**: Pozisyon listesi, renk, kalınlık

## 📱 **Arayüz Bileşenleri**

### **Üst Kontrol Paneli**
- Koordinat giriş alanları
- Adres arama
- Harita türü seçimi
- Temel navigasyon butonları

### **Alt Kontrol Paneli**
- Marker işlemleri
- Path işlemleri
- Mission yönetimi

### **Harita Alanı**
- Interaktif harita widget'ı
- Zoom kontrolleri
- Fare etkileşimleri

### **Bilgi Paneli**
- Mevcut koordinatlar
- Zoom seviyesi
- Marker sayısı
- Harita türü bilgisi

## 🎯 **Drone Operasyonları İçin Kullanım**

### **Keşif Görevleri**
1. Hedef noktaları marker olarak işaretleyin
2. Keşif rotasını path olarak çizin
3. Mission'ı kaydedin ve drone'a gönderin

### **Surveillance Operasyonları**
1. Gözlem noktalarını belirleyin
2. Patrol rotalarını planlayın
3. Kritik alanları marker ile işaretleyin

### **Delivery Operasyonları**
1. Başlangıç ve hedef noktalarını işaretleyin
2. Optimal rota planlaması yapın
3. Güvenli iniş alanlarını belirleyin

## 🚨 **Hata Giderme**

### **Kütüphane Hataları**
```bash
pip install --upgrade tkintermapview
```

### **Harita Yükleme Sorunları**
- İnternet bağlantısını kontrol edin
- Firewall ayarlarını kontrol edin
- Harita sunucu erişimini test edin

### **Performans Sorunları**
- Zoom seviyesini düşürün
- Marker sayısını azaltın
- Harita türünü değiştirin

## 📝 **Örnek Kullanım Senaryoları**

### **Senaryo 1: Basit Keşif Görevi**
1. Haritayı açın ve hedef bölgeye gidin
2. Önemli noktaları marker olarak işaretleyin
3. Keşif rotasını path olarak çizin
4. Mission'ı kaydedin

### **Senaryo 2: Çoklu Harita Analizi**
1. OpenStreetMap ile genel görünüm alın
2. Google Satellite ile detaylı analiz yapın
3. Watercolor ile sanatsal görünüm elde edin
4. Farklı harita türlerinde aynı noktaları karşılaştırın

### **Senaryo 3: Mission Paylaşımı**
1. Detaylı bir mission planı oluşturun
2. Tüm verileri JSON formatında kaydedin
3. Dosyayı ekip üyeleriyle paylaşın
4. Diğer ekip üyeleri mission'ı yükleyin

## 🔮 **Gelecek Geliştirmeler**

- **3D Harita Desteği**: Yükseklik verileri ile 3D görünüm
- **Gerçek Zamanlı Drone Takibi**: Canlı drone pozisyonu
- **Weather Overlay**: Hava durumu verileri
- **Traffic Data**: Trafik bilgileri
- **Offline Harita Desteği**: İnternet olmadan harita kullanımı

## 📞 **Destek**

Herhangi bir sorun yaşarsanız:
1. Hata mesajlarını kontrol edin
2. Gerekli kütüphanelerin yüklü olduğundan emin olun
3. İnternet bağlantınızı test edin
4. GitHub repository'deki issues bölümünü kontrol edin

---

**DroneCore Advanced Ground Control Station** - Profesyonel drone operasyonları için geliştirilmiştir.
