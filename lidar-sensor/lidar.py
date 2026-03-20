from smbus2 import SMBus, i2c_msg
import time
import json
import paho.mqtt.client as mqtt

address = 0x10

# MQTT setup
broker = "localhost"   # Pi itself
topic = "sensor/distance"

client = mqtt.Client()
client.connect(broker, 1883, 60)

write_msg = i2c_msg.write(address, [1, 2, 7])

with SMBus(1) as bus:
    while True:
        try:
            read_msg = i2c_msg.read(address, 7)
            bus.i2c_rdwr(write_msg, read_msg)
            data = list(read_msg)
            
            Dist = (data[3] << 8) | data[2]
            Strength = (data[5] << 8) | data[4]
            Mode = data[6]

            payload = {
                "distance": Dist,
                "strength": Strength,
                "mode": Mode,
                "timestamp": time.time()
            }

            client.publish(topic, json.dumps(payload))

        except Exception as e:
            print("Read error:", e)
        
        time.sleep(0.1)