import json
import threading
import time
import serial
import functools
import asyncio
from queue import Queue, Full
from digi.xbee.devices import XBeeDevice
from digi.xbee.exception import XBeeException, TransmitException, TimeoutException, InvalidOperatingModeException


def check_connected(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.device.is_open():
            print("XBee device is not connected. Please connect the device first.")
            return None
        return func(self, *args, **kwargs)
    return wrapper


class XbeeService:
    def __init__(self, message_received_callback: callable, port: str, baudrate: int, max_queue_size: int = 100) -> None:
        """
        Initialize XbeeService with required parameters.
        Args:
            message_received_callback: Function to call when a message is received.
            port: Serial port for XBee device.
            baudrate: Baudrate for serial communication.
            max_queue_size: Maximum size for message queue.
        """
        self.port: str = port
        self.baudrate: int = baudrate
        self.device: XBeeDevice = XBeeDevice(port, baudrate)
        self.address = self.device.get_16bit_addr()
        self.message_received_callback = message_received_callback
        self.recent_messages: Queue = Queue(maxsize=max_queue_size)
        self.queue_stop_event: threading.Event = threading.Event()
        self.queue_thread: threading.Thread = threading.Thread(target=self.queue_processor, daemon=True)
        if self.message_received_callback:
            self.queue_thread.start()
            print("Message queue processing thread started.")
        else:
            print("No callback function specified for received messages.")

    
    def queue_processor(self) -> None:
        """
        Thread function to process messages from the queue.
        """
        while not self.queue_stop_event.is_set():
            if self.recent_messages.empty():
                time.sleep(0.1)
                continue
            try:
                message = self.recent_messages.get(timeout=0.5)
                self.handle_processed_message(message)
                self.recent_messages.task_done()
            except Exception as e:
                print(f"Error processing message: {e}")
                if not self.recent_messages.empty():
                    self.recent_messages.task_done()
    
    def handle_processed_message(self, message_dict: dict) -> None:
        """
        Handle processed message dictionary.
        Format: {"sender": str, "isBroadcast": bool, "data": str, "timestamp": int}
        """
        try:
            sender = message_dict.get("sender", "Unknown")
            is_broadcast = message_dict.get("isBroadcast", False)
            data = message_dict.get("data", "")
            timestamp = message_dict.get("timestamp", 0)
            print(f"XBee Message Received: sender={sender}, broadcast={is_broadcast}, data={data}, timestamp={timestamp}")
            if hasattr(self, 'custom_message_handler') and callable(self.custom_message_handler):
                # Async method kontrolü ve uygun çağrım
                if asyncio.iscoroutinefunction(self.custom_message_handler):
                    # Async method ise event loop'ta çalıştır
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.custom_message_handler(message_dict))
                    except RuntimeError:
                        # Event loop çalışmıyorsa yeni thread'de başlat
                        import threading
                        def run_async_handler():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                new_loop.run_until_complete(self.custom_message_handler(message_dict))
                            finally:
                                new_loop.close()
                        
                        threading.Thread(target=run_async_handler, daemon=True).start()
                else:
                    # Sync method ise normal çağır
                    self.custom_message_handler(message_dict)
        except Exception as e:
            print(f"Error handling processed message: {e}")

    def set_custom_message_handler(self, handler_func: callable) -> None:
        """
        Set a custom message handler function.
        The function should accept a processed message dictionary.
        """
        self.custom_message_handler = handler_func
        print("Custom message handler set.")

    def default_message_received_callback(self, message) -> None:
        """
        Callback function to process messages received from XBee.
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
            try:
                self.recent_messages.put_nowait(message_full)
            except Full:
                self.recent_messages.get_nowait()
                self.recent_messages.put_nowait(message_full)
        except Exception as e:
            print(f"Error processing received message: {e}")

    def configure_xbee_api_mode(self) -> bool:
        """
        Set XBee device to API mode.
        """
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(1)
            ser.write(b'+++')
            time.sleep(2)
            ser.read(ser.in_waiting)
            ser.write(b'ATAP1\r')
            time.sleep(0.5)
            ser.read(ser.in_waiting)
            ser.write(b'ATWR\r')
            time.sleep(0.5)
            ser.read(ser.in_waiting)
            ser.write(b'ATCN\r')
            time.sleep(0.5)
            ser.close()
            print("XBee set to API mode.")
            return True
        except Exception as e:
            print(f"Error setting XBee to API mode: {e}")
            return False

    def listen(self) -> None:
        """
        Listen for XBee messages and call the callback function when a message is received.
        """
        try:
            if not self.device.is_open():
                self.device.open()
            self.device.add_data_received_callback(self.default_message_received_callback)
            print("Listening for XBee messages...")
        except Exception as e:
            print(f"Failed to open XBee: {e}")
            raise
    
    def construct_message(self, data: str) -> bytes:
        """
        Convert the given data to JSON format for XBee transmission.
        """
        message = {
            "i": self.address,
            "d": data,
            "t": int(time.time()*1000)
        }
        return json.dumps(message, ensure_ascii=False).replace("\n", "").replace(" ", "").encode('utf-8')
    
    @check_connected
    def send_broadcast_message(self, data: str, construct_message: bool) -> bool:
        """
        Broadcast data over XBee.
        """
        try:
            message = self.construct_message(data) if construct_message else data
            self.device.send_data_broadcast(message)
            print(f"Broadcast message sent: {data}")
            return True
        except (XBeeException, TimeoutException, TransmitException, InvalidOperatingModeException) as e:
            print(f"XBee error: {e}")
            return False
    
    @check_connected
    def send_private_message(self, receiver, data: str) -> bool:
        """
        Send data to a specific receiver via XBee.
        """
        message = self.construct_message(data)
        try:
            self.device.send_data(receiver, message)
            print(f"Private message sent to {receiver}: {data}")
            return True
        except Exception as e:
            print(f"Failed to send private message: {e}")
            return False
    
    def close(self) -> None:
        """
        Close the XBee device and stop the message queue processing thread.
        """
        if self.device.is_open():
            self.device.close()
            print("XBee closed.")
            self.queue_stop_event.set()
            print("Message queue processing thread stopped.")
        else:
            print("XBee already closed.")

