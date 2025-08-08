import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl

class InitialYawTest(OffboardControl):
    def __init__(self):
        super().__init__()

async def test_initial_yaw():
    test = InitialYawTest()
    
    drone_port = input("Drone portu (udp://:14540): ") or "udp://:14540"
    
    await test.connect(system_address=drone_port)
    await test.initialize_mission()
    
    # Home yaw açısını yazdır
    if test.home_position:
        print(f"🧭 Home Yaw: {test.home_position['yaw']:.1f}°")
    
    # Kısa süre o yawda kal
    await test.hold_mode(10.0, test.home_position['yaw'])
    
    await test.end_mission()

if __name__ == "__main__":
    asyncio.run(test_initial_yaw())