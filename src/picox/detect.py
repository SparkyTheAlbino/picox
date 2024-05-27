import glob
import platform
from typing import List, Optional

import serial
import serial.tools.list_ports

from .upy import Pico
from .logconfig import LOGGER


def get_serial_ports() -> List[str]:
    """
    Get USB serial devices for your OS
    raises:
        NotImplementedError - If not Windows, Linux or macOS
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

def is_pico(device: str) -> bool:
    """
    Try to determine if USB serial device is a Pi Pico device
    args:
        device (str): USB serial device to test
    returns:
        bool : True/False if MicroPython passed the coms test
    """
    try:
        Pico(
            device,
            serial_read_timeout=1,
            serial_write_timeout=1,
        )
    except Exception as err:
        if "[Errno 13]" in str(err):
            LOGGER.warning(f"[{device}] :: Permission denied!")
        return False
    else:
        return True

def search_ports_for_pico(serial_devices: List[str]) -> List[str]:
    """
    Iterate over list of strings and try to communicate on those USB serial ports with a Pi Pico
    """
    for device in serial_devices:
        if is_pico(device):
            return device
    else:
        return None
    
def get_first_pico_serial() -> Optional[str]:
    """
    Get ports + detect pico
    returns:
        str: serial device name or None
    """
    serial_devices = get_serial_ports()
    for device in serial_devices:
        if is_pico(device):
            return device
    else:
        return None

def get_all_pico_serial() -> List[str]:
    """
    Get ports then return all detected pico devices
    returns:
        List[str] : List of potential Pico serial devices
    """
    serial_devices = get_serial_ports()
    pico_devices = []
    for serial_device in serial_devices:
        if is_pico(serial_device):
            pico_devices.append(serial_device)
    return pico_devices