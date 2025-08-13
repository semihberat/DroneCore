import numpy
import math

class PID:
    """
    PID Kontrol Sınıfı
    - Proportional, Integral, Derivative kontrol bileşenlerini içerir
    - Hedefe ulaşmak için hız ve yön kontrolü sağlar
    """
    
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp  # Proportional kazancı
        self.ki = ki  # Integral kazancı
        self.kd = kd  # Derivative kazancı
        
        self.previous_error = 0.0  # Önceki hata değeri
        self.integral = 0.0  # Integral toplamı
    
    def calculate(self, target: float, current: float, dt: float) -> float:
        """
        PID kontrol hesaplama fonksiyonu
        Args:
            target: Hedef değer
            current: Güncel değer
            dt: Zaman farkı (saniye)
        Returns:
            Kontrol çıktısı (hız)
        """
        error = target - current  # Hata hesapla
        self.integral += error * dt  # Integral güncelleme
        
        derivative = (error - self.previous_error) / dt if dt > 0 else 0.0  # Türev hesapla
        
        # PID kontrol çıktısını hesapla
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        
        self.previous_error = error  # Önceki hatayı güncelle
        
        return output  # Kontrol çıktısını döndür
    
    
            