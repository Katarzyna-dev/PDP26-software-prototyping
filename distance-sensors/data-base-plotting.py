import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import csv
import os
import time
import pandas as pd
from datetime import datetime


# ==== Configuration ====
from config import MQTT_BROKER_IP
broker_ip = MQTT_BROKER_IP
topic = "sensors/distance"
# ==== Generate CSV filename with timestamp ====
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)
csv_file = os.path.join(results_dir, f"sensor_session_{timestamp_str}.csv")


# ==== Live Data Storage (Limited to 500) ====
MAX_LIVE_POINTS = 500
x_live = deque(maxlen=MAX_LIVE_POINTS)
y_live = deque(maxlen=MAX_LIVE_POINTS)

# Create/Clear CSV at start of session
f = open(csv_file, 'w', newline='')
writer = csv.writer(f)
writer.writerow(["X_mm", "Y_mm", "Timestamp"])

# ==== MQTT Logic ====
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        x, y = map(int, payload.split(","))
        
        x_live.append(x)
        y_live.append(y)
        
        writer.writerow([x, y, time.time()])
            
    except Exception as e:
        print(f"Parsing error: {e}")

client = mqtt.Client()
client.on_connect = lambda c, u, f, rc: c.subscribe(topic)
client.on_message = on_message
client.connect(broker_ip, 1883, 60)
client.loop_start()

# ==== Live Plot Setup ====
fig, ax = plt.subplots(figsize=(10, 7))
line, = ax.plot([], [], 'ro', markersize=4, alpha=0.8, label="Recent Path")
ax.set_title("LIVE SENSOR VIEW (Last 500 Points)")
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_xlim(0, 4000) # static limits for speed
ax.set_ylim(0, 4000)
ax.grid(True, linestyle='--', alpha=0.5)

def update(frame):
    if x_live:
        line.set_data(list(x_live), list(y_live))
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
        
        # Read all data back from the CSV
        df = pd.read_csv(csv_file)
        
        if len(df) > 0:
            # Compute min/max with a small padding
            pad_x = (df['X_mm'].max() - df['X_mm'].min()) * 0.05  # 5% padding
            pad_y = (df['Y_mm'].max() - df['Y_mm'].min()) * 0.05

            x_min, x_max = df['X_mm'].min() - pad_x, df['X_mm'].max() + pad_x
            y_min, y_max = df['Y_mm'].min() - pad_y, df['Y_mm'].max() + pad_y

            plt.figure(figsize=(12, 10))
            plt.scatter(df['X_mm'], df['Y_mm'], 
                        s=10, #size of the points
                        c='blue',
                        alpha=0.7,
                        edgecolors='none')
            
            plt.title(f"Final Session Map - Total Points: {len(df)}")
            plt.xlabel("X (mm)")
            plt.ylabel("Y (mm)")
            plt.xlim(x_min, x_max)
            plt.ylim(y_min, y_max)
            plt.axis('equal')  # Keep correct geometry
            plt.grid(True, alpha=0.3)

            # Save the final figure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            final_img = os.path.join(results_dir, f"final_report_{timestamp}.png")
            plt.savefig(final_img, dpi=300)
            print(f"SUCCESS: Saved {len(df)} points to {final_img}")
            plt.show()
        else:
            print("No data was collected.")