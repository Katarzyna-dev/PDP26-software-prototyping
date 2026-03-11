from smbus2 import SMBus, i2c_msg
import time

address = 0x10

# Data request frame (Reg_H, Reg_L, Data Length)
write_msg = i2c_msg.write(address, [1, 2, 7])

with SMBus(1) as bus:
    while True:
        try:
            read_msg = i2c_msg.read(address, 7)
            bus.i2c_rdwr(write_msg, read_msg)
            data = list(read_msg)
            
            TrigFlag = data[0]
            Dist = (data[3] << 8) | data[2]
            Strength = (data[5] << 8) | data[4]
            Mode = data[6]
            
            print(f"Distance: {Dist} cm  Strength: {Strength}  Mode: {Mode}")
        
        except Exception as e:
            print("Read error:", e)
        
        time.sleep(0.1)  # roughly 10 Hz