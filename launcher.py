import subprocess

# Her drone için sysid ve system_address belirle
drones = [
    {"sysid": 1, "system_address": "udp://:14541"},
    {"sysid": 2, "system_address": "udp://:14542"},
    {"sysid": 3, "system_address": "udp://:14543"},
]

processes = []

for drone in drones:
    cmd = [
        "python3",
        "main.py",
        "--sysid", str(drone["sysid"]),
        "--system_address", drone["system_address"]
    ]
    # Her drone için ayrı bir process başlat
    p = subprocess.Popen(cmd)
    processes.append(p)

# Tüm processlerin bitmesini bekle
for p in processes:
    p.wait()