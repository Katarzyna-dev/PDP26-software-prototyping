import serial
import time


class CNCController:

    def __init__(self, port, baudrate=115200, timeout=0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self._wait_for_boot()
        self._sync()


    # Startup

    def _wait_for_boot(self):
        print("Waiting for controller boot...")
        while True:
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()
                print(line)
                if "Grbl" in line:
                    print("Controller ready.")
                    return

    def _sync(self):
        self.ser.write(b'\n')
        time.sleep(0.1)
        self.ser.reset_input_buffer()


    # Communication
    
    def send_command(self, command):
        self.ser.write((command + "\n").encode())

        while True:
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()

                if line.startswith("error"):
                    raise RuntimeError(f"CNC error after '{command}': {line}")

                if line.startswith("ALARM"):
                    raise RuntimeError(f"CNC alarm after '{command}': {line}")

                if line == "ok":
                    return


    def wait_until_idle(self):
        while True:
            self.ser.write(b'?\n')
            time.sleep(0.05)

            while self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()

                if line.startswith("ALARM"):
                    raise RuntimeError(f"CNC alarm: {line}")

                if line.startswith("error"):
                    raise RuntimeError(f"CNC error: {line}")

                if line.startswith("<"):
                    # If it's not Run, assume finished
                    if "Run" not in line:
                        return line

            time.sleep(0.05)



    # Motion

    def unlock(self):
        self.send_command("$X")
        time.sleep(0.2)

    def home(self):
        self.send_command("$H")
        self.wait_until_idle()
        
    def emergency_stop(self):
        self.ser.write(b'!')
        self.ser.flush()

    def set_absolute_mode(self):
        self.send_command("G90")

    def set_relative_mode(self):
        self.send_command("G91")

    def move_absolute(self, x=None, y=None, z=None, feed=1500):
        cmd = "G1"
        if x is not None:
            cmd += f" X{x}"
        if y is not None:
            cmd += f" Y{y}"
        if z is not None:
            cmd += f" Z{z}"
        cmd += f" F{feed}"

        self.send_command(cmd)
        # self.wait_until_idle()

    def move_relative(self, dx=0, dy=0, dz=0, feed=1500):
        self.set_relative_mode()

        cmd = f"G1 X{dx} Y{dy} Z{dz} F{feed}"
        self.send_command(cmd)

        self.wait_until_idle()
        self.set_absolute_mode()

    def get_position(self):
        self.ser.write(b'?\n')
        time.sleep(0.1)

        while self.ser.in_waiting:
            line = self.ser.readline().decode(errors="ignore").strip()
            if line.startswith("<"):
                return line

    def close(self):
        self.ser.close()



    # Spindle

    def spindle_on(self, speed):
        self.send_command(f"M3 S{speed}")

    def spindle_off(self):
        self.send_command("M5")