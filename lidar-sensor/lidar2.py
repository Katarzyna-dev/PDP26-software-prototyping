# SPDX-FileCopyrightText: Copyright (c) 2024 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import board
import digitalio
from adafruit_hx711.hx711 import HX711
from adafruit_hx711.analog_in import AnalogIn
from smbus2 import SMBus, i2c_msg

# --- HX711 setup (pressure/load cell) ---
data_pin = digitalio.DigitalInOut(board.D5)
data_pin.direction = digitalio.Direction.INPUT
clock_pin = digitalio.DigitalInOut(board.D6)
clock_pin.direction = digitalio.Direction.OUTPUT

hx711 = HX711(data_pin, clock_pin)
channel_a = AnalogIn(hx711, HX711.CHAN_A_GAIN_128)
# channel_b = AnalogIn(hx711, HX711.CHAN_B_GAIN_32)  # optional

# --- TFMini-Plus setup (I2C LiDAR) ---
tfm_address = 0x10
write_msg = i2c_msg.write(tfm_address, [1, 2, 7])

with SMBus(1) as bus:
    while True:
        try:
            # --- Read HX711 ---
            pressure = channel_a.value
            print(f"Pressure reading: {pressure}")

            # --- Read TFMini-Plus ---
            read_msg = i2c_msg.read(tfm_address, 7)
            bus.i2c_rdwr(write_msg, read_msg)
            data = list(read_msg)

            TrigFlag = data[0]
            distance = (data[3] << 8) | data[2]
            strength = (data[5] << 8) | data[4]
            mode = data[6]

            print(f"Distance: {distance} cm  Strength: {strength}  Mode: {mode}")

        except Exception as e:
            print("Read error:", e)

        time.sleep(0.1)  # 10 Hz loop