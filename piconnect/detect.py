import serial
import serial.tools.list_ports
import glob
import platform

def get_serial_ports():
    if platform.system() == "Windows":
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    elif platform.system() == "Linux":
        return glob.glob('/dev/ttyACM*')
    elif platform.system() == "Darwin":
        return glob.glob('/dev/tty.usb*')
    else:
        raise NotImplementedError("Unsupported OS")

def is_pico(device):
    try:
        with serial.Serial(device, baudrate=115200, timeout=1, write_timeout=1) as ser:
            ser.write(b"Hello Pi Pico\r\n")
            response = ser.readline()
            return "Pi Pico" in response.decode()
    except (Exception) as e:
        return False
