#kütüphaneler
import asyncio
import serial
import math
import argparse
import time
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw, PositionNedYaw
from mavsdk.telemetry import Position
from digi.xbee.devices import XBeeDevice
#değişkenler
landed = False
msg_code=None
my_id = None
my_lat = None
my_lon = None
my_yaw = None  # Yaw değişkenini başlangıçta tanımla
mesafe = None
konum = None
lat1 = None
lon1 = None
yaw1 = None
speed1 = None
alt1 = None
my_role = None
hedef_alt = 10.0  # varsayılan hedef yükseklik
msg_code1 = None
shutdown_flag = False  # Program kapatma kontrolü için
orta_nokta = {
    "orta_lat": None,
    "orta_lon": None
}

#drone bağlantısı
async def connect_drone(system_address, sysid, port):
    """
    Drone ile bağlantı kurar.
    """
    drone = System(sysid=sysid, port=port)
    await drone.connect(system_address=system_address)
    print(f"Drone bağlantısı kuruldu: {system_address}, System ID: {sysid}, Port: {port}")
    return drone

#xbee bağlantısı
async def connect_xbee(xbee_port):
    global my_id
    """
    XBee ile bağlantı kurar.
    """
    try:
        xbee = XBeeDevice(port=xbee_port, baud_rate=57600)
        xbee.open()
        print(f"XBee bağlantısı kuruldu. Port: {xbee_port}")
        my_id = str(xbee.get_64bit_addr())[-4:]
        return xbee
    except Exception as e:
        print(f"[❌] XBee bağlantı hatası: {e}")
        return None

#telemetri verilerini alır
async def monitor_telemetry(drone):
    global my_lat, my_lon, my_yaw
    print("📡 Telemetry verileri okunuyor...")
    while True:
        try:
            # Konum verisi - async generator kullanımı
            async for pos in drone.telemetry.position():
                lat = pos.latitude_deg
                lon = pos.longitude_deg
                alt = pos.relative_altitude_m
                my_lat = lat  # Global değişkeni güncelle
                my_lon = lon
                break
                
            # Hız verisi
            async for vel in drone.telemetry.velocity_ned():
                vx, vy = vel.north_m_s, vel.east_m_s
                ground_speed = math.sqrt(vx**2 + vy**2)
                break
                
            # Yön (heading)
            async for heading in drone.telemetry.heading():
                my_yaw = heading.heading_deg  # Global değişkeni güncelle
                break
                
            print(f"""
        📍 Konum       : Lat {lat:.6f}, Lon {lon:.6f}, Alt {alt:.1f} m
        🏎️ Yer Hızı    : {ground_speed:.2f} m/s
        🧭 Heading     : {heading.heading_deg:.2f}°
        """)
        except Exception as e:
            print(f"[❌] Telemetri hatası: {e}")

        await asyncio.sleep(5)  # her 5 saniye güncelle

#xbee veri gönderme (pos verisi)
async def broadcast_pos(drone, xbee, my_id, msg_code):
    global shutdown_flag
    while not shutdown_flag:
        try:
            if xbee is None or my_id is None:
                await asyncio.sleep(5)
                continue
                
            # XBee'nin bağlantısını kontrol et
            if not xbee.is_open():
                print("⚠️ XBee bağlantısı kesildi")
                await asyncio.sleep(5)
                continue
                
            # MAVSDK'den pozisyon al - async generator kullanımı
            async for pos in drone.telemetry.position():
                lat = pos.latitude_deg
                lon = pos.longitude_deg
                alt = pos.relative_altitude_m
                break
                
            async for heading in drone.telemetry.heading():
                yaw = heading.heading_deg
                break
                
            async for velocity in drone.telemetry.velocity_ned():
                speed = (velocity.north_m_s**2 + velocity.east_m_s**2)**0.5
                break

            msg = f"POS|{my_id}|{lat:.6f},{lon:.6f},{alt:.1f},{yaw:.1f},{speed:.1f},{msg_code or 0}"

            # XBee ile yayınla
            xbee.send_data_broadcast(msg)
            print(f"[📡] Pozisyon yayınlandı: {msg}")
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                print("📡 XBee thread pool kapatıldı, broadcast durduruluyor...")
                break
        except Exception as e:
            print(f"[❌] Pozisyon yayınlanamadı: {e}")
        
        await asyncio.sleep(5)  # Her 5 saniyede bir yayınla
    print("📡 broadcast_pos sonlandırıldı")
