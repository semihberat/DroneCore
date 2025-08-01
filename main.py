from mavsdk.offboard import VelocityNedYaw
import math

class OffboardControl(DroneConnection):
    # ...existing code...

    async def goto_with_velocity(self, target_lat, target_lon, target_alt, velocity_m_s):
        await self.drone.offboard.start()
        print("Offboard mode started")

        while True:
            # Mevcut konum
            pos = self.current_position
            if pos is None:
                await asyncio.sleep(0.1)
                continue

            # Hedefe olan mesafe ve yönü hesapla (basit örnek, NED frame için)
            # Burada daha hassas bir dönüşüm gerekebilir!
            north = (target_lat - pos.latitude_deg) * 111000  # yaklaşık metre
            east = (target_lon - pos.longitude_deg) * 111000 * math.cos(math.radians(pos.latitude_deg))
            down = pos.absolute_altitude_m - target_alt

            distance = math.sqrt(north**2 + east**2 + down**2)
            if distance < 1.0:  # 1 metreye geldiğinde dur
                break

            # Normalize et ve hız vektörü oluştur
            norm = math.sqrt(north**2 + east**2 + down**2)
            north_v = velocity_m_s * north / norm
            east_v = velocity_m_s * east / norm
            down_v = velocity_m_s * down / norm

            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(north_v, east_v, down_v, 0.0)
            )
            await asyncio.sleep(0.1)  # 10 Hz

        await self.drone.offboard.stop()
        print("Reached target and stopped offboard mode.")

    async def run_mission(self):
        await self.connect()
        self._position_task = asyncio.ensure_future(self.update_position())
        await asyncio.sleep(2)  # Konumun güncellenmesini bekle

        # Örnek: Hedef koordinat ve hız
        await self.goto_with_velocity(target_lat=40.123456, target_lon=29.123456, target_alt=50.0, velocity_m_s=3.0)

# ...existing code...