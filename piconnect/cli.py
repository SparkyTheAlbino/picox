import argparse
from piconnect.detect import get_serial_ports, is_pico
from piconnect.upy.rp2040 import RP2040

def get_args():
    parser = argparse.ArgumentParser(description="piconnect")
    parser.add_argument("-v", "--verbose", action="store_true")

    subparsers  = parser.add_subparsers(dest="command")

    detect_parser   = subparsers.add_parser("detect",   help="Detect pico on serial")
    repl_parser     = subparsers.add_parser("repl",     help="Start REPL session on Pi Pico")
    ls_parser       = subparsers.add_parser("ls",       help="Directory listing on Pi Pico")
    upload_parser   = subparsers.add_parser("upload",   help="Upload a file")
    download_parser = subparsers.add_parser("download", help="Download a file")
    exec_parser     = subparsers.add_parser("exec",     help="Execute a file")
    stop_parser     = subparsers.add_parser("stop",     help="Send a stop to Pico")

    repl_parser.add_argument("device", help="Serial device")

    ls_parser.add_argument("device", help="Serial device")

    upload_parser.add_argument("device", help="Serial device")
    upload_parser.add_argument("read_file", help="File to upload")
    upload_parser.add_argument("file", help="Save name for file to upload")
    upload_parser.add_argument("--overwrite", action="store_true", help="Overwrite the file if it exists")

    download_parser.add_argument("device", help="Serial device")
    download_parser.add_argument("file", help="File to download")
    download_parser.add_argument("save_file", help="Location to save to")

    exec_parser.add_argument("device", help="Serial device")
    exec_parser.add_argument("file", help="File to execute")

    stop_parser.add_argument("device", help="Serial device")

    return parser.parse_args()

def main():
    args = get_args()

    match args.command:
        case "repl":
            # Arrow keys and block commands are broken.... maybe just no timeout for this?
            pico = RP2040(args.device, verbose=False)
            pico.start_repl()
        case "ls":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            for file in pico.get_file_list():
                print(file)
        case "stop":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            pico.stop_exec()
        case "upload":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            with open(args.read_file, "rb") as read_file:
                pico.upload_file(read_file, args.file, overwrite=args.overwrite)
        case "download":
            pico = RP2040(args.device)
            pico.stop_exec()
            pico.send_enter()
            if not pico.coms_test():
                print("Coms test failed. Try re-inserting the Pi Pico USB")
            with open(args.save_file, "w") as save_file:
                pico.download_file(args.file, save_file)
        case "exec":
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