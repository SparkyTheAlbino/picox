import serial
import serial.tools.list_ports
import glob
import platform
from .upy.rp2040 import RP2040

def get_serial_ports():
    match platform.system():
        case "Windows":
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports if "USB Serial Device" in port.description]
        case "Linux":
            return glob.glob('/dev/ttyACM*')
        case "Darwin":
            glob.glob('/dev/tty.usb*')
        case _:
            raise NotImplementedError("Unsupported OS")

def is_pico(device):
    try:
        pico = RP2040(device, serial_read_timeout=1, serial_write_timeout=1)
        pico.stop_exec()
        pico.send_enter()
        return pico.coms_test()
    except Exception as e:
        return False
    
def scan_for_pico(serial_devices):
    for device in serial_devices:
        if is_pico(device):
            return device
    else:
        return None