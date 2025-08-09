import math
import cv2
import numpy as np

class DroneVisionCalculator:
    """
    📷 Drone Kamera Görüş Alanı Hesaplayıcısı
    - Drone yüksekliğine göre kameranın kaç m² alan gördüğünü hesaplar
    - FOV (Field of View) ve çözünürlük bilgilerine göre hesaplama yapar
    - Gerçek dünya koordinatlarını piksel koordinatlarına dönüştürür
    """
    
    def __init__(self, camera_fov_horizontal=90, camera_fov_vertical=60, 
                 image_width=1920, image_height=1080):
        """
        🎥 Kamera Özellikleri
        Args:
            camera_fov_horizontal: Yatay FOV açısı (derece) - varsayılan 90°
            camera_fov_vertical: Dikey FOV açısı (derece) - varsayılan 60°
            image_width: Görüntü genişliği (piksel) - varsayılan 1920px
            image_height: Görüntü yüksekliği (piksel) - varsayılan 1080px
        """
        self.fov_h = math.radians(camera_fov_horizontal)  # Radyana çevir
        self.fov_v = math.radians(camera_fov_vertical)    # Radyana çevir
        self.image_width = image_width
        self.image_height = image_height
        
        print(f"📷 Kamera Özellikleri:")
        print(f"   FOV Yatay: {camera_fov_horizontal}° ({self.fov_h:.3f} rad)")
        print(f"   FOV Dikey: {camera_fov_vertical}° ({self.fov_v:.3f} rad)")
        print(f"   Çözünürlük: {image_width}x{image_height}")
        
    def calculate_ground_coverage(self, altitude):
        """
        🌍 Drone'un Gördüğü Yer Alanını Hesapla
        
        Matematiksel Formül:
        - Yatay genişlik = 2 * altitude * tan(FOV_horizontal / 2)
        - Dikey yükseklik = 2 * altitude * tan(FOV_vertical / 2)  
        - Alan = genişlik × yükseklik
        
        Args:
            altitude: Drone yüksekliği (metre)
            
        Returns:
            dict: {
                'width_m': Yatay genişlik (metre),
                'height_m': Dikey yükseklik (metre),
                'area_m2': Toplam alan (m²),
                'meters_per_pixel_h': Yatay metre/piksel oranı,
                'meters_per_pixel_v': Dikey metre/piksel oranı
            }
        """
        # 📐 Trigonometrik hesaplama (FOV ve yükseklikten)
        ground_width = 2 * altitude * math.tan(self.fov_h / 2)
        ground_height = 2 * altitude * math.tan(self.fov_v / 2)
        
        # 📏 Toplam alan
        total_area = ground_width * ground_height
        
        # 🔍 Piksel başına metre oranı (GSD - Ground Sample Distance)
        meters_per_pixel_h = ground_width / self.image_width
        meters_per_pixel_v = ground_height / self.image_height
        
        result = {
            'altitude_m': altitude,
            'width_m': ground_width,
            'height_m': ground_height,
            'area_m2': total_area,
            'meters_per_pixel_h': meters_per_pixel_h,
            'meters_per_pixel_v': meters_per_pixel_v
        }
        
        return result
    
    def print_coverage_info(self, altitude):
        """
        📊 Kapsama Bilgilerini Yazdır
        """
        coverage = self.calculate_ground_coverage(altitude)
        
        print(f"\n🚁 {altitude}m Yükseklikten Görüş Alanı:")
        print(f"   📏 Genişlik: {coverage['width_m']:.2f} metre")
        print(f"   📏 Yükseklik: {coverage['height_m']:.2f} metre") 
        print(f"   📐 Toplam Alan: {coverage['area_m2']:.2f} m²")
        print(f"   🔍 Yatay GSD: {coverage['meters_per_pixel_h']:.4f} m/piksel")
        print(f"   🔍 Dikey GSD: {coverage['meters_per_pixel_v']:.4f} m/piksel")
        print(f"   📱 1 piksel = {coverage['meters_per_pixel_h']*100:.2f} cm")
        
        return coverage
    
    def pixel_to_real_world(self, pixel_x, pixel_y, altitude):
        """
        🗺️ Piksel Koordinatını Gerçek Dünya Koordinatına Çevir
        - Görüntü merkezini (0,0) kabul eder
        - Pozitif X = Doğu, Pozitif Y = Kuzey
        
        Args:
            pixel_x: X piksel koordinatı (görüntü merkezinden)
            pixel_y: Y piksel koordinatı (görüntü merkezinden)
            altitude: Drone yüksekliği (metre)
            
        Returns:
            tuple: (real_x_m, real_y_m) - Gerçek dünya koordinatları (metre)
        """
        coverage = self.calculate_ground_coverage(altitude)
        
        # Piksel koordinatını metre cinsine çevir
        real_x = pixel_x * coverage['meters_per_pixel_h']
        real_y = pixel_y * coverage['meters_per_pixel_v']
        
        return real_x, real_y
    
    def real_world_to_pixel(self, real_x, real_y, altitude):
        """
        📱 Gerçek Dünya Koordinatını Piksel Koordinatına Çevir
        
        Args:
            real_x: X gerçek koordinatı (metre)
            real_y: Y gerçek koordinatı (metre) 
            altitude: Drone yüksekliği (metre)
            
        Returns:
            tuple: (pixel_x, pixel_y) - Piksel koordinatları
        """
        coverage = self.calculate_ground_coverage(altitude)
        
        # Metre cinsini piksel koordinatına çevir
        pixel_x = real_x / coverage['meters_per_pixel_h']
        pixel_y = real_y / coverage['meters_per_pixel_v']
        
        return int(pixel_x), int(pixel_y)

