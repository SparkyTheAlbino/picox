import glob
import platform
from typing import List, Optional

import serial
import serial.tools.list_ports

from .upy.rp2040 import RP2040


def get_serial_ports() -> List[str]:
    """
    Get USB serial devices for your OS
    raises:
        NotImplimentedError - If not Windows, Linux or macOS
    """
    match platform.system():
        case "Windows":
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports if "USB Serial Device" in port.description]
        case "Linux":
            return glob.glob('/dev/ttyACM*')
        case "Darwin":
            return glob.glob('/dev/tty.usb*')
        case _:
            raise NotImplementedError("Unsupported OS")

def is_pico(device: str):
    """
    Try to determine if USB serial device is a Pi Pico device
    args:
        device (str): USB serial device to test
    """
    try:
        pico = RP2040(device, serial_read_timeout=1, serial_write_timeout=1)
        pico.stop_exec()
        pico.send_enter()
        return pico.coms_test()
    except Exception as err:
        return False

# TODO - Get first or get all???

def search_ports_for_pico(serial_devices: List[str]):
    """
    Iterate over list of strings and try to communicate on those USB serial ports with a Pi Pico
    """
    for device in serial_devices:
        if is_pico(device):
            return device
    else:
        return None
    
def detect_pico() -> Optional[str]:
    """
    Get ports + detect pico
    """
    serial_devices = get_serial_ports()
    return search_ports_for_pico(serial_devices)