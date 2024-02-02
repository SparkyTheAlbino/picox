import argparse
import time
from piconnect.detect import get_serial_ports, is_pico
from piconnect.upy.rp2040 import RP2040

def main():
    parser = argparse.ArgumentParser(description="piconnect")
    subparsers = parser.add_subparsers(dest="command")

    # ls command
    ls_parser = subparsers.add_parser("ls", help="Directory listing on Pi Pico")
    ls_parser.add_argument("device", help="Serial device")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("device", help="Serial device")
    upload_parser.add_argument("read_file", help="File to upload")
    upload_parser.add_argument("file", help="Save name for file to upload")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download a file")
    download_parser.add_argument("device", help="Serial device")
    download_parser.add_argument("file", help="File to download")
    download_parser.add_argument("save_file", help="Location to save to")

    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute a file")
    exec_parser.add_argument("device", help="Serial device")
    exec_parser.add_argument("file", help="File to execute")

    # Detect command
    detect_parser = subparsers.add_parser("detect", help="Detect pico on serial")

    args = parser.parse_args()

    match args.command:
        case "ls":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            for file in pico.get_file_list():
                print(file)
        case "upload":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            with open(args.read_file, "w") as read_file:
                pico.upload_file(read_file, file, overwrite=False)
        case "download":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            with open(args.save_file, "w") as save_file:
                pico.download_file(args.file, save_file)
        case "execute":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            print(f"Executing {args.file}")
            pico.execute_file(args.file)
        case "detect":
            serial_devices = get_serial_ports()
            for device in serial_devices:
                if is_pico(device):
                    print(f"{device}")

if __name__ == "__main__":
    main()