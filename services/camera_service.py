import cv2
import numpy as np
import os

class ArucoController:
    def __init__(self, marker_size=0.035):
        # Aruconun metre cinsinden boyutu
        self.marker_size = marker_size

        # Kamera kalibrasyonu
        calib_file = 'camera_calib.npz'
        if os.path.exists(calib_file):
            print(f"'{calib_file}' dosyası bulundu. Kalibrasyon verileri yükleniyor...")
            calib_data = np.load(calib_file)
            self.camera_matrix = calib_data['camera_matrix']
            self.distortion_coeffs = calib_data['dist_coeffs']
        else:
            print(f"Uyarı: '{calib_file}' dosyası bulunamadı. Varsayılan kalibrasyon verileri kullanılıyor.")
            self.camera_matrix = np.array([[1000, 0, 320],
                                    [0, 1000, 240],
                                    [0, 0, 1]], dtype=np.float32)

            self.distortion_coeffs = np.array([0, 0, 0, 0, 0], dtype=np.float32)

        # Aruco sözlüğü ve işaretçiler
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

        # Kamera açma
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            print("Hata: Kamera açılamadı.")
        
        print("Kamera açıldı.")

    def disconnect(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def distance(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        # Görüntü boyutlarını al
        h, w, _ = frame.shape
        camera_center_x = w / 2
        camera_center_y = h / 2

        # ArUco`ları Tespit Etme
        corners, ids, rejected = self.detector.detectMarkers(frame)

        if ids is not None and len(ids) > 0:
            
            # 3B pozisyonu hesapla
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, self.marker_size, self.camera_matrix, self.distortion_coeffs)
            
            for i in range(len(ids)):
                rvec = rvecs[i]
                tvec = tvecs[i]
                
                # Metre Cinsinden Yatay ve Dikey Mesafeyi Hesaplama ---
                # tvec[0][0]: Yatay kayma (sağ/sol)
                # tvec[0][1]: Dikey kayma (yukarı/aşağı)
                # tvec[0][2]: Derinlik (kameradan uzaklık)
                
                # Yatay mesafe: ArUco'nun kameranın merkezine olan yatay uzaklığı
                horizontal_distance = tvec[0][0]

                # Dikey mesafe: ArUco'nun kameranın merkezine olan dikey uzaklığı
                vertical_distance = -tvec[0][1]

                # --- 6. Görselleştirme ---
                # İşaretçinin 3D merkez noktasını (0,0,0) olarak kabul et
                marker_3d_center = np.zeros((1, 3), dtype=np.float32)

                # Bu 3D noktayı kameranın 2D görüntü düzlemine yansıt
                projected_points, _ = cv2.projectPoints(marker_3d_center, rvec, tvec, self.camera_matrix, self.distortion_coeffs)
                
                # Yansıtılan 2D noktanın x ve y koordinatlarını al
                marker_center_x = projected_points[0][0][0]
                marker_center_y = projected_points[0][0][1]

                # İşaretçinin etrafına eksenleri çiz
                cv2.drawFrameAxes(frame, self.camera_matrix, self.distortion_coeffs, rvec, tvec, self.marker_size * 0.5)

                # İşaretçinin merkezine daire çiz
                cv2.circle(frame, (int(marker_center_x), int(marker_center_y)), 5, (0, 251, 255), -1)

                # Ekrana mesafe bilgilerini yazdır
                text_horiz = f"Yatay Mesafe: {horizontal_distance:.2f} m"
                cv2.putText(frame, text_horiz, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 30)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                text_vert = f"Dikey Mesafe: {vertical_distance:.2f} m"
                cv2.putText(frame, text_vert, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Görüntüyü göster
                cv2.imshow('ArUco Takip', frame)
                return i , horizontal_distance , vertical_distance
        cv2.imshow('ArUco Takip', frame)
        return None

if __name__ == "__main__":
    aruco = ArucoController()
    while True:
        print(aruco.distance())
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    aruco.disconnect()