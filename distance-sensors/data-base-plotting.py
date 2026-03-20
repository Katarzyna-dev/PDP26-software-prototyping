import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import csv
import os
import time
import pandas as pd
from datetime import datetime
import json

# ==== Configuration ====
from config import MQTT_BROKER_IP
broker_ip = MQTT_BROKER_IP
topic = "sensor/distance"  # Matches Pi publisher

# ==== Generate CSV filename with timestamp ====
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)
csv_file = os.path.join(results_dir, f"sensor_session_{timestamp_str}.csv")

# ==== Live Data Storage (Limited to 550 points) ====
MAX_LIVE_POINTS = 550
x_live = deque(maxlen=MAX_LIVE_POINTS)  # Distance
y_live = deque(maxlen=MAX_LIVE_POINTS)  # Timestamp or sequential index

# ==== Create/Clear CSV at start of session ====
f = open(csv_file, 'w', newline='')
writer = csv.writer(f)
writer.writerow(["Distance_cm", "Timestamp"])

# ==== MQTT Logic ====
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())  # Expecting JSON: {"distance":..., "strength":..., "mode":..., "timestamp":...}
        distance = payload.get("distance")
        ts = payload.get("timestamp", time.time())
        
        x_live.append(distance)
        y_live.append(ts)
        
        writer.writerow([distance, ts])
    except Exception as e:
        print(f"Parsing error: {e}")

client = mqtt.Client(protocol=mqtt.MQTTv311)
client.on_connect = lambda c, u, f, rc: c.subscribe(topic)
client.on_message = on_message
client.connect(broker_ip, 1883, 60)
client.loop_start()

# ==== Live Plot Setup ====
fig, ax = plt.subplots(figsize=(10, 6))
line, = ax.plot([], [], 'ro-', markersize=4, alpha=0.8, label="Distance (cm)")
ax.set_title(f"LIVE SENSOR VIEW (Last {MAX_LIVE_POINTS} Points)")
ax.set_xlabel("Timestamp (s)")
ax.set_ylabel("Distance (cm)")
ax.grid(True, linestyle='--', alpha=0.5)
ax.invert_yaxis()

def update(frame):
    if x_live and y_live:
        line.set_data(list(y_live), list(x_live))
        ax.relim()
        ax.autoscale_view()
    return line,

ani = FuncAnimation(fig, update, interval=30, cache_frame_data=False)

# ==== START THE SESSION ====
print(f"Collecting data... Logging to {csv_file}")
print("Close the plot window to end session and generate final map.")

try:
    plt.show()
finally:
    # ==== SESSION ENDED ====
    client.loop_stop()
    f.flush()
    f.close()
    
    if os.path.exists(csv_file):
        print("Generating final high-resolution map...")
        df = pd.read_csv(csv_file)
        
        if len(df) > 0:
            plt.figure(figsize=(12, 6))
            plt.plot(df['Timestamp'], df['Distance_cm'], 'b.-', alpha=0.7)
            plt.title(f"Final Distance vs Time - Total Points: {len(df)}")
            plt.xlabel("Timestamp (s)")
            plt.ylabel("Distance (cm)")
            
            plt.grid(True, alpha=0.3)
            plt.gca().invert_yaxis()
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            final_img = os.path.join(results_dir, f"final_report_{timestamp}.png")
            plt.savefig(final_img, dpi=300)
            print(f"SUCCESS: Saved {len(df)} points to {final_img}")
            plt.show()
        else:
            print("No data was collected.")