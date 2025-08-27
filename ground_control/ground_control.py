#!/usr/bin/env python3
"""
Ground Control Station - Harita Arayüzü
Bu uygulama drone operasyonları için harita görüntüleme ve konum işaretleme sağlar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import folium
import webbrowser
import os
import tempfile
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import threading
import time

class GroundControl:
    def __init__(self, root):
        self.root = root
        self.root.title("DroneCore - Ground Control Station")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Harita değişkenleri
        self.current_map = None
        self.markers = []
        self.map_file = None
        
        # UI bileşenlerini oluştur
        self.create_widgets()
        
        # Varsayılan harita oluştur
        self.create_default_map()
    
    def create_widgets(self):
        """Ana widget'ları oluştur"""
        # Ana frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = tk.Label(
            main_frame, 
            text="DRONECORE GROUND CONTROL STATION", 
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=(0, 20))
        
        # Kontrol paneli frame
        control_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Koordinat girişi
        coord_frame = tk.Frame(control_frame, bg='#34495e')
        coord_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Latitude
        tk.Label(coord_frame, text="Latitude:", bg='#34495e', fg='white').pack(side=tk.LEFT)
        self.lat_entry = tk.Entry(coord_frame, width=15)
        self.lat_entry.pack(side=tk.LEFT, padx=(5, 15))
        self.lat_entry.insert(0, "39.9334")  # İstanbul varsayılan
        
        # Longitude
        tk.Label(coord_frame, text="Longitude:", bg='#34495e', fg='white').pack(side=tk.LEFT)
        self.lon_entry = tk.Entry(coord_frame, width=15)
        self.lon_entry.pack(side=tk.LEFT, padx=(5, 15))
        self.lon_entry.insert(0, "32.8597")  # İstanbul varsayılan
        
        # Adres arama
        address_frame = tk.Frame(control_frame, bg='#34495e')
        address_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(address_frame, text="Adres Ara:", bg='#34495e', fg='white').pack(side=tk.LEFT)
        self.address_entry = tk.Entry(address_frame, width=30)
        self.address_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.address_entry.insert(0, "İstanbul, Türkiye")
        
        # Butonlar
        button_frame = tk.Frame(control_frame, bg='#34495e')
        button_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Harita oluştur butonu
        self.create_map_btn = tk.Button(
            button_frame,
            text="Harita Oluştur",
            command=self.create_map_from_coords,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            bd=2
        )
        self.create_map_btn.pack(side=tk.LEFT, padx=5)
        
        # Adres ara butonu
        self.search_address_btn = tk.Button(
            button_frame,
            text="Adres Ara",
            command=self.search_address,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            bd=2
        )
        self.search_address_btn.pack(side=tk.LEFT, padx=5)
        
        # Haritayı aç butonu
        self.open_map_btn = tk.Button(
            button_frame,
            text="Haritayı Aç",
            command=self.open_map,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            bd=2
        )
        self.open_map_btn.pack(side=tk.LEFT, padx=5)
        
        # Harita bilgileri frame
        info_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Harita durumu
        self.map_status_label = tk.Label(
            info_frame,
            text="Harita Durumu: Hazırlanıyor...",
            bg='#34495e',
            fg='white',
            font=('Arial', 12)
        )
        self.map_status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Koordinat bilgisi
        self.coord_info_label = tk.Label(
            info_frame,
            text="Koordinat: 39.9334, 32.8597 (İstanbul)",
            bg='#34495e',
            fg='white',
            font=('Arial', 12)
        )
        self.coord_info_label.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Harita önizleme frame
        map_preview_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        map_preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Harita önizleme başlığı
        preview_title = tk.Label(
            map_preview_frame,
            text="HARİTA ÖNİZLEME",
            bg='#34495e',
            fg='white',
            font=('Arial', 14, 'bold')
        )
        preview_title.pack(pady=10)
        
        # Harita önizleme alanı
        self.preview_text = tk.Text(
            map_preview_frame,
            height=20,
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Courier', 10),
            wrap=tk.WORD
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.preview_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.preview_text.yview)
    
    def create_default_map(self):
        """Varsayılan harita oluştur"""
        try:
            # İstanbul merkezi koordinatları
            lat, lon = 39.9334, 32.8597
            
            # Folium haritası oluştur
            self.current_map = folium.Map(
                location=[lat, lon],
                zoom_start=10,
                tiles='OpenStreetMap'
            )
            
            # Merkez işaretleyici ekle
            folium.Marker(
                [lat, lon],
                popup='İstanbul Merkez',
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(self.current_map)
            
            # Harita durumunu güncelle
            self.map_status_label.config(text="Harita Durumu: Hazır")
            self.coord_info_label.config(text=f"Koordinat: {lat}, {lon} (İstanbul)")
            
            # Önizleme metnini güncelle
            self.update_preview()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Varsayılan harita oluşturulamadı: {str(e)}")
    
    def create_map_from_coords(self):
        """Koordinatlardan harita oluştur"""
        try:
            # Koordinatları al
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            
            # Koordinat kontrolü
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                messagebox.showerror("Hata", "Geçersiz koordinatlar! Latitude: -90 ile 90, Longitude: -180 ile 180 arasında olmalı.")
                return
            
            # Yeni harita oluştur
            self.current_map = folium.Map(
                location=[lat, lon],
                zoom_start=12,
                tiles='OpenStreetMap'
            )
            
            # Merkez işaretleyici ekle
            folium.Marker(
                [lat, lon],
                popup=f'Konum: {lat}, {lon}',
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(self.current_map)
            
            # Harita durumunu güncelle
            self.map_status_label.config(text="Harita Durumu: Güncellendi")
            self.coord_info_label.config(text=f"Koordinat: {lat}, {lon}")
            
            # Önizleme metnini güncelle
            self.update_preview()
            
            messagebox.showinfo("Başarılı", f"Harita {lat}, {lon} koordinatları için oluşturuldu!")
            
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal koordinatlar girin!")
        except Exception as e:
            messagebox.showerror("Hata", f"Harita oluşturulamadı: {str(e)}")
    
    def search_address(self):
        """Adres arama fonksiyonu"""
        address = self.address_entry.get().strip()
        if not address:
            messagebox.showwarning("Uyarı", "Lütfen bir adres girin!")
            return
        
        # Durum güncelle
        self.map_status_label.config(text="Harita Durumu: Adres aranıyor...")
        self.root.update()
        
        # Arka planda adres arama
        def search_thread():
            try:
                geolocator = Nominatim(user_agent="dronecore_ground_control")
                location = geolocator.geocode(address)
                
                if location:
                    lat, lon = location.latitude, location.longitude
                    
                    # Ana thread'de UI güncelle
                    self.root.after(0, lambda: self.update_map_from_address(lat, lon, address))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Uyarı", "Adres bulunamadı!"))
                    self.root.after(0, lambda: self.map_status_label.config(text="Harita Durumu: Adres bulunamadı"))
                    
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", "Adres arama servisi kullanılamıyor!"))
                self.root.after(0, lambda: self.map_status_label.config(text="Harita Durumu: Servis hatası"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Adres arama hatası: {str(e)}"))
                self.root.after(0, lambda: self.map_status_label.config(text="Harita Durumu: Hata"))
        
        # Thread başlat
        threading.Thread(target=search_thread, daemon=True).start()
    
    def update_map_from_address(self, lat, lon, address):
        """Adres sonucundan haritayı güncelle"""
        try:
            # Koordinat girişlerini güncelle
            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, str(lat))
            
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, str(lon))
            
            # Yeni harita oluştur
            self.current_map = folium.Map(
                location=[lat, lon],
                zoom_start=15,
                tiles='OpenStreetMap'
            )
            
            # Merkez işaretleyici ekle
            folium.Marker(
                [lat, lon],
                popup=f'Adres: {address}',
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(self.current_map)
            
            # Harita durumunu güncelle
            self.map_status_label.config(text="Harita Durumu: Adres bulundu")
            self.coord_info_label.config(text=f"Koordinat: {lat}, {lon} - {address}")
            
            # Önizleme metnini güncelle
            self.update_preview()
            
            messagebox.showinfo("Başarılı", f"Adres bulundu: {address}\nKoordinatlar: {lat}, {lon}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Harita güncellenemedi: {str(e)}")
    
    def update_preview(self):
        """Harita önizleme metnini güncelle"""
        if self.current_map:
            # Harita HTML'ini al
            html_content = self.current_map._repr_html_()
            
            # Önizleme metnini temizle ve güncelle
            self.preview_text.delete(1.0, tk.END)
            
            # HTML içeriğini basitleştirilmiş şekilde göster
            preview_text = f"""
HARİTA BİLGİLERİ:
==================

Harita Türü: OpenStreetMap
Zoom Seviyesi: {self.current_map.options.get('zoom', 'N/A')}
Merkez Koordinatlar: {self.current_map.location if hasattr(self.current_map, 'location') else 'N/A'}

HTML İçeriği (İlk 500 karakter):
{html_content[:500]}...

Harita başarıyla oluşturuldu!
"Haritayı Aç" butonuna tıklayarak tarayıcıda görüntüleyebilirsiniz.
            """
            
            self.preview_text.insert(1.0, preview_text)
    
    def open_map(self):
        """Haritayı tarayıcıda aç"""
        if not self.current_map:
            messagebox.showwarning("Uyarı", "Önce bir harita oluşturun!")
            return
        
        try:
            # Geçici HTML dosyası oluştur
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                self.current_map.save(f.name)
                self.map_file = f.name
            
            # Tarayıcıda aç
            webbrowser.open(f'file://{self.map_file}')
            
            messagebox.showinfo("Başarılı", "Harita tarayıcıda açıldı!")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Harita açılamadı: {str(e)}")
    
    def cleanup(self):
        """Temizlik işlemleri"""
        if self.map_file and os.path.exists(self.map_file):
            try:
                os.unlink(self.map_file)
            except:
                pass

def main():
    """Ana fonksiyon"""
    try:
        # Gerekli kütüphaneleri kontrol et
        import folium
        import geopy
    except ImportError as e:
        print(f"Gerekli kütüphane eksik: {e}")
        print("Lütfen şu komutları çalıştırın:")
        print("pip install folium geopy")
        return
    
    # Ana pencere oluştur
    root = tk.Tk()
    app = GroundControl(root)
    
    # Pencere kapatıldığında temizlik yap
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Uygulamayı başlat
    root.mainloop()

if __name__ == "__main__":
    main()
