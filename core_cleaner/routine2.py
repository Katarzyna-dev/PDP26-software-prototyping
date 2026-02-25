from controllers.cnc_controller import CNCController
from systems.test_system import CleaningSystem


PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_0001-if00-port0"


def main():

    cnc = CNCController(PORT)

    cnc.unlock()
    cnc.home()                              # IMPORTANT!! If home is not set CNC can run into the walls and damage it.

    cleaning = CleaningSystem(cnc)

    cleaning.clean_core_rows(
    start_x=50.0,
    start_y=20.0,
    row_spacing_x=30.0,
    clean_length_y=500.0,
    z_depth=-5.0,
    num_rows=6
)


    cnc.close()


if __name__ == "__main__":
    main()
