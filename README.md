# drone-core
python3 missions/waypoint_mission/multiple_waypoint_mission.py \
    --sysid 1 \
    --system_address udp://:14541 \
    --waypoints 47.397701,8.547730,10.0 47.397705,8.547740,12.0 47.397709,8.547750,10.0

python3 missions/waypoint_mission.py \
    --sysid 1 \
    --system_address udp://:14541 \
    --target_lat 47.397701 \
    --target_lon 8.547730 \
    --target_alt 10.0