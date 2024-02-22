import serial
import serial.tools.list_ports
import glob
import platform
from .upy.rp2040 import RP2040

def get_serial_ports():
    if platform.system() == "Windows":
        # TODO Fix windows
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    elif platform.system() == "Linux":
        # TODO Test Linux
        return glob.glob('/dev/ttyACM*')
    elif platform.system() == "Darwin":
        return glob.glob('/dev/tty.usb*')
    else:
        raise NotImplementedError("Unsupported OS")

def is_pico(device):
    try:
        pico = RP2040(device)
        pico.stop_exec()
        pico.send_enter()
        return pico.coms_test()
    except Exception as e:
        return False