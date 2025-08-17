import math
import cv2
import numpy as np

class DroneVisionCalculator:
    """
    Calculates camera ground coverage and pixel-to-real-world conversions for drones.
    """
    def __init__(self, camera_fov_horizontal: float = 90, camera_fov_vertical: float = 60, 
                 image_width: int = 1920, image_height: int = 1080):
        self.fov_h: float = math.radians(camera_fov_horizontal)
        self.fov_v: float = math.radians(camera_fov_vertical)
        self.image_width: int = image_width
        self.image_height: int = image_height

    def calculate_ground_coverage(self, altitude: float) -> dict:
        """
        Calculate ground coverage area and GSD at given altitude.
        Returns: dict with width, height, area, meters per pixel (h/v)
        """
        ground_width = 2 * altitude * math.tan(self.fov_h / 2)
        ground_height = 2 * altitude * math.tan(self.fov_v / 2)
        total_area = ground_width * ground_height
        meters_per_pixel_h = ground_width / self.image_width
        meters_per_pixel_v = ground_height / self.image_height
        return {
            'altitude_m': altitude,
            'width_m': ground_width,
            'height_m': ground_height,
            'area_m2': total_area,
            'meters_per_pixel_h': meters_per_pixel_h,
            'meters_per_pixel_v': meters_per_pixel_v
        }

    def print_coverage_info(self, altitude: float) -> dict:
        """
        Print ground coverage info for given altitude.
        """
        coverage = self.calculate_ground_coverage(altitude)
        print(f"Coverage at {altitude}m: width={coverage['width_m']:.2f}m, height={coverage['height_m']:.2f}m, area={coverage['area_m2']:.2f}m²")
        print(f"GSD: horizontal={coverage['meters_per_pixel_h']:.4f}m/pixel, vertical={coverage['meters_per_pixel_v']:.4f}m/pixel")
        return coverage

    def pixel_to_real_world(self, pixel_x: int, pixel_y: int, altitude: float) -> tuple[float, float]:
        """
        Convert pixel coordinates to real-world meters (centered at image center).
        Returns: (real_x_m, real_y_m)
        """
        coverage = self.calculate_ground_coverage(altitude)
        real_x = pixel_x * coverage['meters_per_pixel_h']
        real_y = pixel_y * coverage['meters_per_pixel_v']
        return real_x, real_y

    def real_world_to_pixel(self, real_x: float, real_y: float, altitude: float) -> tuple[int, int]:
        """
        Convert real-world meters to pixel coordinates.
        Returns: (pixel_x, pixel_y)
        """
        coverage = self.calculate_ground_coverage(altitude)
        pixel_x = real_x / coverage['meters_per_pixel_h']
        pixel_y = real_y / coverage['meters_per_pixel_v']
        return int(pixel_x), int(pixel_y)