#xbee veri gönderme (orta nokta)
async def broadcast_ort(xbee, my_id):
    global shutdown_flag
    while not shutdown_flag:
        try:
            if xbee is None or my_id is None:
                await asyncio.sleep(5)
                continue
                
            # XBee'nin bağlantısını kontrol et
            if not xbee.is_open():
                print("⚠️ XBee bağlantısı kesildi")
                await asyncio.sleep(5)
                continue
                
            if orta_nokta["orta_lat"] is not None and orta_nokta["orta_lon"] is not None:
                msg = f"ORT|{my_id}|{orta_nokta['orta_lat']:.6f},{orta_nokta['orta_lon']:.6f}"
                xbee.send_data_broadcast(msg)
                print(f"[🟡] ORT noktası yayınlandı: {msg}")
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                print("📡 XBee thread pool kapatıldı, ORT broadcast durduruluyor...")
                break
        except Exception as e:
            print(f"[❌] ORT yayın hatası: {e}")
        
        await asyncio.sleep(5)
    print("📡 broadcast_ort sonlandırıldı")

#xbee veri alma
async def xbee_veri_alma(xbee):
  global my_lat, my_lon, my_yaw, msg_code, lat1, lon1, mesafe, konum, yaw1, speed1, alt1, msg_code1, orta_nokta, shutdown_flag
  while not shutdown_flag:  
    try:
        if xbee is None:
            await asyncio.sleep(1)
            continue
            
        # XBee'nin bağlantısını kontrol et
        if not xbee.is_open():
            print("⚠️ XBee bağlantısı kesildi, yeniden deneniyor...")
            await asyncio.sleep(5)
            continue
            
        msg = xbee.read_data(1000)
        if msg:
            data = msg.data.decode()  # gelen veri örn: POS|N1|lat,lon,alt,yaw,speed,code
            print(f"📩 Gelen Veri: {data}")

            if data.startswith("POS|"):
                # POS mesajını işle
                _, drone_id, payload = data.split("|")
                parcalar = payload.split(",")  # örn: "41.1,29.1,10,5,2.5"
                lat1 = float(parcalar[0])
                lon1 = float(parcalar[1])
                alt1 = float(parcalar[2])
                yaw1 = float(parcalar[3])
                speed1 = float(parcalar[4])
                msg_code1 = parcalar[5]
                
                if my_lat is not None and my_lon is not None:
                    mesafe, konum = await hesapla_mesafe_yon(my_lat, my_lon, my_yaw or 0, lat1, lon1)
                    orta_lat, orta_lon = hesapla_orta_nokta(lat1, lon1, my_lat, my_lon)
                    orta_nokta["orta_lat"] = orta_lat
                    orta_nokta["orta_lon"] = orta_lon
                
                print(f"🛰️ {drone_id} → POS: ({lat1}, {lon1}, {alt1}) | YAW: {yaw1} | SPEED: {speed1} | msg_code {msg_code1}")
                print(f"🛰️ {drone_id} → Diğer drone: ({lat1}, {lon1}, {alt1}) noktasında")

            elif data.startswith("ORT|"):
                # ORT mesajını işle
                _, drone_id, payload = data.split("|")
                ort_lat, ort_lon = map(float, payload.split(","))

                print(f"📍 {drone_id} → ORTA NOKTA: ({ort_lat}, {ort_lon})")
                
                # İstersen ortak noktayı hafızaya al
                orta_nokta["orta_lat"] = ort_lat
                orta_nokta["orta_lon"] = ort_lon

            elif data.startswith("GUI|"): 
                #GUI mesajını işle
                _, msg_type, payload = data.split("|")
                msg_code = int(msg_type)
                print(f"🖥️ GUI Mesajı: {msg_type} | Payload: {payload}")   

            else:
                print("⚠️ Tanınmayan mesaj tipi!")
                
    except RuntimeError as e:
        if "cannot schedule new futures after shutdown" in str(e):
            print("📡 XBee thread pool kapatıldı, çıkılıyor...")
            break
    except Exception as e:
        print(f"[❌] XBee veri alma hatası: {e}")
        
    await asyncio.sleep(0.1)
  print("📡 xbee_veri_alma sonlandırıldı")

