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

        # ---- Demo parameters -----
        center_x = -500
        center_y = -500
        base_z = -20
        radius = 50
        z_amplitude = 10
        revolutions = 2
        segments_per_rev = 120
        travel_feed = 3000
        motion_feed = 3000
        # --------------------------

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



    # Scanning test
    def scan_grid(self, width, height, x_step=20, feed=3000):
        """
        Mimics scanning over a grid to map the tray using a lidar.
        """

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
            

    # Clean cores by adding the row width to the x-direction to change rows
    def clean_core_rows(
        self,
        start_x,
        start_y,
        row_spacing_x,
        clean_length_y,
        z_depth,
        num_rows,
        spindle_speed,
        base_z=0,
        travel_feed=3000,
        clean_feed=3000
    ):

        self.cnc.set_absolute_mode()

        direction = 1  # 1 = forward, -1 = backward

        # Move to safe height
        self.cnc.move_absolute(z=base_z, feed=travel_feed)

        # Move to initial start position
        self.cnc.move_absolute(x=start_x, y=start_y, feed=travel_feed)

        # Turn spindle on
        self.cnc.spindle_on(spindle_speed)

        for i in range(num_rows):

            row_x = start_x + i * row_spacing_x

            # Retract before reposition
            self.cnc.move_absolute(z=base_z, feed=travel_feed)

            # Move to correct X
            self.cnc.move_absolute(x=row_x, feed=travel_feed)

            # Position Y start depending on direction
            if direction == 1:
                self.cnc.move_absolute(y=start_y, feed=travel_feed)
                target_y = start_y + clean_length_y
            else:
                self.cnc.move_absolute(y=start_y + clean_length_y, feed=travel_feed)
                target_y = start_y

            # Plunge
            self.cnc.move_absolute(z=z_depth, feed=travel_feed)

            # Clean pass
            self.cnc.move_absolute(y=target_y, feed=clean_feed)

            direction *= -1

        # Retract
        self.cnc.move_absolute(z=base_z, feed=travel_feed)

        # Turn spindle off
        self.cnc.spindle_off()

        # Zero
        self.cnc.move_absolute(x=0, y=0, z=0, feed=travel_feed)


        self.cnc.wait_until_idle()


    # Clean cores using a 'bounding box' of the core tray
    def clean_rows_between_points(
        self,
        start_x,
        start_y,
        end_x,
        end_y,
        row_width,
        num_rows,
        z_depth,
        spindle_speed,
        base_z=0,
        travel_feed=3000,
        clean_feed=3000
    ):

        self.cnc.set_absolute_mode()

        # --- Compute direction vector ---
        dx = end_x - start_x
        dy = end_y - start_y

        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError("Start and end cannot be the same point")

        # Unit direction along row
        ux = dx / length
        uy = dy / length

        # Perpendicular unit vector (row stepping direction)
        px = -uy
        py = ux

        # Move to safe height
        self.cnc.move_absolute(z=base_z, feed=travel_feed)

        # Turn spindle on
        self.cnc.spindle_on(spindle_speed)

        for i in range(num_rows):

            # Offset each row by row_width
            offset_x = start_x + i * row_width * px
            offset_y = start_y + i * row_width * py

            row_start_x = offset_x
            row_start_y = offset_y

            row_end_x = offset_x + dx
            row_end_y = offset_y + dy

            # Move above row start
            self.cnc.move_absolute(x=row_start_x, y=row_start_y, feed=travel_feed)

            # Plunge
            self.cnc.move_absolute(z=z_depth, feed=travel_feed)

            # Clean row
            self.cnc.move_absolute(x=row_end_x, y=row_end_y, feed=clean_feed)

            # Retract
            self.cnc.move_absolute(z=base_z, feed=travel_feed)

        # Return to origin
        self.cnc.move_absolute(x=0, y=0, z=0, feed=travel_feed)

        self.cnc.spindle_off()
        self.cnc.wait_until_idle()