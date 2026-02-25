import math
import time

class CleaningSystem:

    def __init__(self, cnc_controller):
        self.cnc = cnc_controller


    # Trace rectangle
    def clean_rectangle(self, width, height, feed=3000):
        """
        Example cleaning motion - tracing core tray edges
        """

        self.cnc.set_absolute_mode()

        print("Starting rectangular cleaning pass")

        # Home at 'bottom-left' corner 
        self.cnc.move_relative(dx=width, dy=0, feed=feed)
        self.cnc.move_relative(dx=0, dy=height, feed=feed)
        self.cnc.move_relative(dx=-width, dy=0, feed=feed)
        self.cnc.move_relative(dx=0, dy=-height, feed=feed)

        print("Rectangle complete")



    # Test motion
    def demo_motion(self):
        """
        Simple hardcoded helix demo.
        Z=0 is top.
        Motion stays between -10 and -30 mm.
        """

        # ---- Hardcoded demo parameters ----
        center_x = -500
        center_y = -500
        base_z = -20
        radius = 50
        z_amplitude = 10
        revolutions = 2
        segments_per_rev = 120
        travel_feed = 3000
        motion_feed = 3000
        # -----------------------------------

        total_segments = revolutions * segments_per_rev

        # Ensure safe height
        self.cnc.move_absolute(z=0, feed=travel_feed)

        # Move to circle start point at safe height
        start_x = center_x + radius
        start_y = center_y
        self.cnc.move_absolute(x=start_x, y=start_y, feed=travel_feed)

        # Drop to starting depth
        self.cnc.move_absolute(z=base_z, feed=travel_feed)

        # Helical motion
        for i in range(total_segments + 1):

            theta = 2 * math.pi * (i / segments_per_rev)

            x = center_x + radius * math.cos(theta)
            y = center_y + radius * math.sin(theta)
            z = base_z + z_amplitude * math.sin(theta)

            self.cnc.move_absolute(x=x, y=y, z=z, feed=motion_feed)

        # Retract to top at end
        self.cnc.move_absolute(z=0, feed=travel_feed)

        # Go home
        self.cnc.home




    def scan_grid(self, width, height, x_step=20, feed=3000):

        self.cnc.set_absolute_mode()

        # Start at machine zero (top-right)
        self.cnc.move_absolute(x=0, y=0, feed=3000)
        self.cnc.wait_until_idle()

        current_x = 0
        direction = -1  # start by going negative Y

        while abs(current_x) <= width:

            target_y = -height if direction == -1 else 0
            self.cnc.move_absolute(y=target_y, feed=feed)
            self.cnc.wait_until_idle()

            current_x -= x_step
            if abs(current_x) > width:
                break

            self.cnc.move_absolute(x=current_x, feed=feed)
            self.cnc.wait_until_idle()

            direction *= -1
            