#fonksiyonlar
#mesafe hesaplama
async def hesapla_mesafe_yon(my_lat, my_lon, my_yaw_deg, lat1, lon1):
    global  mesafe, konum, my_role


    """
    Diğer drone ile arandaki mesafeyi ve yönsel konumunu (sağ/sol) döndürür.
    """

    # 🔹 Dünya düzlemsel varsayımıyla mesafe (basit havacılık için yeterli)
    R = 6371000  # dünya yarıçapı (metre)
    
    # Farkları radian cinsine çevir
    dlat = math.radians(lat1 - my_lat)
    dlon = math.radians(lon1 - my_lon)
    
    # Ortalama enlemle çarp (doğruluğu artırmak için)
    avg_lat = math.radians((my_lat + lat1) / 2)
    dx = R * dlon * math.cos(avg_lat)
    dy = R * dlat

    # 🔹 Mesafe
    mesafe = math.sqrt(dx**2 + dy**2)

    # 🔹 Açı farkı (bağıl yön)
    angle_to_other = math.degrees(math.atan2(dx, dy))  # kuzey referanslı
    yaw_fark = (angle_to_other - my_yaw_deg + 360) % 360

    if yaw_fark > 315 or yaw_fark < 45:
        konum = "önünde"
        my_role = "sağ"

    elif 45 <= yaw_fark < 135:
        konum = "sağında"
        my_role = "sol"
    elif 135 <= yaw_fark < 225:
        konum = "arkanda"
        my_role = "sol"
    else:
        konum = "solunda"
        my_role = "sağ"

    print(f"📏 Aradaki mesafe: {mesafe:.2f} m, diğer drone {konum}")
    
    return mesafe, konum

#orta nokta hesaplama
def hesapla_orta_nokta(lat1, lon1, my_lat, my_lon): 
    global  orta_nokta

    """
    İki konum (lat/lon) arasındaki ağırlık merkezi/orta noktayı (lat/lon) döndürür.
    Dünya yüzeyi düz kabul edilir.
    """

    # Dünya yarıçapı (metre)
    R = 6371000

    # Ortalama enlemi radian cinsinden al
    avg_lat = math.radians((lat1 + my_lat) / 2)

    # x ve y doğrultusunda farklar (metre cinsinden)
    dx = R * math.radians(my_lon - lon1) * math.cos(avg_lat)
    dy = R * math.radians(my_lat - lat1)

    # Orta noktanın x/y yer değiştirmesi (yarı mesafe)
    dx_orta = dx / 2
    dy_orta = dy / 2

    # İlk konumdan bu fark kadar ilerleyerek orta noktayı bul
    orta_lat = lat1 + math.degrees(dy_orta / R)
    orta_lon = lon1 + math.degrees(dx_orta / (R * math.cos(avg_lat)))
    
    print(f"🟡 Orta Nokta → LAT: {orta_lat:.6f}, LON: {orta_lon:.6f}")

    return orta_lat, orta_lon

# Orta nokta değişkeni( xbee ile paylaşılacak)
def guncelle_orta_nokta(lat1, lon1, my_lat, my_lon):
    orta_lat, orta_lon = hesapla_orta_nokta(lat1, lon1, my_lat, my_lon)
    orta_nokta["orta_lat"] = orta_lat
    orta_nokta["orta_lon"] = orta_lon

#formasyon için yeni hedef hesabı
def hedef_nokta_hesapla(orta_lat, orta_lon, rol, msg_code):
    """
    Orta noktaya ve role göre yeni hedef noktasını hesaplar.
    rol: 'sag' veya 'sol'
    msg_code: 1 (yukarı/aşağı), 2 (sağ/sol formasyon)
    """

    # Sabit: 5 metre offset → derece cinsine çevrilmesi gerekiyor
    metre_offset = 5

    # Dünya yarıçapı
    R = 6371000  # metre

    # Enlemde 5 metre ≈ derece karşılığı
    delta_lat = (metre_offset / R) * (180 / math.pi)

    # Boylamda 5 metre ≈ derece karşılığı (enleme bağlı!)
    delta_lon = (metre_offset / (R * math.cos(math.radians(orta_lat)))) * (180 / math.pi)

    yeni_lat = orta_lat
    yeni_lon = orta_lon

    if msg_code == 1:
        # Yukarı - Aşağı (enlem değişir)
        if rol == "sag":
            yeni_lat = orta_lat - delta_lat  # güneye
        elif rol == "sol":
            yeni_lat = orta_lat + delta_lat  # kuzeye

    elif msg_code == 2:
        # Sağ - Sol (boylam değişir)
        if rol == "sag":
            yeni_lon = orta_lon - delta_lon  # batıya
        elif rol == "sol":
            yeni_lon = orta_lon + delta_lon  # doğuya

    print(f"🎯 Yeni hedef nokta: LAT: {yeni_lat:.6f}, LON: {yeni_lon:.6f}")
    return yeni_lat, yeni_lon

