import serial
import time
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# SETTINGS
PORT = os.getenv('XPRO_PORT')  # Change to 'COM3' etc. on Windows
BAUD = 115200
DISTANCE_MM = 1000     # 1 meter = 1000mm
SPEED = 2000           # mm per minute (how fast to move)

def monitor_move(ser):
    """Polls the machine state until it returns to 'Idle'"""
    print("Moving...")
    while True:
        ser.write(b'?') # Send status query
        status = ser.readline().decode().strip()
        
        if status:
            print(f"Status: {status}") # e.g., <Run|WPos:450.00,0,0...>
            
            if 'Idle' in status:
                print("Move Complete!")
                break
        
        time.sleep(0.1) # Check 10 times per second

try:
    # 1. Open Connection
    s = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2) # Wait for xPRO to wake up
    s.flushInput()

    # 2. Setup Machine State
    # G21: Metric units, G91: Relative mode (move 1m from "here")
    s.write(b"G21 G91\n") 
    
    # 3. Send the 1-meter move command
    # G1: Linear move, X1000: Move X 1000mm, F2000: Speed
    move_cmd = f"G1 X{DISTANCE_MM} F{SPEED}\n"
    print(f"Sending: {move_cmd}")
    s.write(move_cmd.encode())

    # 4. Monitor in Real-Time
    monitor_move(s)

except Exception as e:
    print(f"Error: {e}")
finally:
    s.close()