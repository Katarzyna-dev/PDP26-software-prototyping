import time
import json
import board
import busio
import adafruit_vl53l0x
import paho.mqtt.client as mqtt

# ---- I2C and sensor setup ----
i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

# Optional: adjust timing budget for speed/accuracy
# vl53.measurement_timing_budget = 20000  # 20 ms → faster, less accurate
# vl53.measurement_timing_budget = 200000 # 200 ms → slower, more accurate

# ---- MQTT setup ----
MQTT_BROKER = "192.168.1.103"  # Replace with your Pi's IP if not localhost
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/vl"

client = mqtt.Client(client_id="", protocol=mqtt.MQTTv311)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# ---- Main loop ----
try:
    while True:
        dist = vl53.range  # distance in millimeters
        payload = {
            "distance": dist,
            "timestamp": time.time()
        }
        client.publish(MQTT_TOPIC, json.dumps(payload))
        print(f"Published: {dist} mm")
        time.sleep(0.02)  # 10 Hz
except KeyboardInterrupt:
    print("Stopping publisher...")
finally:
    client.loop_stop()