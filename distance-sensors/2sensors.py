import time
import json
from smbus2 import SMBus, i2c_msg
import board
import busio
import adafruit_vl53l0x
import paho.mqtt.client as mqtt

# -----------------------------
# I2C SENSOR 1 (custom sensor)
# -----------------------------
I2C_ADDRESS = 0x10
WRITE_FRAME = [1, 2, 7]
READ_LENGTH = 7
BUS_ID = 1

# -----------------------------
# SENSOR 2 (VL53L0X)
# -----------------------------
i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

# -----------------------------
# MQTT CONFIG
# -----------------------------
MQTT_BROKER = "localhost"  # change if needed
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/all"

# -----------------------------
# MQTT SETUP
# -----------------------------
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# -----------------------------
# READ SENSOR 1
# -----------------------------
def read_custom_sensor(bus):
    try:
        write_msg = i2c_msg.write(I2C_ADDRESS, WRITE_FRAME)
        read_msg = i2c_msg.read(I2C_ADDRESS, READ_LENGTH)
        bus.i2c_rdwr(write_msg, read_msg)
        data = list(read_msg)

        return {
            "distance": (data[3] << 8) | data[2],
            "strength": (data[5] << 8) | data[4],
            "mode": data[6]
        }
    except Exception as e:
        print("Custom sensor error:", e)
        return None

# -----------------------------
# MAIN LOOP
# -----------------------------
with SMBus(BUS_ID) as bus:
    while True:
        try:
            # Read both sensors
            sensor1 = read_custom_sensor(bus)
            sensor2_distance = vl53.range

            payload = {
                "sensor1": sensor1,
                "sensor2": {
                    "distance": sensor2_distance
                },
                "timestamp": time.time()
            }

            # Publish combined data
            client.publish(MQTT_TOPIC, json.dumps(payload))

            print(payload)

            time.sleep(0.05)  # ~20 Hz (adjust if needed)

        except Exception as e:
            print("Loop error:", e)