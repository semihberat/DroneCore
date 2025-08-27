# DroneCore Ground Control Station

Bu uygulama drone operasyonları için gelişmiş bir harita arayüzü sağlar.

## Özellikler

- **Harita Görüntüleme**: OpenStreetMap tabanlı interaktif haritalar
- **Koordinat Girişi**: Latitude ve Longitude değerleri ile konum belirleme
- **Adres Arama**: Adres yazarak otomatik koordinat bulma
- **Harita Önizleme**: Harita bilgilerini metin olarak görüntüleme
- **Tarayıcı Entegrasyonu**: Haritaları web tarayıcısında açma

## Kurulum

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:
```bash
python ground_control.py
```

## Kullanım

### Koordinat ile Harita Oluşturma
1. Latitude ve Longitude alanlarına koordinatları girin
2. "Harita Oluştur" butonuna tıklayın
3. Harita belirtilen konumda oluşturulacak

### Adres ile Arama
1. "Adres Ara" alanına istediğiniz adresi yazın
2. "Adres Ara" butonuna tıklayın
3. Sistem otomatik olarak koordinatları bulacak ve haritayı güncelleyecek

### Haritayı Görüntüleme
1. "Haritayı Aç" butonuna tıklayın
2. Harita varsayılan web tarayıcınızda açılacak
3. Haritada işaretleyiciler ile konumları görebilirsiniz

## Arayüz Bileşenleri

- **Kontrol Paneli**: Koordinat girişi ve adres arama
- **Durum Bilgisi**: Harita durumu ve koordinat bilgileri
- **Önizleme Alanı**: Harita detayları ve HTML içeriği
- **Butonlar**: Harita oluşturma, adres arama ve harita açma

## Teknik Detaylar

- **Harita Motoru**: Folium (Python için Leaflet.js wrapper)
- **Koordinat Sistemi**: WGS84 (GPS standardı)
- **Harita Kaynağı**: OpenStreetMap
- **Geocoding**: Nominatim servisi

## Notlar

- İnternet bağlantısı gereklidir (harita yükleme ve adres arama için)
- Koordinatlar WGS84 formatında olmalıdır
- Latitude: -90 ile 90 arasında
- Longitude: -180 ile 180 arasında

## Hata Giderme

Eğer kütüphane hatası alırsanız:
```bash
pip install --upgrade folium geopy
```

Eğer harita yüklenemiyorsa:
- İnternet bağlantınızı kontrol edin
- Firewall ayarlarınızı kontrol edin
- Tarayıcı cache'ini temizleyin