#git noktaya 
async def git_noktaya(drone, yeni_lat, yeni_lon, hedef_alt=10.0, tolerans=0.5):
    """
    Drone'u verilen yeni_lat ve yeni_lon koordinatlarına götürür.
    Hedefe 0.5 metre içinde ulaşınca tamamlanmış sayılır.
    """
    print(f"🚀 Yeni noktaya gidiliyor: {yeni_lat}, {yeni_lon}")
    await drone.action.goto_location(yeni_lat, yeni_lon, hedef_alt, 0)

    # Konuma yaklaşana kadar bekle
    while True:
        try:
            async for pos in drone.telemetry.position():
                lat = pos.latitude_deg
                lon = pos.longitude_deg
                alt = pos.relative_altitude_m
                break

            # Haversine ile mesafe hesapla
            mesafe = haversine(lat, lon, yeni_lat, yeni_lon)
            if mesafe <= tolerans:
                print("✅ Hedef noktaya ulaşıldı.")
                break
            else:
                print(f"📍 Mesafe hedefe: {mesafe:.2f} m")
        except Exception as e:
            print(f"[❌] Konum alma hatası: {e}")
            
        await asyncio.sleep(1)

#noktaya kalan mesafeyi hesapla
def haversine(lat1, lon1, my_lat, my_lon):
    
    """
    İki GPS noktası arasındaki mesafeyi (metre) hesaplar.
    """
    R = 6371000  # Dünya yarıçapı (metre)
    phi1 = math.radians(lat1)
    phi2 = math.radians(my_lat)
    dphi = math.radians(my_lat - lat1)
    dlambda = math.radians(my_lon - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

#arm and takeoff
async def arm_and_takeoff(drone, msg_code, hedef_alt=10.0):
    """
    Drone'u offboard moda geçirip arm eder ve hedef irtifaya yükselmesini bekler.
    """
    if msg_code != 0:
        print("ℹ️ MSG_CODE 0 değil → arm_and_takeoff çalıştırılmadı.")
        return

    print("🔧 Offboard başlatılıyor...")

    # Dummy velocity verisi göndererek offboard mod için hazırlık
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(north_m_s=0.0, east_m_s=0.0, down_m_s=0.0, yaw_deg=0.0)
    )

    try:
        await drone.offboard.start()
        print("✅ Offboard moda geçildi.")
    except OffboardError as e:
        print(f"[❌] Offboard başlatılamadı: {e}")
        return

    # Arm et
    print("🔐 Drone arm ediliyor...")
    await drone.action.arm()
    print("✅ Drone arm edildi.")

    # Yüksekliğe çık
    await drone.action.set_takeoff_altitude(hedef_alt)
    await drone.action.takeoff()
    print(f"🚁 Drone kalktı, hedef irtifa: {hedef_alt} m")

    # Yüksekliğe ulaşana kadar bekle
    while True:
        try:
            async for pos in drone.telemetry.position():
                alt = pos.relative_altitude_m
                print(f"📶 Yükseklik: {alt:.2f} m")
                break

            if abs(alt - hedef_alt) < 0.5:
                print("✅ Hedef yüksekliğe ulaşıldı → Beklemeye geçiliyor.")
                break
        except Exception as e:
            print(f"[❌] Yükseklik kontrolü hatası: {e}")

        await asyncio.sleep(1)

#iniş fonksiyonu
async def land_drone(drone):
    global landed
    landed = True
    """
    Drone'u güvenli şekilde indirir.
    Bu fonksiyon offboard uçuş sonrası çağrılabilir.
    """
    try:
        print("⬇️ Drone iniş yapıyor...")
        await drone.action.land()
        print("✅ İniş başarılı.")
    except Exception as e:
        print(f"[❌] İniş başarısız: {e}")


