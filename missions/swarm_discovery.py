import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl
from optimization.distance_calculation import CalculateDistance
from mavsdk.offboard import VelocityNedYaw

class SwarmDiscovery(OffboardControl):
    def __init__(self):
        super().__init__()
            
    async def square_oscillation_by_meters(self, forward_length=50.0, side_length=20.0, altitude=10.0, velocity=5.0):
        """Kare dalga oscillation - 10 döngü"""
        print("🔄 Square Oscillation başlıyor...")
        
        current_yaw = self.home_position["yaw"]
        
    
        # 1. İleri git (başlangıç yönünde)
   
        await self.go_forward_by_meter(forward_length, altitude, velocity, current_yaw)
        await self.go_forward_by_meter(side_length, altitude, velocity, current_yaw + 90.0)
        await self.go_forward_by_meter(forward_length, altitude, velocity, current_yaw + 180.0)
        await self.go_forward_by_meter(side_length, altitude, velocity, current_yaw + 90.0)
        await self.go_forward_by_meter(forward_length, altitude, velocity, current_yaw + 0.0)

        await asyncio.sleep(1)  # Döngüler arası kısa bekleme
        
        print("✅ Square Oscillation tamamlandı!")
        
async def test_initial_yaw():
    swarmdiscovery = SwarmDiscovery()
    
    drone_port = input("Drone portu (udp://:14540): ") or "udp://:14540"
    
    await swarmdiscovery.connect(system_address=drone_port)
    await swarmdiscovery.initialize_mission()
    
    await swarmdiscovery.square_oscillation_by_meters()

    await swarmdiscovery.end_mission()

if __name__ == "__main__":
    asyncio.run(test_initial_yaw())