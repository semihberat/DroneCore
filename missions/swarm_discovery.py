#Drone Core Libraries
import asyncio
import math
from mavsdk.offboard import (PositionNedYaw, VelocityNedYaw)
#System Libraries
import argparse
import sys
import os
#Custom Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.offboard_control import OffboardControl


from mavsdk.camera import (CameraError, Mode)
from mavsdk import System


class SwarmDiscoverySquare(OffboardControl):
    def __init__(self):
        super().__init__()
        self.home_position = None  # ✅ Sabit home referansı
