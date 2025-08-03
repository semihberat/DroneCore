import subprocess
import time

drones = [
    {"sysid": 1, "system_address": "udp://:14541", "target_lat": 47.397701, "target_lon": 8.547730, "target_alt": 10.0},
    {"sysid": 2, "system_address": "udp://:14542", "target_lat": 47.397705, "target_lon": 8.547740, "target_alt": 10.0},
    {"sysid": 3, "system_address": "udp://:14543", "target_lat": 47.397709, "target_lon": 8.547750, "target_alt": 10.0},
]

for drone in drones:
    cmd = (
        f"python3 missions/multiple_waypoint_mission.py "
        f"--sysid {drone['sysid']} "
        f"--system_address {drone['system_address']} "
        f"--target_lat {drone['target_lat']} "
        f"--target_lon {drone['target_lon']} "
        f"--target_alt {drone['target_alt']}"
    )
    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c", f"{cmd}; exec bash"
    ])
    time.sleep(2)  # Her drone'u 2 saniye arayla başlat

# Not: Tüm terminaller kendi başına çalışır, ana script beklemez.