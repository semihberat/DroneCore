import asyncio
import sys
import os
# 📂 Path ayarları - üst klasördeki modüllere erişim için
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.drone_vision_calculator import DroneVisionCalculator
from aruco_mission.realtime_camera_viewer import RealtimeCameraViewer
import threading
from mavsdk.offboard import VelocityNedYaw
class SwarmDiscovery(OffboardControl):
    """
    🔄 Swarm Discovery - Kare Dalga Oscillation Misyonu
    - 10 döngülük kare pattern uçuş
    - İleri → Sol → İleri → Sağ hareket dizisi
    - Drone-relative yaw açı hesaplamaları
    """
    def __init__(self):
        super().__init__()
        self.pi_cam = RealtimeCameraViewer()  # Raspberry Pi kamerası sistemi 

    async def square_oscillation_by_meters(self, long_distance=50.0, short_distance=50.0, 
                                            velocity=10.0, repeat_count=10):
        """
        🟦 Kare Dalga Oscillation Pattern
        - 4 adımlık hareket dizisini 10 kez tekrarlar
        - Her hareket GPS tabanlı mesafe kontrolü ile yapılır
        
        Args:
            forward_length: İleri hareket mesafesi (metre) - varsayılan 50m
            side_length: Yan hareket mesafesi (metre) - varsayılan 10m  
            altitude: Uçuş yüksekliği (metre) - varsayılan 10m
            velocity: Hareket hızı (m/s) - varsayılan 2m/s
        
        Pattern:
        1️⃣ İleri (forward_length metre)
        2️⃣ Sol 90° + yan hareket (side_length metre)  
        3️⃣ İleri (forward_length metre)
        4️⃣ Sağ 90° + yan hareket (side_length metre)
        """
        print("🔄 Square Oscillation başlıyor...")
        
        # 🧭 Home yaw açısını referans al (drone-relative hesaplamalar için)
        current_yaw = self.home_position["yaw"]
        
        # 🔁 10 döngü kare dalga pattern
        for cycle in range(repeat_count):
            
            # 1️⃣ İleri git (başlangıç yönünde)
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)  # Stabilizasyon için kısa bekleme
            # 2️⃣ Sol 90° dön + yan hareket
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)  # Stabilizasyon için kısa bekleme
            # 3️⃣ İleri git (180° ters yönde)  
            await self.go_forward_by_meter(long_distance, velocity, current_yaw + 180.0)
            await self.hold_mode(1.0, current_yaw + 180.0)
            # 4️⃣ Sağ 90° dön + yan hareket (döngüyü tamamla)
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)
        
        if current_yaw + 90 != self.home_position["yaw"]:
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)  # Stabilizasyon için kısa bekleme
            

        await asyncio.sleep(1)  # Döngüler arası stabilizasyon
        
        print("✅ Square Oscillation tamamlandı!")

    async def square_oscillation_by_cam_fov(self, 
                                                distance1=30.0, 
                                                distance2=30.0,                               
                                                velocity=2.0,
                                                camera_fov_horizontal=62,
                                                camera_fov_vertical=49,
                                                image_width=1920,
                                                image_height=1080):
        drone_vision_calculator = DroneVisionCalculator(
            camera_fov_horizontal=camera_fov_horizontal,  # Pi Cam V2
            camera_fov_vertical=camera_fov_vertical,    # Pi Cam V2
            image_width=image_width,           # Önerilen çözünürlük
            image_height=image_height           # 4:3 oran
        )
        threading.Thread(target=self.pi_cam.show_camera_with_detection, ).start()
        
        sqosc_async_thread = asyncio.create_task(
            self.square_oscillation_by_meters(
                long_distance=distance1,
                short_distance=drone_vision_calculator.calculate_ground_coverage(self.target_altitude)["width_m"] / 2,
                repeat_count = int(distance2 /(drone_vision_calculator.calculate_ground_coverage(self.target_altitude)["width_m"] / 2)/2),
                velocity=velocity, 
            )
        )

        while not sqosc_async_thread.done() and not self.pi_cam.is_found:
            await asyncio.sleep(0.1)  # 100ms bekle ve tekrar kontrol et

        if self.pi_cam.is_found:
            sqosc_async_thread.cancel()
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
            )
            await self.hold_mode(1.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
            
            # Precision landing loop
            print("🎯 ArUco bulundu! Precision landing başlıyor...")
            
            while self.pi_cam.is_found and not self.pi_cam.is_centered:
                x, y, z = self.pi_cam.get_averaged_position()
                print(f"📍 Pozisyon: X={x:.3f}m, Y={y:.3f}m, Z={z:.3f}m")
                
                # Merkeze hareket (çok yavaş ve hassas)
                if abs(x) > 0.02 or abs(y) > 0.02:  # 2cm tolerans
                    # Çok küçük hız ile düzeltme hareketi
                    correction_speed = 0.5  # 0.5 m/s
                    move_x = -x * correction_speed  # Kamera koordinatı tersine
                    move_y = -y * correction_speed
                    
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(move_x, move_y, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                    )
                    await asyncio.sleep(0.2)  # Kısa hareket
                    
                    # Durdur
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                    )
                    await asyncio.sleep(0.2)  # Stabilizasyon
                else:
                    break
            
            if self.pi_cam.is_centered:
                print("✅ ArUco merkezlendi! Precision landing tamamlandı!")
            else:
                print("⚠️ ArUco kayboldu, precision landing durdu!")
                
        print("🔚 Misyon tamamlandı!")

    
    
   