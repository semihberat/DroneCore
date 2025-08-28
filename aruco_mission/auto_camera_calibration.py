#!/usr/bin/env python3
"""
Otomatik Kamera Kalibrasyonu Sistemi - DICT_4X4_50
Raspberry Pi kamerasını ArUco DICT_4X4_50 için otomatik kalibre eder
"""

import cv2
import numpy as np
import subprocess
import threading
import queue
import os
import time
import pickle
import glob
import signal

class AutoCameraCalibration:
    def __init__(self):
        """Otomatik kamera kalibrasyonu sistemi - DICT_4X4_50 için"""
        print("🤖 Otomatik Kamera Kalibrasyonu Sistemi")
        print("🎯 ArUco DICT_4X4_50 için optimize edildi")
        
        # Satranç tahtası ayarları
        self.chessboard_size = (9, 6)  # İç köşe sayısı
        self.square_size = 0.025  # Her karenin boyutu (2.5cm)
        
        # ArUco ayarları - DICT_4X4_50
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        print("📋 ArUco Sözlük: DICT_4X4_50 (4x4 bit, 50 marker)")
        
        # Kalibrasyon klasörü
        self.calibration_folder = "calibration_images"
        os.makedirs(self.calibration_folder, exist_ok=True)
        
        # Kamera stream ayarları
        self.process = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=5)
        
        # Satranç tahtası tespiti için
        self.detection_criteria = cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER
        self.detection_params = (30, 0.001)
        
        # 3D nokta koordinatları
        self.objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)
        self.objp *= self.square_size
        
        print("✅ Kalibrasyon sistemi hazır!")
    
    def create_test_aruco_markers(self):
        """DICT_4X4_50 için test ArUco marker'ları oluştur"""
        print("\n🎯 DICT_4X4_50 Test Marker'ları Oluşturuluyor...")
        
        # Birkaç farklı ID ile marker oluştur
        test_ids = [0, 1, 5, 10, 25, 42]  # DICT_4X4_50 için geçerli ID'ler (0-49)
        created_files = []
        
        for marker_id in test_ids:
            if marker_id < 50:  # DICT_4X4_50 maksimum 49 ID'ye kadar
                # 200x200 piksel marker oluştur
                marker = cv2.aruco.generateImageMarker(self.aruco_dict, marker_id, 200)
                
                # Kenarlık ekle (beyaz çerçeve)
                bordered = cv2.copyMakeBorder(marker, 50, 50, 50, 50, 
                                            cv2.BORDER_CONSTANT, value=255)
                
                # Dosya adı
                filename = f'test_marker_4x4_50_id_{marker_id}.png'
                cv2.imwrite(filename, bordered)
                created_files.append(filename)
                
                print(f"   ✅ Marker ID {marker_id}: {filename}")
        
        print(f"\n📋 {len(created_files)} adet DICT_4X4_50 marker oluşturuldu")
        print("📋 Bu marker'ları yazdırıp test edebilirsiniz")
        return created_files
    
    def create_chessboard_pattern(self):
        """Satranç tahtası deseni oluştur"""
        print("\n🏁 Satranç Tahtası Deseni Oluşturuluyor...")
        
        # Satranç tahtası boyutları (piksel)
        square_size_px = 50
        board_width = (self.chessboard_size[0] + 1) * square_size_px
        board_height = (self.chessboard_size[1] + 1) * square_size_px
        
        # Boş tahta oluştur
        chessboard = np.ones((board_height, board_width), dtype=np.uint8) * 255
        
        # Satranç deseni
        for i in range(self.chessboard_size[1] + 1):
            for j in range(self.chessboard_size[0] + 1):
                if (i + j) % 2 == 1:
                    y1 = i * square_size_px
                    y2 = (i + 1) * square_size_px
                    x1 = j * square_size_px
                    x2 = (j + 1) * square_size_px
                    chessboard[y1:y2, x1:x2] = 0
        
        # Kenarlık ekle
        bordered = cv2.copyMakeBorder(chessboard, 50, 50, 50, 50, 
                                    cv2.BORDER_CONSTANT, value=255)
        
        # Kaydet
        filename = 'chessboard_9x6.png'
        cv2.imwrite(filename, bordered)
        
        print(f"✅ Satranç tahtası kaydedildi: {filename}")
        print("📋 Bu dosyayı yazdırın ve düz bir yüzeye yapıştırın")
        return filename
    
    def start_camera_stream(self, width=640, height=480, fps=15):
        """Kamera stream başlat (kalibrasyon için daha düşük FPS)"""
        print(f"\n📹 Kalibrasyon Kamerası Başlatılıyor:")
        print(f"   Çözünürlük: {width}x{height}")
        print(f"   FPS: {fps}")
        
        # Geçici pipe file
        pipe_path = "/tmp/calibration_pipe"
        
        # Eski pipe'ı temizle
        if os.path.exists(pipe_path):
            os.remove(pipe_path)
        
        # FIFO oluştur
        os.mkfifo(pipe_path)
        
        # Libcamera komutu
        cmd = [
            'libcamera-vid',
            '--width', str(width),
            '--height', str(height),
            '--framerate', str(fps),
            '--timeout', '0',
            '--nopreview',
            '--codec', 'yuv420',
            '--output', pipe_path,
            '--flush'
        ]
        
        try:
            print("   🔄 Kamera başlatılıyor...")
            self.process = subprocess.Popen(cmd, 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          preexec_fn=os.setsid)
            
            time.sleep(2)
            
            if self.process.poll() is None:
                print("   ✅ Kamera çalışıyor!")
                return pipe_path
            else:
                print("   ❌ Kamera başlatılamadı!")
                return None
                
        except Exception as e:
            print(f"   ❌ Kamera hatası: {e}")
            return None
    
    def read_frames_thread(self, pipe_path, width, height):
        """Frame okuma thread'i"""
        frame_size = width * height * 3 // 2  # YUV420
        
        try:
            with open(pipe_path, 'rb') as pipe:
                while self.running:
                    try:
                        data = pipe.read(frame_size)
                        
                        if len(data) != frame_size:
                            continue
                        
                        # YUV'yi BGR'ye çevir
                        yuv_array = np.frombuffer(data, dtype=np.uint8)
                        yuv_frame = yuv_array.reshape((height * 3 // 2, width))
                        bgr_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
                        
                        # Queue'ya ekle
                        if not self.frame_queue.full():
                            self.frame_queue.put(bgr_frame)
                        else:
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                            self.frame_queue.put(bgr_frame)
                    
                    except Exception as e:
                        if self.running:
                            print(f"   ⚠️  Frame hatası: {e}")
                        break
        
        except Exception as e:
            print(f"   ❌ Pipe hatası: {e}")
        
        finally:
            if os.path.exists(pipe_path):
                os.remove(pipe_path)
    
    def auto_capture_calibration_images(self):
        """Otomatik kalibrasyon fotoğrafları çek"""
        print(f"\n📸 Otomatik Kalibrasyon Fotoğrafları:")
        print("🎯 İDEAL KALİBRASYON İÇİN:")
        print("📋 Satranç tahtasını EĞİK tutun (dümdüz DEĞİL!)")
        print("📋 FARKLI açılardan gösterin (15°, 30°, 45°)")
        print("📋 FARKLI mesafelerden gösterin (yakın, orta, uzak)")
        print("📋 Kameranın KENAR bölgelerine götürün")
        print("📋 Tahtayı DÖNDÜRÜN (45°, 90° açılarla)")
        print("📋 Sistem 2 saniyede bir otomatik çekecek")
        print("📋 ESC ile çıkış")
        
        # Kamera başlat
        pipe_path = self.start_camera_stream()
        if not pipe_path:
            print("❌ Kamera başlatılamadı!")
            return []
        
        # Frame okuma thread'ini başlat
        self.running = True
        read_thread = threading.Thread(
            target=self.read_frames_thread, 
            args=(pipe_path, 640, 480)
        )
        read_thread.daemon = True
        read_thread.start()
        
        # OpenCV penceresi
        cv2.namedWindow('Kalibrasyon - Satranç Tahtası', cv2.WINDOW_AUTOSIZE)
        
        captured_images = []
        last_capture_time = 0
        capture_interval = 2.0  # 2 saniyede bir otomatik çekim
        required_images = 20
        
        print(f"\n🎯 Hedef: {required_images} farklı açıdan fotoğraf")
        print("🔄 Otomatik çekim başladı...")
        
        try:
            while len(captured_images) < required_images:
                try:
                    frame = self.frame_queue.get(timeout=0.1)
                    current_time = time.time()
                    
                    # Frame kopyası
                    display_frame = frame.copy()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Satranç tahtası tespit et
                    ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)
                    
                    if ret:
                        # Köşeleri çiz
                        cv2.drawChessboardCorners(display_frame, self.chessboard_size, corners, ret)
                        
                        # Pozisyon analizi
                        corner_positions = corners.reshape(-1, 2)
                        center_x = np.mean(corner_positions[:, 0])
                        center_y = np.mean(corner_positions[:, 1])
                        
                        # Kameraya göre pozisyon
                        frame_center_x = display_frame.shape[1] / 2
                        frame_center_y = display_frame.shape[0] / 2
                        
                        # Pozisyon kategorisi
                        pos_x = "MERKEZ"
                        if center_x < frame_center_x * 0.7:
                            pos_x = "SOL"
                        elif center_x > frame_center_x * 1.3:
                            pos_x = "SAĞ"
                            
                        pos_y = "MERKEZ" 
                        if center_y < frame_center_y * 0.7:
                            pos_y = "ÜST"
                        elif center_y > frame_center_y * 1.3:
                            pos_y = "ALT"
                        
                        # Mesafe tahmini (köşe alanından)
                        corner_area = cv2.contourArea(corner_positions)
                        if corner_area > 50000:
                            distance = "YAKIN"
                        elif corner_area > 20000:
                            distance = "ORTA"
                        else:
                            distance = "UZAK"
                        
                        # Eğim analizi (perspektif)
                        corner_rect = cv2.minAreaRect(corner_positions)
                        angle = abs(corner_rect[2])
                        if angle > 30:
                            tilt = "ÇOK EĞİK"
                        elif angle > 15:
                            tilt = "EĞİK"
                        else:
                            tilt = "DÜZ"
                        
                        # Otomatik çekim zamanı geldi mi?
                        if current_time - last_capture_time > capture_interval:
                            # Alt-piksel hassasiyeti
                            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), 
                                                      (self.detection_criteria, *self.detection_params))
                            
                            # Fotoğrafı kaydet
                            image_path = os.path.join(self.calibration_folder, f'calibration_{len(captured_images):02d}.jpg')
                            cv2.imwrite(image_path, frame)
                            captured_images.append(image_path)
                            last_capture_time = current_time
                            
                            position_info = f"{pos_x}-{pos_y}, {distance}, {tilt}"
                            print(f"   📸 Fotoğraf {len(captured_images)}/{required_images}: {position_info}")
                            
                            # Görsel geri bildirim
                            cv2.putText(display_frame, f"ÇEKILDI! {len(captured_images)}/{required_images}", 
                                      (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                        
                        # Tespit durumu ve pozisyon bilgisi
                        cv2.putText(display_frame, "SATRANÇ TAHTASI BULUNDU", 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
                        # Pozisyon bilgisi
                        pos_info = f"{pos_x}-{pos_y} | {distance} | {tilt}"
                        cv2.putText(display_frame, pos_info, 
                                  (10, display_frame.shape[0] - 80), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                        
                        # Açı önerisi
                        if tilt == "DÜZ":
                            cv2.putText(display_frame, "TAHTAYI EĞİN! (15-30°)", 
                                      (10, display_frame.shape[0] - 110), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        elif pos_x == "MERKEZ" and pos_y == "MERKEZ":
                            cv2.putText(display_frame, "KENARLARA GÖTÜRÜN!", 
                                      (10, display_frame.shape[0] - 110), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        # Tespit yok
                        cv2.putText(display_frame, "SATRANÇ TAHTASI ARAMASINDA...", 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    # İlerleme göster
                    progress_text = f"Fotoğraf: {len(captured_images)}/{required_images}"
                    cv2.putText(display_frame, progress_text, 
                              (10, display_frame.shape[0] - 20), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
                    # Kalan süre
                    time_until_next = max(0, capture_interval - (current_time - last_capture_time))
                    if ret and time_until_next > 0:
                        cv2.putText(display_frame, f"Sonraki çekim: {time_until_next:.1f}s", 
                                  (10, display_frame.shape[0] - 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    cv2.imshow('Kalibrasyon - Satranç Tahtası', display_frame)
                    
                    # Klavye kontrolü
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC
                        print("\n⏹️  Kullanıcı tarafından durduruldu!")
                        break
                    
                except queue.Empty:
                    # Frame yoksa boş frame
                    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(empty_frame, "Kamera bekleniyor...", 
                              (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.imshow('Kalibrasyon - Satranç Tahtası', empty_frame)
                    
                    key = cv2.waitKey(30) & 0xFF
                    if key == 27:
                        break
                
                except KeyboardInterrupt:
                    print("\n⏹️  Program durduruldu!")
                    break
        
        except Exception as e:
            print(f"❌ Kalibrasyon hatası: {e}")
        
        finally:
            cv2.destroyAllWindows()
            self.stop_stream()
        
        print(f"\n✅ {len(captured_images)} fotoğraf çekildi!")
        return captured_images
    
    def calibrate_from_captured_images(self, image_paths):
        """Çekilen fotoğraflardan kalibrasyou yap"""
        if len(image_paths) < 10:
            print(f"⚠️  Sadece {len(image_paths)} fotoğraf! En az 10 gerekli")
            return None, None
        
        print(f"\n🔧 {len(image_paths)} fotoğraf ile kalibrasyon yapılıyor...")
        
        objpoints = []  # 3D noktalar
        imgpoints = []  # 2D noktalar
        
        valid_images = 0
        for image_path in image_paths:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Satranç tahtası köşelerini bul
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)
            
            if ret:
                valid_images += 1
                objpoints.append(self.objp)
                
                # Alt-piksel hassasiyeti
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), 
                                          (self.detection_criteria, *self.detection_params))
                imgpoints.append(corners2)
        
        print(f"📊 {valid_images}/{len(image_paths)} fotoğraf kullanılabilir")
        
        if valid_images < 10:
            print("❌ Yeterli geçerli fotoğraf yok!")
            return None, None
        
        # Kamera kalibrasyonu
        img_shape = gray.shape[::-1]
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_shape, None, None
        )
        
        if ret:
            print("✅ Kalibrasyon başarılı!")
            print(f"📐 Kamera Matrisi:")
            print(camera_matrix)
            print(f"🔍 Distorsiyon Katsayıları:")
            print(dist_coeffs)
            
            # Kalibrasyonu kaydet
            calibration_data = {
                'camera_matrix': camera_matrix,
                'dist_coeffs': dist_coeffs,
                'rvecs': rvecs,
                'tvecs': tvecs,
                'image_shape': img_shape,
                'calibration_error': ret
            }
            
            with open('camera_calibration.pkl', 'wb') as f:
                pickle.dump(calibration_data, f)
            
            print("💾 Kalibrasyon kaydedildi: camera_calibration.pkl")
            
            # realtime_camera_viewer.py'ye entegrasyon kodu göster
            self.show_integration_code(camera_matrix, dist_coeffs)
            
            return camera_matrix, dist_coeffs
        else:
            print("❌ Kalibrasyon başarısız!")
            return None, None
    
    def show_integration_code(self, camera_matrix, dist_coeffs):
        """Entegrasyon kodunu göster"""
        print("\n📝 realtime_camera_viewer.py DICT_4X4_50 için güncellenecek:")
        print("=" * 60)
        print("# ArUco sözlük değişikliği:")
        print("self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)")
        print("\n# Kamera kalibrasyonu:")
        print(f"self.camera_matrix = np.array({camera_matrix.tolist()}, dtype=np.float32)")
        print(f"self.dist_coeffs = np.array({dist_coeffs.flatten().tolist()}, dtype=np.float32)")
        print("=" * 60)
        print("🎯 Bu değişiklikler otomatik olarak uygulanacak!")
    
    def stop_stream(self):
        """Stream'i durdur"""
        self.running = False
        
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=3)
            except:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass
        
        # Queue temizle
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break


def main():
    print("🤖 Otomatik Kamera Kalibrasyonu Sistemi")
    print("🎯 ArUco DICT_4X4_50 için Optimize")
    print("=" * 50)
    
    calibrator = AutoCameraCalibration()
    
    print("\n🎯 Adımlar:")
    print("1️⃣ Satranç tahtası deseni oluştur")
    print("2️⃣ DICT_4X4_50 test marker'ları oluştur")
    print("3️⃣ Otomatik kalibrasyon fotoğrafları çek")
    print("4️⃣ Kalibrasyonu hesapla")
    print("5️⃣ realtime_camera_viewer.py otomatik güncelle")
    
    # Satranç tahtası oluştur
    chessboard_file = calibrator.create_chessboard_pattern()
    
    # ArUco test marker'ları oluştur
    marker_files = calibrator.create_test_aruco_markers()
    
    print(f"\n📋 YAPILACAKLAR:")
    print(f"1. {chessboard_file} dosyasını yazdırın (kalibrasyon için)")
    print("2. Düz bir yüzeye (karton/duvar) yapıştırın")
    print("3. Test marker'larını da yazdırabilirsiniz (opsiyonel)")
    print("4. Enter'a basın")
    
    input("\n✅ Hazır olduğunuzda Enter'a basın...")
    
    # Otomatik fotoğraf çekimi
    image_paths = calibrator.auto_capture_calibration_images()
    
    if len(image_paths) >= 10:
        # Kalibrasyonu hesapla
        camera_matrix, dist_coeffs = calibrator.calibrate_from_captured_images(image_paths)
        
        if camera_matrix is not None:
            print("\n🎉 Kalibrasyon tamamlandı!")
            
            # realtime_camera_viewer.py'yi otomatik güncelle
            update_realtime_viewer_for_4x4_50(camera_matrix, dist_coeffs)
            
        else:
            print("\n❌ Kalibrasyon başarısız!")
    else:
        print(f"\n⚠️  Yeterli fotoğraf alınamadı: {len(image_paths)}")


def update_realtime_viewer_for_4x4_50(camera_matrix, dist_coeffs):
    """realtime_camera_viewer.py dosyasını DICT_4X4_50 için otomatik güncelle"""
    print("\n🔄 realtime_camera_viewer.py DICT_4X4_50 için güncelleniyor...")
    
    try:
        # Dosyayı oku
        with open('realtime_camera_viewer.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # DICT_6X6_250 -> DICT_4X4_50 değiştir
        content = content.replace(
            'cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)',
            'cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)'
        )
        
        # Sistem başlık güncelle
        content = content.replace(
            'Gerçek Zamanlı Kamera + ArUco Sistemi',
            'Gerçek Zamanlı Kamera + ArUco DICT_4X4_50 Sistemi'
        )
        
        content = content.replace(
            'Gerçek Zamanlı Kamera + ArUco 3D Sistemi',
            'Gerçek Zamanlı Kamera + ArUco DICT_4X4_50 3D Sistemi'
        )
        
        # Test marker ID güncelle (DICT_4X4_50 için 0-49 arası)
        content = content.replace(
            'def create_marker(self, marker_id=42):',
            'def create_marker(self, marker_id=25):'
        )
        
        content = content.replace(
            'viewer_marker_42.png',
            'viewer_marker_4x4_50_id_25.png'
        )
        
        # Başlık güncelle
        content = content.replace(
            'marker_file = system.create_marker(42)',
            'marker_file = system.create_marker(25)'
        )
        
        # Dosyayı kaydet
        with open('realtime_camera_viewer.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ realtime_camera_viewer.py DICT_4X4_50 için güncellendi!")
        print("📋 Değişiklikler:")
        print("   🔄 ArUco sözlük: DICT_6X6_250 → DICT_4X4_50")
        print("   🔄 Test marker ID: 42 → 25")
        print("   🔄 Sistem başlığı güncellendi")
        print("   🔄 Kişisel kalibrasyon otomatik yüklenecek")
        
    except Exception as e:
        print(f"⚠️  Otomatik güncelleme hatası: {e}")
        print("📝 Manuel olarak DICT_4X4_50 güncellemesi gerekebilir")


if __name__ == "__main__":
    import signal
    main()
