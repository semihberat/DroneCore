#!/usr/bin/env python3
"""
XBee Service Test Suite
XBee haberleşme kapasitesi ve performans testi
"""

import sys
import os
import time
import threading
import json
import random
import string
from datetime import datetime

# Path ayarları
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.xbee_service import XBeeController

class XBeeTestSuite:
    def __init__(self):
        self.received_messages = []
        self.sent_messages = []
        self.test_start_time = None
        self.test_duration = 60  # Test süresi (saniye)
        self.max_message_size = 100  # Maksimum mesaj boyutu (bytes)
        self.message_interval = 0.1  # Mesajlar arası süre (saniye)
        self.lock = threading.Lock()
        
    def message_callback(self, message):
        """Gelen mesajları işleyen callback"""
        with self.lock:
            message['received_time'] = time.time()
            self.received_messages.append(message)
            print(f"📨 Mesaj alındı: {message['sender'][:8]}... | Data: {message['data'][:20]}...")
    
    def generate_test_data(self, size_bytes):
        """Test için rastgele veri üretir"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=size_bytes))
    
    def test_connection(self, xbee):
        """XBee bağlantı testi"""
        print("\n🔧 XBee Bağlantı Testi")
        print("=" * 50)
        
        try:
            xbee.listen()
            print("✅ XBee başarıyla başlatıldı")
            print(f"📍 XBee Adresi: {xbee.address}")
            return True
        except Exception as e:
            print(f"❌ XBee bağlantı hatası: {e}")
            return False
    
    def test_basic_messaging(self, xbee):
        """Temel mesajlaşma testi"""
        print("\n📨 Temel Mesajlaşma Testi")
        print("=" * 50)
        
        test_messages = [
            "Merhaba XBee!",
            "Test mesajı 123",
            "🚁 Drone koordinatları: 40.7128, -74.0060",
            json.dumps({"type": "telemetry", "altitude": 100, "battery": 85}),
            "A" * 50  # 50 karakter uzun mesaj
        ]
        
        success_count = 0
        for i, msg in enumerate(test_messages):
            print(f"📤 Mesaj {i+1} gönderiliyor: {msg[:30]}...")
            
            start_time = time.time()
            result = xbee.send_broadcast_message(msg, construct_message=True)
            end_time = time.time()
            
            if result:
                success_count += 1
                send_time = (end_time - start_time) * 1000  # ms
                self.sent_messages.append({
                    'message': msg,
                    'size': len(msg.encode('utf-8')),
                    'send_time': send_time,
                    'timestamp': start_time
                })
                print(f"✅ Başarılı (Süre: {send_time:.2f}ms)")
            else:
                print(f"❌ Başarısız")
            
            time.sleep(0.5)  # Mesajlar arası bekleme
        
        print(f"\n📊 Sonuç: {success_count}/{len(test_messages)} mesaj başarılı")
        return success_count == len(test_messages)
    
    def test_throughput(self, xbee):
        """Veri aktarım hızı testi"""
        print("\n🚀 Veri Aktarım Hızı Testi")
        print("=" * 50)
        
        # Farklı boyutlarda mesajlar test et
        message_sizes = [10, 25, 50, 75, 100]  # bytes
        
        for size in message_sizes:
            print(f"\n📏 {size} byte mesaj testi...")
            
            test_data = self.generate_test_data(size)
            success_count = 0
            total_time = 0
            test_count = 10
            
            for i in range(test_count):
                start_time = time.time()
                result = xbee.send_broadcast_message(test_data, construct_message=True)
                end_time = time.time()
                
                if result:
                    success_count += 1
                    send_time = (end_time - start_time) * 1000
                    total_time += send_time
                
                time.sleep(0.1)  # Kısa bekleme
            
            if success_count > 0:
                avg_time = total_time / success_count
                throughput = (size * success_count) / (total_time / 1000)  # bytes/second
                print(f"✅ Başarı Oranı: {success_count}/{test_count}")
                print(f"⏱️  Ortalama Süre: {avg_time:.2f}ms")
                print(f"🌊 Throughput: {throughput:.2f} bytes/sec")
            else:
                print(f"❌ Hiç mesaj gönderilemedi")
    
    def test_stress(self, xbee):
        """Stres testi - yoğun mesajlaşma"""
        print("\n💪 Stres Testi (30 saniye)")
        print("=" * 50)
        
        start_time = time.time()
        message_count = 0
        error_count = 0
        
        while time.time() - start_time < 30:  # 30 saniye test
            test_data = f"Stres_mesaji_{message_count}_{int(time.time())}"
            
            result = xbee.send_broadcast_message(test_data, construct_message=True)
            if result:
                message_count += 1
            else:
                error_count += 1
            
            if message_count % 10 == 0:
                print(f"📊 Gönderilen: {message_count}, Hata: {error_count}")
            
            time.sleep(self.message_interval)
        
        duration = time.time() - start_time
        print(f"\n📈 Stres Testi Sonuçları:")
        print(f"   Süre: {duration:.1f} saniye")
        print(f"   Gönderilen Mesaj: {message_count}")
        print(f"   Hata Sayısı: {error_count}")
        print(f"   Mesaj/Saniye: {message_count/duration:.2f}")
        print(f"   Başarı Oranı: {(message_count/(message_count+error_count))*100:.1f}%")
    
    def test_bidirectional(self, xbee):
        """Çift yönlü haberleşme testi"""
        print("\n🔄 Çift Yönlü Haberleşme Testi")
        print("=" * 50)
        print("Bu test için başka bir XBee cihazının mesaj göndermesi gerekiyor...")
        
        initial_count = len(self.received_messages)
        start_time = time.time()
        
        # 10 saniye bekle ve gelen mesajları say
        while time.time() - start_time < 10:
            # Test mesajı gönder
            test_msg = f"Ping_{int(time.time())}"
            xbee.send_broadcast_message(test_msg, construct_message=True)
            
            time.sleep(1)
        
        received_count = len(self.received_messages) - initial_count
        print(f"📨 10 saniyede alınan mesaj: {received_count}")
        
        if received_count > 0:
            print("✅ Çift yönlü haberleşme çalışıyor")
            
            # Son mesajları göster
            print("\n📋 Son alınan mesajlar:")
            for msg in self.received_messages[-min(3, received_count):]:
                print(f"   {msg['sender'][:8]}... -> {msg['data'][:30]}...")
        else:
            print("⚠️  Gelen mesaj yok (başka XBee cihazı gerekli)")
    
    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🧪 XBee Service Test Suite")
        print("=" * 60)
        
        # XBee controller başlat
        try:
            xbee = XBeeController(
                message_received_callback=self.message_callback,
                port="/dev/ttyUSB0",  # Raspberry Pi'de genelde bu
                baudrate=57600
            )
        except Exception as e:
            print(f"❌ XBee controller başlatılamadı: {e}")
            print("💡 XBee cihazının bağlı olduğundan emin olun")
            return
        
        try:
            # Test sırası
            if not self.test_connection(xbee):
                return
            
            time.sleep(2)
            self.test_basic_messaging(xbee)
            
            time.sleep(2)
            self.test_throughput(xbee)
            
            time.sleep(2)
            self.test_stress(xbee)
            
            time.sleep(2)
            self.test_bidirectional(xbee)
            
            # Genel sonuçlar
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\n⏹️  Test kullanıcı tarafından durduruldu")
        finally:
            xbee.close()
            print("🔚 XBee bağlantısı kapatıldı")
    
    def print_summary(self):
        """Test sonuçlarını özetle"""
        print("\n📊 TEST SONUÇLARI ÖZETİ")
        print("=" * 60)
        
        print(f"📤 Gönderilen Mesaj: {len(self.sent_messages)}")
        print(f"📨 Alınan Mesaj: {len(self.received_messages)}")
        
        if self.sent_messages:
            avg_send_time = sum(msg['send_time'] for msg in self.sent_messages) / len(self.sent_messages)
            total_bytes = sum(msg['size'] for msg in self.sent_messages)
            print(f"⏱️  Ortalama Gönderim Süresi: {avg_send_time:.2f}ms")
            print(f"📦 Toplam Gönderilen Veri: {total_bytes} bytes")
        
        if self.received_messages:
            print(f"🔄 İlk Alınan: {datetime.fromtimestamp(self.received_messages[0]['received_time'])}")
            print(f"🔄 Son Alınan: {datetime.fromtimestamp(self.received_messages[-1]['received_time'])}")


def main():
    """Ana test fonksiyonu"""
    print("🚁 Drone XBee Service Test Suite")
    print("Raspberry Pi XBee modülü test ediliyor...")
    
    test_suite = XBeeTestSuite()
    
    try:
        test_suite.run_all_tests()
    except Exception as e:
        print(f"❌ Test hatası: {e}")
    
    print("\n✅ Test tamamlandı!")


if __name__ == "__main__":
    main()
