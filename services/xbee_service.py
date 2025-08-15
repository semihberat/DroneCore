import json
import threading
import time
import logging
import serial
import functools
import sys
from queue import Queue, Full

from digi.xbee.devices import XBeeDevice
from digi.xbee.exception import XBeeException, TransmitException, TimeoutException, InvalidOperatingModeException

logging.basicConfig(level=logging.INFO, format='[%(asctime)s - %(levelname)s]:\n\t%(message)s')

def check_connected(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.device.is_open():
            logging.error("XBee cihazı açık değil.")
            return None
        return func(self, *args, **kwargs)
    return wrapper

class XbeeService:
    def __init__(self, message_received_callback, port="/dev/ttyUSB0", baudrate=57600, max_queue_size=20):
        self.port = port
        self.baudrate = baudrate
        self.device = XBeeDevice(port, baudrate)
        self.address = self.device.get_16bit_addr()
        self.message_received_callback = message_received_callback
        self.recent_messages = Queue(maxsize=max_queue_size)
        self.queue_stop_event = threading.Event()
        # self.configure_xbee_api_mode()
        self.queue_thread = threading.Thread(target=self.queue_processor, daemon=True)
        if self.message_received_callback:
            self.queue_thread.start()
            logging.warning("Mesaj kuyruğu işleme thread'i başlatıldı.")
        else:
            logging.warning("Mesaj alındığında çağrılacak callback fonksiyonu belirtilmemiş.")

    
    def queue_processor(self):
        """
        Mesaj kuyruğundan mesajları işleyen thread fonksiyonu.
        """
        while not self.queue_stop_event.is_set():
            if self.recent_messages.empty():
                time.sleep(0.1)
                continue
            try:
                message = self.recent_messages.get(timeout=0.5)
                logging.info(f"Mesaj işleniyor: {message}")
                
                # Processed message dictionary için özel handler
                self.handle_processed_message(message)
                logging.info("Mesaj başarıyla işlendi.")
                self.recent_messages.task_done()
            except Exception as e:
                logging.error(f"Mesaj işlenirken hata oluştu: {e}")
                if not self.recent_messages.empty():
                    self.recent_messages.task_done()
    
    def handle_processed_message(self, message_dict):
        """
        İşlenmiş mesaj dictionary'sini işleyen fonksiyon.
        message_dict format: {"sender": "...", "isBroadcast": True, "data": "...", "timestamp": ...}
        """
        try:
            sender = message_dict.get("sender", "Unknown")
            is_broadcast = message_dict.get("isBroadcast", False)
            data = message_dict.get("data", "")
            timestamp = message_dict.get("timestamp", 0)
            
            logging.info(f"📨 XBee Mesajı Alındı:")
            logging.info(f"   Gönderen: {sender}")
            logging.info(f"   Broadcast: {is_broadcast}")
            logging.info(f"   Veri: {data}")
            logging.info(f"   Zaman: {timestamp}")
            
            # Eğer özel bir callback varsa ve farklıysa onu da çağır
            if (hasattr(self, 'custom_message_handler') and 
                callable(self.custom_message_handler)):
                self.custom_message_handler(message_dict)
                
        except Exception as e:
            logging.error(f"İşlenmiş mesaj handle edilirken hata: {e}")
    
    def set_custom_message_handler(self, handler_func):
        """
        Özel mesaj işleyici fonksiyonu ayarlar.
        Bu fonksiyon işlenmiş mesaj dictionary'si alır.
        """
        self.custom_message_handler = handler_func
        logging.info("Özel mesaj işleyici ayarlandı.")
    
    def default_message_received_callback(self, message):
        """
        Xbee'den gelen mesajları işleyen callback fonksiyonu.
        """
        try:
            if not self.queue_thread.is_alive() and self.message_received_callback:
                self.queue_thread.start()
            message_data = message.data.decode('utf-8')
            sender = int.from_bytes(message.remote_device.get_64bit_addr().address, "big")
            message_full = {
                "sender": f"{sender:016X}",
                "isBroadcast": message.is_broadcast,
                "data": message_data,
                "timestamp": message.timestamp
            }
            logging.debug(f"Mesaj alındı: {message_full}")
            try:
                self.recent_messages.put_nowait(message_full)
                logging.info("Mesaj kuyruğa eklendi")
            except Full:
                logging.error(f"Mesaj kuyruğa eklenemedi, kuyruk dolu.")
                # Kuyruk doluysa en eski mesajı sil ve yeni mesajı ekle
                logging.info("En eski mesaj siliniyor ve yeni mesaj ekleniyor.")
                self.recent_messages.get_nowait()
                self.recent_messages.put_nowait(message_full)
        except Exception as e:
            logging.error(f"Mesaj işlenirken hata oluştu: {e}")
    
    def configure_xbee_api_mode(self):
        """
        XBee cihazını API moduna geçirir.
        """
        try:
            logging.info("XBee cihazı API moduna geçiriliyor...")
            # Serial bağlantı kur
            ser = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(1)  # Bağlantının stabilleşmesi için bekle
            # Command moduna geç
            ser.write(b'+++')
            time.sleep(2)
            response = ser.read(ser.in_waiting)
            logging.info(f"Command mode response: {response}")
            # API mode 1'e geç (AP=1)
            ser.write(b'ATAP1\r')
            time.sleep(0.5)
            response = ser.read(ser.in_waiting)
            logging.info(f"API mode response: {response}")
            # Ayarları kaydet
            ser.write(b'ATWR\r')
            time.sleep(0.5)
            response = ser.read(ser.in_waiting)
            logging.info(f"Write response: {response}")
            # Command modundan çık
            ser.write(b'ATCN\r')
            time.sleep(0.5)
            ser.close()
            logging.info("XBee başarıyla API moduna geçirildi.")
            return True
            
        except Exception as e:
            logging.error(f"XBee API moduna geçirilirken hata: {e}")
            return False

    def listen(self):
        """
        Xbee mesajlarını dinler ve mesaj gelince callback fonksiyonunu çağırır.
        """
        try:
            if not self.device.is_open():
                self.device.open()
            self.device.add_data_received_callback(self.default_message_received_callback)
            logging.info("XBee dinleniyor...")
        except Exception as e:
            logging.error(f"XBee açılamadı: {e}")
            raise
    
    def construct_message(self, data):
        """
        Verilen mesajı JSON formatına çevirir.
        """
        message = {
            "i": self.address,
            "d": data,
            "t": int(time.time()*1000)
        }
        logging.debug(f"Mesaj yapılandırıldı.")
        return json.dumps(message, ensure_ascii=False).replace("\n", "").replace(" ", "").encode('utf-8')
    
    @check_connected
    def send_broadcast_message(self, data, construct_message=False):
        """
        Xbee üzerinden veri yayınlar (broadcast eder).
        """
        try:
            if construct_message:
                message = self.construct_message(data)
            else:
                message = data
            logging.debug(f"Broadcast mesajı yapılandırıldı: {message}")
            self.device.send_data_broadcast(message)
            logging.info(f"Mesaj gönderildi:\n Mesaj: {data}\nAlıcı: Broadcast")
            return True
        except XBeeException as e:
            logging.error(f"XBee Hatası: {e}")
            return False
        except TimeoutException as e:
            logging.error(f"Zaman aşımı hatası: {e}")
            return False
        except TransmitException as e:
            logging.error(f"Transmit hatası: {e}")
            return False
        except InvalidOperatingModeException as e:
            logging.error(f"Geçersiz çalışma modu hatası: {e}")
            return False
    
    @check_connected
    def send_private_message(self, receiver, data):
        """
        Xbee üzerinden bir alıcıya veri gönderir.
        """
        message = self.construct_message(data)
        try:
            self.device.send_data(receiver, message)
            logging.info(f"Mesaj gönderildi:\n Mesaj: {data}\nAlıcı: {receiver}")
            return True
        except Exception as e:
            logging.error(f"Mesaj gönderilemedi: {e}")
            return False
    
    def close(self):
        """
        XBee cihazını kapatır ve mesaj kuyruğu işleme thread'ini durdurur.
        """
        if self.device.is_open():
            self.device.close()
            logging.info("XBee kapatıldı.")
            self.queue_stop_event.set()
            logging.info("Mesaj kuyruğu işleme thread'i durduruldu.")
        else:
            logging.warning("XBee zaten kapalı.")
            
def main():
    """
    XBeeController test fonksiyonu.
    Bu fonksiyon, XBee cihazını başlatır, mesaj gönderir ve dinler.
    """
    xbee = XbeeService(message_received_callback=XbeeService.default_message_received_callback, port = "/dev/ttyUSB1", baudrate=57600, max_queue_size=100)
    xbee.listen()
    
    # Test mesajı gönder
    try:
        while True:
            # xbee.send_broadcast_message("oto mesaj", construct_message=True)
            time.sleep(1)
    except KeyboardInterrupt:
        xbee.close()

if __name__ == "__main__":
    logging.info("XBeeController başlatılıyor...")
    main()
    logging.info("XBeeController testinin tüm adımları tamamlandı, çıkılıyor.")
    sys.exit(0)