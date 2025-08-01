import math

def get_lat_lon_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Dünya yarıçapı (metre)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    # Yönlü kuzey-güney mesafesi
    north = dLat * R
    # Yönlü doğu-batı mesafesi (enlem ortalaması ile düzeltme)
    east = dLon * R * math.cos(math.radians((lat1 + lat2) / 2))
    return north, east

def test():
    lat1 = 52.2296756
    lon1 = 21.0122287
    lat2 = 41.8919300
    lon2 = 12.5113300

    north, east = get_lat_lon_distance(lat1, lon1, lat2, lon2)
    print(f"North (latitude) distance: {north:.2f} meters")
    print(f"East (longitude) distance: {east:.2f} meters")

test()