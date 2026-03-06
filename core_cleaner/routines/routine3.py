# Nav to root to find dependencies
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from controllers.cnc_controller import CNCController
from systems.test_system import CleaningSystem



PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_0001-if00-port0"


def main():

    cnc = CNCController(PORT)

    cnc.unlock()
    cnc.home()                              # IMPORTANT!! If home is not set CNC can run into the walls and damage it.

    cleaning = CleaningSystem(cnc)

    cleaning.clean_rows_between_points(
        start_x=-166.0,
        start_y=-106.0,
        end_x=-449,
        end_y=-1030,
        z_depth=-55,
        num_rows=6,
        spindle_speed=0,
        base_z=-40,
        travel_feed=3000,
        clean_feed=3000
    )


    cnc.close()


if __name__ == "__main__":
    main()
