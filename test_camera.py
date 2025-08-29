def find_middle_of_two_points(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
        """
        Find the geographical midpoint between two GPS coordinates.
        Returns: (mid_lat, mid_lon)
        """
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        return mid_lat, mid_lon


print(find_middle_of_two_points(40.7445114, 30.3380595,40.7440583, 30.3381680))