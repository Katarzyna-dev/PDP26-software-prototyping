from smbus2 import SMBus, i2c_msg
import time
import json
import paho.mqtt.client as mqtt

# -----------------------------
# I2C SENSOR CONFIG
# -----------------------------
I2C_ADDRESS = 0x10
WRITE_FRAME = [1, 2, 7]
READ_LENGTH = 7
BUS_ID = 1
PUBLISH_INTERVAL = 0.01  # seconds

# -----------------------------
# MQTT CONFIG
# -----------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/distance"

# -----------------------------
# MQTT CALLBACKS
# -----------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("MQTT connected successfully")
    else:
        print(f"MQTT connection failed with code {rc}")

def on_publish(client, userdata, mid):
    pass

# -----------------------------
# MAIN SCRIPT
# -----------------------------
def read_sensor(bus):
    """Read distance sensor data from I2C bus."""
    try:
        write_msg = i2c_msg.write(I2C_ADDRESS, WRITE_FRAME)
        read_msg = i2c_msg.read(I2C_ADDRESS, READ_LENGTH)
        bus.i2c_rdwr(write_msg, read_msg)
        data = list(read_msg)

        dist = (data[3] << 8) | data[2]
        strength = (data[5] << 8) | data[4]
        mode = data[6]

        return {
            "distance": dist,
            "strength": strength,
            "mode": mode,
            "timestamp": time.time()
        }
    except Exception as e:
        print("Sensor read error:", e)
        return None

def main():
    # MQTT client setup
    client = mqtt.Client(client_id="", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    # Open I2C bus
    with SMBus(BUS_ID) as bus:
        while True:
            payload = read_sensor(bus)
            if payload:
                client.publish(MQTT_TOPIC, json.dumps(payload))
            time.sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    main()