#görev
async def main(args):
    global drone, xbee, my_lat, my_lon, my_yaw

    # Drone ve XBee bağlantılarını kur
    drone = await connect_drone(args.system_address, args.sysid, args.port)
    xbee = await connect_xbee(args.xbee_port)    # Telemetri verilerini oku
    asyncio.create_task(monitor_telemetry(drone))
    # XBee'den veri al
    asyncio.create_task(xbee_veri_alma(xbee))
    # Pozisyonu yayınla
    asyncio.create_task(broadcast_pos(drone, xbee, my_id, msg_code))
    # Orta nokta yayınla
    asyncio.create_task(broadcast_ort(xbee, my_id))
    
    print("🖥️ GUI'den ilk komutun (msg_code) gelmesi bekleniyor...")
    while msg_code is None: # msg_code hala None ise beklemeye devam et
        await asyncio.sleep(1) # Her saniye kontrol et, bu sırada diğer arka plan görevleri çalışmaya devam eder
    print(f"✅ İlk komut alındı: msg_code = {msg_code}")

    # Drone'u arm et ve kalkış yap
    if msg_code == 0:
        await arm_and_takeoff(drone, msg_code, hedef_alt)
    # Formasyona geçiş    
    elif msg_code == 1:#doğuya bakan çizgi formasyonu
        print("🟢 Doğuya bakan çizgi formasyonu → Hedef nokta hesaplanıyor...")
        if orta_nokta["orta_lat"] is not None and orta_nokta["orta_lon"] is not None and my_role is not None:
            yeni_lat, yeni_lon = hedef_nokta_hesapla(orta_nokta["orta_lat"], orta_nokta["orta_lon"], my_role, msg_code)
            await git_noktaya(drone, yeni_lat, yeni_lon, hedef_alt=10, tolerans=0.5)
        else:
            print("⚠️ Orta nokta veya rol bilgisi henüz mevcut değil!")
    elif msg_code == 2:  #kuzeye bakan çizgi formasyonu
        print("🟢 Kuzeye bakan çizgi formasyonu → Hedef nokta hesaplanıyor...")
        if orta_nokta["orta_lat"] is not None and orta_nokta["orta_lon"] is not None and my_role is not None:
            yeni_lat, yeni_lon = hedef_nokta_hesapla(orta_nokta["orta_lat"], orta_nokta["orta_lon"], my_role, msg_code)
            await git_noktaya(drone, yeni_lat, yeni_lon, hedef_alt=10, tolerans=0.5)
        else:
            print("⚠️ Orta nokta veya rol bilgisi henüz mevcut değil!")
    elif msg_code == 3:#iniş yap
        print("🛬 İniş yapılıyor...")
        await land_drone(drone)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drone formation flight control")
    parser.add_argument("--sysid", type=int, default=1, help="Drone system ID (default: 1)")
    parser.add_argument("--port", type=int, default=50051, help="MAVSDK server port (default: 50051)")
    parser.add_argument("--system_address", type=str, default="udp://:14540", help="MAVSDK system address (default: udp://:14540)")
    parser.add_argument("--xbee_port", type=str, default="/dev/ttyUSB0", help="XBee port (default: /dev/ttyUSB0)")
    
    args = parser.parse_args()
    
    # Global my_id değişkenini argparse'dan gelen sysid ile ayarla
    my_id = args.sysid
    
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("Program sonlandırılıyor...")
        shutdown_flag = True  # Tüm görevlere dur sinyali gönder
        
        # Kısa bir süre bekle ki görevler temizlensin
        time.sleep(1)
        
        if 'drone' in globals() and drone:
            try:
                asyncio.run(land_drone(drone))
            except Exception as e:
                print(f"[❌] Drone iniş hatası: {e}")
        print("Drone bağlantısı kesildi.")
        
        if 'xbee' in globals() and xbee:
            try:
                if xbee.is_open():
                    xbee.close()
                print("XBee bağlantısı kapatıldı.")
            except Exception as e:
                print(f"[❌] XBee kapatma hatası: {e}")
        print("Tüm bağlantılar kapatıldı.")
    except Exception as e:
        print(f"[❌] Program hatası: {e}")
        shutdown_flag = True
        if 'xbee' in globals() and xbee:
            try:
                if xbee.is_open():
                    xbee.close()
            except:
                pass
      