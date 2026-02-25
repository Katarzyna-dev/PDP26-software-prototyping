from controllers.cnc_controller import CNCController
from systems.test_system import CleaningSystem


PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_0001-if00-port0"


def main():

    cnc = CNCController(PORT)

    cnc.unlock()
    cnc.home()                              # IMPORTANT!! If home is not set CNC can run into the walls and damage it.
    cnc.set_absolute_mode()

    cleaning = CleaningSystem(cnc)
    # cleaning.clean_rectangle(width=-300, height=-200, feed=3000)
    #cleaning.demo_motion()

    # cleaning.scan_grid(
    #     width=250,
    #     height=250,
    #     x_step=20,
    #     feed=3000
    # )

    # print(cnc.get_position())

    cnc.close()


if __name__ == "__main__":
    main()
