#!/usr/bin/env python3
"""
DroneCore Advanced Ground Control Station - TkinterMapView ile XBee Bağlantısı
Bu uygulama drone operasyonları için gelişmiş harita arayüzü ve XBee iletişimi sağlar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
import json
import threading
import time
import serial
import serial.tools.list_ports

class AdvancedGroundControl:
    def __init__(self, root):
        self.root = root
        self.root.title("DroneCore - Advanced Ground Control Station")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Harita değişkenleri
        self.map_widget = None
        self.markers = []
        self.paths = []
        self.polygons = []
        self.mission_data = {}
        
        # XBee değişkenleri
        self.xbee_serial = None
        self.xbee_connected = False
        self.xbee_port = None
        self.xbee_baudrate = 9600
        
        # UI bileşenlerini oluştur
        self.create_widgets()
        
        # Varsayılan harita oluştur
        self.create_default_map()
        
        # Sağ tık menüsü komutları ekle
        self.setup_right_click_menu()
        
        # XBee port listesini güncelle
        self.update_port_list()
    
    def create_widgets(self):
        """Ana widget'ları oluştur"""
        # Ana frame
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = tk.Label(
            main_frame, 
            text="DRONECORE ADVANCED GROUND CONTROL STATION", 
            font=('Arial', 16, 'bold'),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        title_label.pack(pady=(0, 15))
        
        # Üst kontrol paneli
        top_control_frame = tk.Frame(main_frame, bg='#2d2d2d', relief=tk.RAISED, bd=2)
        top_control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Sol taraf - Koordinat girişi
        coord_frame = tk.Frame(top_control_frame, bg='#2d2d2d')
        coord_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Latitude
        tk.Label(coord_frame, text="Latitude:", bg='#2d2d2d', fg='white').pack(side=tk.LEFT)
        self.lat_entry = tk.Entry(coord_frame, width=12, bg='#3d3d3d', fg='white', insertbackground='white')
        self.lat_entry.pack(side=tk.LEFT, padx=(5, 15))
        self.lat_entry.insert(0, "39.9334")
        
        # Longitude
        tk.Label(coord_frame, text="Longitude:", bg='#2d2d2d', fg='white').pack(side=tk.LEFT)
        self.lon_entry = tk.Entry(coord_frame, width=12, bg='#3d3d3d', fg='white', insertbackground='white')
        self.lon_entry.pack(side=tk.LEFT, padx=(5, 15))
        self.lon_entry.insert(0, "32.8597")
        
        # Orta - Adres arama
        address_frame = tk.Frame(top_control_frame, bg='#2d2d2d')
        address_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(address_frame, text="Adres Ara:", bg='#2d2d2d', fg='white').pack(side=tk.LEFT)
        self.address_entry = tk.Entry(address_frame, width=25, bg='#3d3d3d', fg='white', insertbackground='white')
        self.address_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.address_entry.insert(0, "İstanbul, Türkiye")
        
        # Sağ taraf - Harita türü ve XBee
        right_frame = tk.Frame(top_control_frame, bg='#2d2d2d')
        right_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Harita türü seçimi
        tk.Label(right_frame, text="Harita:", bg='#2d2d2d', fg='white').pack(side=tk.LEFT)
        self.map_type_var = tk.StringVar(value="osm")
        map_type_combo = ttk.Combobox(
            right_frame, 
            textvariable=self.map_type_var,
            values=["osm", "google_normal", "google_satellite", "watercolor", "toner"],
            width=12,
            state="readonly"
        )
        map_type_combo.pack(side=tk.LEFT, padx=(5, 10))
        map_type_combo.bind('<<ComboboxSelected>>', self.change_map_type)
        
        # XBee bağlantı frame
        xbee_frame = tk.Frame(right_frame, bg='#2d2d2d')
        xbee_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        tk.Label(xbee_frame, text="XBee:", bg='#2d2d2d', fg='white').pack(side=tk.LEFT)
        
        # Port seçimi
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            xbee_frame,
            textvariable=self.port_var,
            width=10,
            state="readonly"
        )
        self.port_combo.pack(side=tk.LEFT, padx=(5, 5))
        
        # Refresh butonu
        self.refresh_btn = tk.Button(
            xbee_frame,
            text="🔄",
            command=self.refresh_port_list,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.RAISED,
            bd=2,
            width=3
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Bağlan/Bağlantıyı Kes butonu
        self.connect_btn = tk.Button(
            xbee_frame,
            text="Bağlan",
            command=self.toggle_xbee_connection,
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.RAISED,
            bd=2
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Alt kontrol paneli
        bottom_control_frame = tk.Frame(main_frame, bg='#2d2d2d', relief=tk.RAISED, bd=2)
        bottom_control_frame.pack(fill=tk.X, pady=(0, 15))
        

        
        # Orta - XBee durumu
        xbee_status_frame = tk.Frame(bottom_control_frame, bg='#2d2d2d')
        xbee_status_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(xbee_status_frame, text="XBee Durumu:", bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        self.xbee_status_label = tk.Label(
            xbee_status_frame,
            text="Bağlantı Yok",
            bg='#e74c3c',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.SUNKEN,
            bd=1
        )
        self.xbee_status_label.pack(side=tk.LEFT, padx=10)
        
        # Sağ taraf - XBee veri gönderme
        xbee_data_frame = tk.Frame(bottom_control_frame, bg='#2d2d2d')
        xbee_data_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        tk.Label(xbee_data_frame, text="Veri Gönder:", bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        self.data_entry = tk.Entry(xbee_data_frame, width=20, bg='#3d3d3d', fg='white', insertbackground='white')
        self.data_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.data_entry.insert(0, "TEST")
        
        self.send_data_btn = tk.Button(
            xbee_data_frame,
            text="Gönder",
            command=self.send_xbee_data,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.RAISED,
            bd=2
        )
        self.send_data_btn.pack(side=tk.LEFT, padx=5)
        
        # Harita widget'ı
        map_frame = tk.Frame(main_frame, bg='#2d2d2d', relief=tk.RAISED, bd=2)
        map_frame.pack(fill=tk.BOTH, expand=True)
        
        # Harita başlığı
        map_title = tk.Label(
            map_frame,
            text="INTERAKTİF HARİTA",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 12, 'bold')
        )
        map_title.pack(pady=5)
        
        # Harita widget'ı burada oluşturulacak
        self.map_container = tk.Frame(map_frame, bg='#2d2d2d')
        self.map_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Alt bilgi paneli
        info_frame = tk.Frame(main_frame, bg='#2d2d2d', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Koordinat bilgisi
        self.coord_info_label = tk.Label(
            info_frame,
            text="Koordinat: 39.9334, 32.8597 (İstanbul) | Zoom: 10 | XBee: Bağlantı Yok",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 10)
        )
        self.coord_info_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Harita türü bilgisi
        self.map_info_label = tk.Label(
            info_frame,
            text="Harita Türü: OpenStreetMap",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 10)
        )
        self.map_info_label.pack(side=tk.RIGHT, padx=20, pady=10)
    
    def update_port_list(self):
        """Mevcut port listesini güncelle"""
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            self.port_combo['values'] = ports
            if ports:
                self.port_combo.set(ports[0])
        except Exception as e:
            print(f"Port listesi güncellenemedi: {str(e)}")
    
    def refresh_port_list(self):
        """Port listesini yenile"""
        try:
            # Mevcut seçili portu kaydet
            current_port = self.port_var.get()
            
            # Port listesini güncelle
            self.update_port_list()
            
            # Eğer önceki port hala mevcutsa seç
            available_ports = self.port_combo['values']
            if current_port in available_ports:
                self.port_var.set(current_port)
            elif available_ports:
                self.port_var.set(available_ports[0])
            
            # Başarı mesajı göster
            port_count = len(available_ports)
            if port_count > 0:
                messagebox.showinfo("Port Listesi Güncellendi", f"{port_count} port bulundu:\n" + "\n".join(available_ports))
            else:
                messagebox.showwarning("Port Bulunamadı", "Hiç USB port bulunamadı!")
                
        except Exception as e:
            messagebox.showerror("Hata", f"Port listesi yenilenemedi: {str(e)}")
    
    def toggle_xbee_connection(self):
        """XBee bağlantısını aç/kapat"""
        if not self.xbee_connected:
            self.connect_xbee()
        else:
            self.disconnect_xbee()
    
    def connect_xbee(self):
        """XBee'e bağlan"""
        try:
            port = self.port_var.get()
            if not port:
                messagebox.showwarning("Uyarı", "Lütfen bir port seçin!")
                return
            
            # Serial bağlantısı aç
            self.xbee_serial = serial.Serial(
                port=port,
                baudrate=self.xbee_baudrate,
                timeout=1
            )
            
            self.xbee_connected = True
            self.xbee_port = port
            
            # UI güncelle
            self.connect_btn.config(text="Bağlantıyı Kes", bg='#e74c3c')
            self.xbee_status_label.config(text="Bağlı", bg='#27ae60')
            self.port_combo.config(state="disabled")
            
            # Bilgi etiketini güncelle
            self.update_info_labels()
            
            messagebox.showinfo("Başarılı", f"XBee bağlantısı kuruldu: {port}")
            
            # XBee dinleme thread'ini başlat
            self.start_xbee_listener()
            
        except Exception as e:
            messagebox.showerror("Hata", f"XBee bağlantısı kurulamadı: {str(e)}")
    
    def disconnect_xbee(self):
        """XBee bağlantısını kes"""
        try:
            if self.xbee_serial:
                self.xbee_serial.close()
                self.xbee_serial = None
            
            self.xbee_connected = False
            self.xbee_port = None
            
            # UI güncelle
            self.connect_btn.config(text="Bağlan", bg='#27ae60')
            self.xbee_status_label.config(text="Bağlantı Yok", bg='#e74c3c')
            self.port_combo.config(state="readonly")
            
            # Bilgi etiketini güncelle
            self.update_info_labels()
            
            messagebox.showinfo("Başarılı", "XBee bağlantısı kesildi!")
            
        except Exception as e:
            messagebox.showerror("Hata", f"XBee bağlantısı kesilemedi: {str(e)}")
    
    def start_xbee_listener(self):
        """XBee veri dinleme thread'ini başlat"""
        def listen_thread():
            while self.xbee_connected and self.xbee_serial:
                try:
                    if self.xbee_serial.in_waiting > 0:
                        data = self.xbee_serial.readline().decode('utf-8').strip()
                        if data:
                            # Ana thread'de veriyi işle
                            self.root.after(0, lambda: self.process_xbee_data(data))
                except Exception as e:
                    print(f"XBee dinleme hatası: {str(e)}")
                    break
                time.sleep(0.1)
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def process_xbee_data(self, data):
        """XBee'den gelen veriyi işle"""
        try:
            print(f"XBee'den gelen veri: {data}")
            
            # JSON formatında koordinat verisi geliyorsa işle
            if data.startswith('{') and data.endswith('}'):
                try:
                    json_data = json.loads(data)
                    if 'lat' in json_data and 'lon' in json_data:
                        lat = json_data['lat']
                        lon = json_data['lon']
                        
                        # Koordinat girişlerini güncelle
                        self.lat_entry.delete(0, tk.END)
                        self.lat_entry.insert(0, str(lat))
                        
                        self.lon_entry.delete(0, tk.END)
                        self.lon_entry.insert(0, str(lon))
                        
                        # Haritayı güncelle
                        self.map_widget.set_position(lat, lon)
                        self.map_widget.set_zoom(15)
                        
                        # Bilgi etiketlerini güncelle
                        self.update_info_labels()
                        
                        messagebox.showinfo("XBee Veri", f"Drone koordinatları güncellendi: {lat}, {lon}")
                        
                except json.JSONDecodeError:
                    print("Geçersiz JSON formatı")
            
        except Exception as e:
            print(f"XBee veri işleme hatası: {str(e)}")
    
    def send_xbee_data(self):
        """XBee'e veri gönder"""
        if not self.xbee_connected:
            messagebox.showwarning("Uyarı", "Önce XBee'e bağlanın!")
            return
        
        try:
            data = self.data_entry.get().strip()
            if not data:
                messagebox.showwarning("Uyarı", "Lütfen gönderilecek veriyi girin!")
                return
            
            # Veriyi gönder
            self.xbee_serial.write(f"{data}\n".encode('utf-8'))
            
            messagebox.showinfo("Başarılı", f"Veri gönderildi: {data}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Veri gönderilemedi: {str(e)}")
    
    def create_default_map(self):
        """Varsayılan harita oluştur"""
        try:
            # İstanbul merkezi koordinatları
            lat, lon = 39.9334, 32.8597
            
            # TkinterMapView widget'ı oluştur
            self.map_widget = tkintermapview.TkinterMapView(
                self.map_container,
                width=1200,
                height=600,
                corner_radius=0
            )
            self.map_widget.pack(fill=tk.BOTH, expand=True)
            
            # Harita pozisyonunu ayarla
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(10)
            
            # Merkez işaretleyici ekle
            center_marker = self.map_widget.set_marker(
                lat, lon, 
                text="İstanbul Merkez",
                marker_color_circle="red",
                marker_color_outside="darkred"
            )
            self.markers.append(center_marker)
            
            # Bilgi etiketlerini güncelle
            self.update_info_labels()
            
            # Harita tıklama olaylarını ekle
            self.map_widget.add_left_click_map_command(self.on_map_left_click)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Harita oluşturulamadı: {str(e)}")
    
    def setup_right_click_menu(self):
        """Sağ tık menüsü komutlarını ayarla"""
        if self.map_widget:
            self.map_widget.add_right_click_menu_command(
                label="Koordinatları Kopyala",
                command=self.copy_coordinates,
                pass_coords=True
            )
    
    def change_map_type(self, event=None):
        """Harita türünü değiştir"""
        if not self.map_widget:
            return
            
        map_type = self.map_type_var.get()
        
        try:
            if map_type == "osm":
                self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
                self.map_info_label.config(text="Harita Türü: OpenStreetMap")
            elif map_type == "google_normal":
                self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
                self.map_info_label.config(text="Harita Türü: Google Maps")
            elif map_type == "google_satellite":
                self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
                self.map_info_label.config(text="Harita Türü: Google Satellite")
            elif map_type == "watercolor":
                self.map_widget.set_tile_server("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png")
                self.map_info_label.config(text="Harita Türü: Watercolor")
            elif map_type == "toner":
                self.map_widget.set_tile_server("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png")
                self.map_info_label.config(text="Harita Türü: Toner")
                
        except Exception as e:
            messagebox.showerror("Hata", f"Harita türü değiştirilemedi: {str(e)}")
    
    def copy_coordinates(self, coords):
        """Koordinatları panoya kopyala"""
        try:
            lat, lon = coords
            coord_text = f"{lat}, {lon}"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(coord_text)
            
            messagebox.showinfo("Başarılı", f"Koordinatlar panoya kopyalandı: {coord_text}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Koordinatlar kopyalanamadı: {str(e)}")
    
    def on_map_left_click(self, coords):
        """Harita sol tık olayı"""
        try:
            lat, lon = coords
            
            # Koordinat girişlerini güncelle
            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, str(lat))
            
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, str(lon))
            
            # Bilgi etiketlerini güncelle
            self.update_info_labels()
            
        except Exception as e:
            print(f"Sol tık olayı hatası: {str(e)}")
    
    def update_info_labels(self):
        """Bilgi etiketlerini güncelle"""
        try:
            if self.map_widget:
                # Mevcut pozisyonu al
                current_pos = self.map_widget.get_position()
                current_zoom = getattr(self.map_widget, 'zoom', 10)
                
                # XBee durumu
                xbee_status = "Bağlı" if self.xbee_connected else "Bağlantı Yok"
                
                if current_pos:
                    lat, lon = current_pos
                    self.coord_info_label.config(
                        text=f"Koordinat: {lat:.6f}, {lon:.6f} | Zoom: {current_zoom} | XBee: {xbee_status}"
                    )
                else:
                    self.coord_info_label.config(
                        text=f"Koordinat: N/A | Zoom: {current_zoom} | XBee: {xbee_status}"
                    )
                    
        except Exception as e:
            print(f"Bilgi etiketi güncelleme hatası: {str(e)}")

def main():
    """Ana fonksiyon"""
    try:
        # Gerekli kütüphaneleri kontrol et
        import tkintermapview
        import serial
    except ImportError as e:
        print(f"Gerekli kütüphane eksik: {e}")
        print("Lütfen şu komutları çalıştırın:")
        print("pip install tkintermapview pyserial")
        return
    
    # Ana pencere oluştur
    root = tk.Tk()
    app = AdvancedGroundControl(root)
    
    # Uygulamayı başlat
    root.mainloop()

if __name__ == "__main__":
    main()
