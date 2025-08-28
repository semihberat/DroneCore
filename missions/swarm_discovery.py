import asyncio
import sys
import os
# Add parent directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.drone_vision_calculator import DroneVisionCalculator
from aruco_mission.realtime_camera_viewer import RealtimeCameraViewer
from aruco_mission.computer_camera_test import ComputerCameraTest
import threading
from mavsdk.offboard import VelocityNedYaw
from services.xbee_service import XbeeService

class SwarmDiscovery(OffboardControl):
    """
    SwarmDiscovery mission: square oscillation flight and ArUco-based precision landing.
    """
    def __init__(self, xbee_port: str = None, use_computer_camera: bool = False):
        super().__init__()
        self.pi_cam = RealtimeCameraViewer() if not use_computer_camera else ComputerCameraTest()
        self.mission_completed = False
        self.landing_command_received = False  # Command 1 için flag
        self.feedback_received = False  # Feedback alındı mı flag'i
        self.THRESHOLD = 0.01  # 1 cm = normal hassasiyet (class seviyesinde)
        self.xbee_service = XbeeService(
            message_received_callback=XbeeService.default_message_received_callback,
            port=xbee_port,
            max_queue_size=100,
            baudrate=57600
        )
        # Instance method'u callback olarak kullan
        self.xbee_service.set_custom_message_handler(self.handle_xbee_message)
        
        print("-- Starting XBee service...")
        try:
            self.xbee_service.listen()
            print("✅ XBee service started successfully!")
        except Exception as e:
            print(f"⚠️ XBee service failed to start: {e}")
            print("   Continuing without XBee...")

    
    def handle_xbee_message(self, message_dict: dict) -> None:
        """
        Handle received XBee message data.
        """
        data = message_dict.get("data", "")
        print(f"Received data: {data}")
        try:
            parts = data.split(',')
            if len(parts) == 4:
                lat = int(parts[0])
                lon = int(parts[1])
                alt = int(parts[2])
                command = int(parts[3])
                print(f"Parsed data - Lat: {lat}, Lon: {lon}, Alt: {alt}, Command: {command}")
                
                if command == 1:
                    print("Command 1 received - sending feedback and setting landing flag!")
                    # Feedback gönder (command=2)
                    self.send_feedback_message(lat, lon, alt)
                    # Landing flag set et
                    self.landing_command_received = True
                    
                elif command == 2:
                    print("Feedback received - message confirmed!")
                    # Feedback alındı, iniş yapabilir
                    self.feedback_received = True
                    
                else:
                    print(f"Command {command} - no action taken")
                    
        except ValueError as e:
            print(f"Data parse error: {e}")
        except Exception as e:
            print(f"Message handler error: {e}")
    
    def send_feedback_message(self, lat: int, lon: int, alt: int) -> None:
        """
        Send feedback message (command=2) to confirm message received.
        """
        try:
            feedback_message = f"{lat},{lon},{alt},2"
            print(f"Sending feedback: {feedback_message}")
            
            # XBee ile feedback gönder
            if hasattr(self, 'xbee_service') and self.xbee_service:
                # Thread-safe gönderim
                import threading
                def send_feedback():
                    try:
                        self.xbee_service.send_broadcast_message(feedback_message, False)
                        print("Feedback sent successfully!")
                    except Exception as e:
                        print(f"Feedback send error: {e}")
                
                threading.Thread(target=send_feedback, daemon=True).start()
            else:
                print("XBee service not available for feedback")
                
        except Exception as e:
            print(f"Feedback message error: {e}")

    async def square_oscillation_by_meters(self, long_distance: float, short_distance: float, velocity: float, repeat_count: int):
        """
        Square oscillation pattern flight.
        Args:
            long_distance: forward movement (meters)
            short_distance: side movement (meters)
            velocity: movement speed (m/s)
            repeat_count: number of cycles
        """
        print("Square Oscillation started...")
        current_yaw = self.home_position["yaw"]
        for cycle in range(repeat_count):
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)
            await self.go_forward_by_meter(long_distance, velocity, current_yaw + 180.0)
            await self.hold_mode(1.0, current_yaw + 180.0)
            await self.go_forward_by_meter(short_distance, velocity, current_yaw + 90.0)
            await self.hold_mode(1.0, current_yaw + 90.0)
        if current_yaw + 90 != self.home_position["yaw"]:
            await self.go_forward_by_meter(long_distance, velocity, current_yaw)
            await self.hold_mode(1.0, current_yaw)
        await asyncio.sleep(1)
        print("Square Oscillation finished!")

    async def square_oscillation_by_cam_fov(
        self,
        distance1: float,
        distance2: float,
        velocity: float,
        camera_fov_horizontal: float,
        camera_fov_vertical: float,
        image_width: int,
        image_height: int
    ):
        """
        Square oscillation flight based on camera FOV and ArUco detection.
        """
        drone_vision_calculator = DroneVisionCalculator(
            camera_fov_horizontal=camera_fov_horizontal,
            camera_fov_vertical=camera_fov_vertical,
            image_width=image_width,
            image_height=image_height
        )
        
        # Camera thread'ini daemon olarak başlat ve referansını sakla
        camera_thread = threading.Thread(
            target=self.pi_cam.show_camera_with_detection, 
            daemon=True
        )
        camera_thread.start()
        
        ground_coverage = drone_vision_calculator.calculate_ground_coverage(self.target_altitude)
        short_distance = ground_coverage["width_m"] / 2
        repeat_count = int(distance2 / short_distance / 2)
        
        # Square oscillation task'ını oluştur
        sqosc_task = asyncio.create_task(
            self.square_oscillation_by_meters(
                long_distance=distance1,
                short_distance=short_distance,
                repeat_count=repeat_count,
                velocity=velocity
            )
        )
        
        # ArUco bulunana kadar veya task tamamlanana kadar bekle
        while not sqosc_task.done() and not self.pi_cam.is_found:
            # Command 1 geldi mi real-time kontrol et
            if self.landing_command_received:
                print("Landing command received during search - starting normal landing immediately!")
                await self.end_mission()
                return
            await asyncio.sleep(0.01)  # Daha hızlı kontrol
        
        # ArUco bulunduktan sonra command 1 geldi mi kontrol et
        if self.landing_command_received:
            print("Landing command received before ArUco found - starting normal landing...")
            await self.end_mission()
            return
            
        if self.pi_cam.is_found:
            # Square oscillation task'ını güvenli şekilde iptal et
            if not sqosc_task.done():
                sqosc_task.cancel()
                try:
                    await sqosc_task
                except asyncio.CancelledError:
                    print("Square oscillation task cancelled successfully")
            
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
            )
            await self.hold_mode(1.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
            print("ArUco found! Precision landing started...")
            
            # Precision landing sırasında command 1 geldi mi kontrol et
            while not self.pi_cam.is_centered and not self.mission_completed and not self.landing_command_received:
                # Command 1 geldi mi real-time kontrol et
                if self.landing_command_received:
                    print("Landing command received during precision landing - stopping and landing immediately!")
                    break
                
                x, y, z = self.pi_cam.get_averaged_position()
                print(f"DEBUG: ArUco position - X={x:.4f}, Y={y:.4f}")
                # Threshold kontrolü - OR operatörü kullan (daha esnek)
                if abs(x) > self.THRESHOLD or abs(y) > self.THRESHOLD:  # Class seviyesindeki threshold
                    print(f"Correction needed: X={x:.4f} Y={y:.4f}")
                    correction_speed = 0.5
                    move_x = x * correction_speed
                    move_y = y * correction_speed
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(move_x, move_y, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                    )
                    await asyncio.sleep(0.1)  # Daha hızlı
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                    )
                    await asyncio.sleep(0.1)  # Daha hızlı
                else:
                    print(f"ArUco centered! Position: X={x:.4f} Y={y:.4f}")
                    break
            
            # ArUco ortalandıktan sonra command 1 geldi mi kontrol et
            if self.landing_command_received:
                print("Landing command received after ArUco centered - starting normal landing...")
                await self.end_mission()
                return
                
            if self.pi_cam.is_centered:
                print("Precision landing complete. Sending XBee message...")
                lat_scaled = int(self.current_position.latitude_deg * 1000000)
                lon_scaled = int(self.current_position.longitude_deg * 1000000)
                alt_scaled = int(self.current_position.absolute_altitude_m * 10)
                simple_message = f"{lat_scaled},{lon_scaled},{alt_scaled},1"
                print(f"XBee message: {simple_message}")
                
                # Mesajı gönder
                try:
                    if hasattr(self, 'xbee_service') and self.xbee_service:
                        loop = asyncio.get_running_loop()
                        success = await loop.run_in_executor(
                            None, 
                            self.xbee_service.send_broadcast_message, 
                            simple_message, 
                            False
                        )
                        if success:
                            print("XBee message sent. Waiting for feedback...")
                            
                            # Feedback 2 gelene kadar ArUco ortalamasını sürdür
                            feedback_start = asyncio.get_event_loop().time()
                            feedback_timeout = 60  # 60 saniye timeout (daha uzun)
                            
                            while not self.feedback_received:
                                # Timeout kontrolü
                                if asyncio.get_event_loop().time() - feedback_start > feedback_timeout:
                                    print("Feedback timeout - proceeding without confirmation")
                                    break
                                
                                # ArUco pozisyonunu sürekli kontrol et ve ortala
                                x, y, z = self.pi_cam.get_averaged_position()
                                print(f"DEBUG: Feedback wait - ArUco position: X={x:.4f}, Y={y:.4f}")
                                
                                if abs(x) > self.THRESHOLD or abs(y) > self.THRESHOLD:  # Class seviyesindeki threshold
                                    print(f"Maintaining ArUco centering: X={x:.4f} Y={y:.4f}")
                                    correction_speed = 0.3  # Daha yumuşak düzeltme
                                    move_x = x * correction_speed
                                    move_y = y * correction_speed
                                    await self.drone.offboard.set_velocity_ned(
                                        VelocityNedYaw(move_x, move_y, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                                    )
                                    await asyncio.sleep(0.1)
                                    await self.drone.offboard.set_velocity_ned(
                                        VelocityNedYaw(0.0, 0.0, 0.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                                    )
                                    await asyncio.sleep(0.1)
                                else:
                                    print(f"ArUco perfectly centered, maintaining position: X={x:.4f} Y={y:.4f}")
                                
                                # Command 1 geldi mi kontrol et
                                if self.landing_command_received:
                                    print("Landing command received during feedback wait - starting normal landing!")
                                    break
                                
                                await asyncio.sleep(0.1)
                            
                            if self.feedback_received:
                                print("Feedback received! Starting landing sequence...")
                            else:
                                print("No feedback received, but proceeding...")
                            
                            self.mission_completed = True
                        else:
                            print("XBee message failed.")
                            self.mission_completed = True
                    else:
                        print("XBee service not found.")
                        self.mission_completed = True
                except Exception as e:
                    print(f"XBee error: {e}")
                    self.mission_completed = True
                
                print("Mission complete.")
                await asyncio.sleep(1)
                await self.go_forward_by_meter(5.0, 1.0, self.current_attitude.yaw_deg if self.current_attitude else 0.0)
                await self.end_mission()
            else:
                print("ArUco not centered.")
        
        # Final command 1 kontrolü
        if self.landing_command_received:
            print("Landing command received - starting normal landing...")
            await self.end_mission()
            return
        
        if self.mission_completed:
            print("Mission complete - XBee message sent.")
        else:
            print("Mission failed - ArUco not found or not centered.")
        
        # Cleanup: Camera thread'ini kontrol et
        if camera_thread.is_alive():
            print("Camera thread cleanup...")
            # Camera thread'i güvenli şekilde sonlandır
            try:
                if hasattr(self.pi_cam, 'stop_camera'):
                    self.pi_cam.stop_camera()
            except Exception as e:
                print(f"Camera cleanup error: {e}")
        
        print("Mission finished!")



