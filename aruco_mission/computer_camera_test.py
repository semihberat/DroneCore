#!/usr/bin/env python3
"""
Computer Camera + OpenCV + Gerçek Zamanlı Görüntü Sistemi
ArUco DICT_4X4_50 - 3D Pozisyon Tespiti
Bilgisayar kamerası (webcam) için test versiyonu
"""

import cv2
import numpy as np
import time
import pickle
import os

class ComputerCameraTest:
    def __init__(self, target_marker_id=42):
        """Bilgisayar kamerası ile gerçek zamanlı ArUco sistemi - DICT_4X4_50"""
        
        # ArUco detection status
        self.is_found = False
        self.is_centered = False
        
        # Position tracking
        self.x_vec, self.y_vec, self.z_vec = 0.0, 0.0, 0.0
        
        # Precision landing parameters
        self.position_buffer = []  # Son N değeri sakla
        self.buffer_size = 10  # 10 frame ortalama
        self.center_threshold = 0.025  # 5cm merkez toleransı
        self.stable_count = 0
        self.stable_threshold = 15  # 5 frame sabit kalırsa merkezde
        
        # Hedef marker ID'si
        self.target_marker_id = target_marker_id
        if self.target_marker_id >= 50:
            self.target_marker_id = 42
        
        # ArUco setup - DICT_4X4_50
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.detector_params = cv2.aruco.DetectorParameters()
        
        # Daha hassas tespit için parametreler
        self.detector_params.adaptiveThreshWinSizeMin = 3
        self.detector_params.adaptiveThreshWinSizeMax = 23
        self.detector_params.adaptiveThreshWinSizeStep = 10
        self.detector_params.minMarkerPerimeterRate = 0.03
        self.detector_params.maxMarkerPerimeterRate = 4.0
        
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.detector_params)
        
        # ArUco marker boyutu (metre cinsinden - gerçek boyutu)
        self.marker_size = 0.05  # 5cm marker boyutu
        
        # 3D Pose estimation için kamera kalibrasyonu
        self.setup_camera_calibration()
        
        # Webcam objesi
        self.cap = None
      
    
    def setup_camera_calibration(self):
        """Kamera kalibrasyonu parametrelerini ayarla"""
        # Önce kaydedilmiş kalibrasyonu yüklemeyi dene
        if os.path.exists('camera_calibration.pkl'):
            try:
                with open('camera_calibration.pkl', 'rb') as f:
                    calibration_data = pickle.load(f)
                
                self.camera_matrix = calibration_data['camera_matrix']
                self.dist_coeffs = calibration_data['dist_coeffs']
                return
                
            except Exception as e:
                pass
        
        # Varsayılan kalibrasyon parametreleri
        self.camera_matrix = np.array([
            [500.0, 0.0, 320.0],    # fx=500, cx=320 (640/2)
            [0.0, 500.0, 240.0],    # fy=500, cy=240 (480/2)
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
        # Distorsiyon katsayıları (lens bozulması)
        self.dist_coeffs = np.array([0.1, -0.2, 0.0, 0.0, 0.0], dtype=np.float32)
    
    def update_marker_size(self, size_in_meters):
        """Marker boyutunu güncelle (metre cinsinden)"""
        self.marker_size = size_in_meters
    
    def update_position(self, x, y, z):
        """ArUco pozisyonunu güncelle ve ortalama hesapla"""
        # Yeni pozisyonu buffer'a ekle
        self.position_buffer.append((x, y, z))
        
        # Buffer boyutunu kontrol et
        if len(self.position_buffer) > self.buffer_size:
            self.position_buffer.pop(0)  # En eski değeri çıkar
        
        # Ortalama hesapla
        if self.position_buffer:
            avg_x = sum(pos[0] for pos in self.position_buffer) / len(self.position_buffer)
            avg_y = sum(pos[1] for pos in self.position_buffer) / len(self.position_buffer)
            avg_z = sum(pos[2] for pos in self.position_buffer) / len(self.position_buffer)
            
            self.x_vec, self.y_vec, self.z_vec = avg_x, avg_y, avg_z
            
            # Merkez kontrolü (X ve Y koordinatları)
            distance_from_center = np.sqrt(avg_x**2 + avg_y**2)
            
            if distance_from_center < self.center_threshold:
                self.stable_count += 1
                if self.stable_count >= self.stable_threshold:
                    self.is_centered = True
            else:
                self.stable_count = 0
                self.is_centered = False
    
    def get_averaged_position(self):
        """Ortalanmış pozisyonu döndür"""
        return self.x_vec, self.y_vec, self.z_vec
    
    def reset_position_tracking(self):
        """Pozisyon takibini sıfırla"""
        self.position_buffer = []
        self.stable_count = 0
        self.is_centered = False
        self.is_found = False
    
    def estimate_pose(self, corners):
        """ArUco marker'ın 3D pozisyonunu ve oryantasyonunu hesapla"""
        if corners is None or len(corners) == 0:
            return None, None
        
        # Pose estimation
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners, self.marker_size, self.camera_matrix, self.dist_coeffs
        )
        
        return rvecs, tvecs
    
    def rotation_vector_to_euler(self, rvec):
        """Rotation vector'ı Euler açılarına çevir (derece cinsinden)"""
        # Rotation matrix'e çevir
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        
        # Euler açılarını hesapla (X-Y-Z sırası)
        sy = np.sqrt(rotation_matrix[0,0] * rotation_matrix[0,0] + rotation_matrix[1,0] * rotation_matrix[1,0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(rotation_matrix[2,1], rotation_matrix[2,2])
            y = np.arctan2(-rotation_matrix[2,0], sy)
            z = np.arctan2(rotation_matrix[1,0], rotation_matrix[0,0])
        else:
            x = np.arctan2(-rotation_matrix[1,2], rotation_matrix[1,1])
            y = np.arctan2(-rotation_matrix[2,0], sy)
            z = 0
        
        # Radyandan dereceye çevir
        return np.degrees([x, y, z])
    
    def draw_3d_axis(self, frame, rvec, tvec, camera_matrix, dist_coeffs, length=0.03):
        """3D eksenleri çiz (X=Kırmızı, Y=Yeşil, Z=Mavi)"""
        # 3D nokta tanımla (eksenlerin uç noktaları)
        axis_points = np.array([
            [0, 0, 0],           # Orijin
            [length, 0, 0],      # X ekseni (Kırmızı)
            [0, length, 0],      # Y ekseni (Yeşil) 
            [0, 0, -length]      # Z ekseni (Mavi) - negatif çünkü kamera koordinat sistemi
        ], dtype=np.float32)
        
        # 3D noktaları 2D'ye projekte et
        axis_2d, _ = cv2.projectPoints(axis_points, rvec, tvec, camera_matrix, dist_coeffs)
        axis_2d = axis_2d.astype(int)
        
        # Orijin noktası
        origin = tuple(axis_2d[0].ravel())
        x_point = tuple(axis_2d[1].ravel())
        y_point = tuple(axis_2d[2].ravel())
        z_point = tuple(axis_2d[3].ravel())

        # Eksenleri çiz
        cv2.line(frame, origin, x_point, (0, 0, 255), 3)    # X ekseni - Kırmızı
        cv2.line(frame, origin, y_point, (0, 255, 0), 3)    # Y ekseni - Yeşil
        cv2.line(frame, origin, z_point, (255, 0, 0), 3)    # Z ekseni - Mavi
        
        # Eksen etiketleri
        cv2.putText(frame, 'X', x_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, 'Y', y_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, 'Z', z_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return frame
    
    def draw_crosshair(self, frame):
        """Kamera ortasına crosshair çiz"""
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Crosshair boyutları
        line_length = 30
        thickness = 2
        
        # Yatay çizgi
        cv2.line(frame, 
                (center_x - line_length, center_y), 
                (center_x + line_length, center_y), 
                (0, 255, 0), thickness)
        
        # Dikey çizgi
        cv2.line(frame, 
                (center_x, center_y - line_length), 
                (center_x, center_y + line_length), 
                (0, 255, 0), thickness)
        
        # Merkez nokta
        cv2.circle(frame, (center_x, center_y), 3, (0, 255, 0), -1)
        
        # Crosshair etrafında çember (hedef alanı)
        cv2.circle(frame, (center_x, center_y), 50, (0, 255, 0), 1)
        
        return frame
    
    def create_marker(self, marker_id=None):
        """DICT_4X4_50 test marker oluştur"""
        # Hedef marker ID'sini kullan
        if marker_id is None:
            marker_id = self.target_marker_id
            
        # ID kontrolü (DICT_4X4_50 için 0-49 arası)
        if marker_id >= 50:
            marker_id = 42
        
        marker = cv2.aruco.generateImageMarker(self.aruco_dict, marker_id, 200)
        bordered = cv2.copyMakeBorder(marker, 50, 50, 50, 50, 
                                    cv2.BORDER_CONSTANT, value=255)
        
        filename = f'target_marker_id_{marker_id}.png'
        cv2.imwrite(filename, bordered)
        return filename
    
    def start_webcam(self, camera_index=0, width=640, height=480):
        """Bilgisayar kamerasını başlat"""
        # OpenCV VideoCapture ile webcam bağlantısı
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            # Farklı index'leri dene
            for i in range(5):
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    camera_index = i
                    break
            else:
                return False
        
        # Kamera ayarları
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Test frame al
        ret, test_frame = self.cap.read()
        if not ret:
            return False
        
        return True
    
    def show_camera_with_detection(self):
        """Bilgisayar kamerası ile ArUco tespiti"""
        
        # Webcam başlat
        if not self.start_webcam():
            return
        
        # OpenCV penceresi oluştur
        cv2.namedWindow('ArUco Computer Camera', cv2.WINDOW_AUTOSIZE)
        
        # İstatistikler
        start_time = time.time()
        frame_count = 0
        detection_count = 0
        last_detection_time = 0
        
        try:
            while True:
                # Frame al
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                frame_count += 1
                current_time = time.time()
                
                # Frame kopyası (orijinali bozmamak için)
                display_frame = frame.copy()
                
                # ArUco tespit
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, rejected = self.detector.detectMarkers(gray)
                
                # Sadece hedef marker'ı filtrele
                if ids is not None:
                    # Hedef ID'yi ara
                    target_indices = []
                    for i, marker_id in enumerate(ids.flatten()):
                        if marker_id == self.target_marker_id:
                            target_indices.append(i)
                    
                    # Sadece hedef marker varsa işle
                    if target_indices:
                        # Sadece hedef marker'ın verilerini al
                        filtered_corners = [corners[i] for i in target_indices]
                        filtered_ids = np.array([[self.target_marker_id]])
                        
                        detection_count += 1
                        last_detection_time = current_time
                        
                        # Marker'ı çiz
                        cv2.aruco.drawDetectedMarkers(display_frame, filtered_corners, filtered_ids)
                        
                        # 3D Pose estimation
                        rvecs, tvecs = self.estimate_pose(filtered_corners)
                        
                        # Hedef marker için bilgi
                        for i, corner_set in enumerate(filtered_corners):
                            marker_id = self.target_marker_id
                            
                            # Merkez hesapla
                            center = corner_set[0].mean(axis=0).astype(int)
                            cv2.putText(display_frame, f"ID {marker_id}", 
                                      (center[0]-20, center[1]-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                     
                            
                            # 3D pozisyon bilgileri varsa
                            if rvecs is not None and tvecs is not None:
                                rvec = rvecs[i][0]
                                tvec = tvecs[i][0]
                                
                                # 3D eksenleri çiz
                                self.draw_3d_axis(display_frame, rvec, tvec, 
                                                self.camera_matrix, self.dist_coeffs)
                                
                                # Pozisyon bilgileri (metre cinsinden)
                                x, y, z = tvec
                                
                                # Pozisyonu güncelle ve ortalama hesapla
                                self.update_position(x, y, z)
                                self.is_found = True
                                
                                # Oryantasyon bilgileri (Euler açıları - derece)
                                euler_angles = self.rotation_vector_to_euler(rvec)
                                roll, pitch, yaw = euler_angles
                                
                                # Ortalanmış pozisyonu al
                                avg_x, avg_y, avg_z = self.get_averaged_position()
                                
                                # Pozisyon yazısı (cm cinsinden göster)
                                pos_text = f"Avg X:{avg_x*100:.1f}cm Y:{avg_y*100:.1f}cm Z:{avg_z*100:.1f}cm"
                                cv2.putText(display_frame, pos_text, 
                                          (center[0]-100, center[1]-40), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                                
                                # Merkez durumu
                                center_status = "CENTERED" if self.is_centered else "CENTERING"
                                center_color = (0, 255, 0) if self.is_centered else (0, 255, 255)
                                cv2.putText(display_frame, center_status, 
                                          (center[0]-50, center[1]-55), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, center_color, 2)
                            
                            # Hedef marker vurgusu
                            cv2.putText(display_frame, f"🎯 HEDEF: {marker_id}", 
                                      (center[0]-40, center[1]-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 3)
                            
                            # Özel hedef marker çerçevesi
                            cv2.circle(display_frame, tuple(center), 8, (0, 255, 0), -1)
                            cv2.circle(display_frame, tuple(center), 15, (0, 255, 0), 3)
                            
                        # Hedef tespit mesajı
                        status_text = "ARUCO_CENTERED" if self.is_centered else "ARUCO_FOUND"
                        status_color = (0, 255, 0) if self.is_centered else (0, 255, 255)
                        cv2.putText(display_frame, status_text, 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 3)
          
                    else:
                        # Hedef marker yok
                        self.reset_position_tracking()
                        cv2.putText(display_frame, f"Searching...", 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    # Hiç marker tespit edilmedi
                    self.reset_position_tracking()
                    cv2.putText(display_frame, f"Searching for ArUco ID: {self.target_marker_id}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # FPS ve istatistikler
                elapsed = current_time - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                
                # Bilgi metinleri
                info_text = [
                    f"FPS: {fps:.1f}",
                    f"Frame: {frame_count}",
                    f"Tespit: {detection_count}",
                    f"Süre: {elapsed:.1f}s"
                ]
                
                # Bilgileri ekranda göster
                for i, text in enumerate(info_text):
                    y_pos = display_frame.shape[0] - 100 + (i * 25)
                    cv2.putText(display_frame, text, (10, y_pos), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(display_frame, text, (10, y_pos), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
                
                # Son tespit zamanı
                if detection_count > 0:
                    time_since_detection = current_time - last_detection_time
                    if time_since_detection < 2:  # 2 saniye içinde
                        cv2.putText(display_frame, "✅ HEDEF MARKER GÖRÜLÜYOR", 
                                  (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Hedef marker bilgisi (sürekli göster)
                cv2.putText(display_frame, f"Hedef ID: {self.target_marker_id}", 
                          (10, display_frame.shape[0] - 130), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(display_frame, f"Hedef ID: {self.target_marker_id}", 
                          (10, display_frame.shape[0] - 130), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
                
                # Crosshair çiz (her zaman görünsün)
                display_frame = self.draw_crosshair(display_frame)
                
                # Çerçeve göster
                cv2.imshow('ArUco Computer Camera', display_frame)
                
                # Klavye kontrolü
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27:  # ESC
                    break
                elif key == ord('s') or key == ord('S'):  # Screenshot
                    screenshot_path = f'screenshot_{int(current_time)}.jpg'
                    cv2.imwrite(screenshot_path, display_frame)
                elif key == ord(' '):  # SPACE - marker kaydet
                    if ids is not None:
                        marker_path = f'detected_marker_{int(current_time)}.jpg'
                        cv2.imwrite(marker_path, display_frame)
        
        except KeyboardInterrupt:
            pass
        
        except Exception as e:
            pass
        
        finally:
            # Temizlik
            cv2.destroyAllWindows()
            if self.cap:
                self.cap.release()


def main():
    try:
        target_id = int(input("Hedef Marker ID'sini girin (varsayılan: 42): ") or "42")
        if target_id < 0 or target_id >= 50:
            target_id = 42
    except ValueError:
        target_id = 42
    
    system = ComputerCameraTest(target_marker_id=target_id)
    
    # Hedef marker oluştur
    marker_file = system.create_marker()
    
    try:
        # Kamera görüntüsü ile tespit
        system.show_camera_with_detection()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
