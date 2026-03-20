import time
import board
import digitalio
from adafruit_hx711.hx711 import HX711
from adafruit_hx711.analog_in import AnalogIn

# --- EDIT THESE VALUES AFTER CALIBRATING ---
OFFSET = 123456  # Replace with your 'Tare Offset'
SCALE_FACTOR = 456.7  # Replace with your 'Scale Factor'
# ------------------------------------------

data = digitalio.DigitalInOut(board.D5)
clock = digitalio.DigitalInOut(board.D6)
hx711 = HX711(data, clock)
channel_a = AnalogIn(hx711, HX711.CHAN_A_GAIN_128)

while True:
    raw_value = channel_a.value
    weight = (raw_value - OFFSET) / SCALE_FACTOR
    
    # Simple smoothing: if weight is very small, show 0
    if abs(weight) < 0.1: weight = 0.0
    
    print(f"Weight: {weight:.2f} units")
    time.sleep(0.5)