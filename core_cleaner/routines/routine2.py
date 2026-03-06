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

    cleaning.clean_core_rows(
    start_x=-166,
    start_y=-106,
    row_spacing_x=-55.5,
    clean_length_y=-900.0,
    z_depth=-25,
    num_rows=6,
    base_z=-20.0,
    spindle_speed=500)


    cnc.close()


if __name__ == "__main__":
    main()
