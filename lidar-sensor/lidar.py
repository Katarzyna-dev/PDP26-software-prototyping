import smbus
import time

bus = smbus.SMBus(1)
addr = 0x10

while True:
    try:
        data = bus.read_i2c_block_data(addr, 0x00, 9)
        dist = data[2] + data[3]*256
        print("Distance:", dist, "cm")
    except:
        print("Read error")

    time.sleep(0.1)