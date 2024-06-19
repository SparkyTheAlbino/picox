import argparse
import logging
import sys
from pathlib import Path

from .upy import Pico
from .detect import get_all_pico_serial, get_first_pico_serial
from .logconfig import LOGGER


def get_args():
    parser = argparse.ArgumentParser(description="picox")
    parser.add_argument("-v", "--verbose", action="store_true")

    # parse global flags first
    args, remaining_argv = parser.parse_known_args()

    subparsers = parser.add_subparsers(dest="command")

    detect_parser   = subparsers.add_parser("detect", help="Detect pico on serial")
    repl_parser     = subparsers.add_parser("repl", help="Start REPL session on Pi Pico")
    cat_parser      = subparsers.add_parser("cat", help="Print file contents")
    ls_parser       = subparsers.add_parser("ls", help="Directory listing on Pi Pico")
    rm_parser       = subparsers.add_parser("rm", help="Delete file/folder on Pi Pico")
    mkdir_parser    = subparsers.add_parser("mkdir", help="Create directory on pico")
    upload_parser   = subparsers.add_parser("upload", help="Upload a file")
    download_parser = subparsers.add_parser("download", help="Download a file")
    exec_parser     = subparsers.add_parser("exec", help="Execute a file")
    stop_parser     = subparsers.add_parser("stop", help="Send a stop to Pico")
    attach_parser   = subparsers.add_parser('attach', help="Attach to console output from Pico")
    reboot_parser   = subparsers.add_parser('reboot', help="Soft reboot Pico")

    cat_parser.add_argument("device", help="Serial device")
    cat_parser.add_argument("file", help="File to cat")

    detect_parser.add_argument("--all", action="store_true", help="Detect all pico devices and return a list")

    repl_parser.add_argument("device", help="Serial device")

    ls_parser.add_argument("device", help="Serial device")
    ls_parser.add_argument("path", help="Folder to list", default="/", nargs="?")

    rm_parser.add_argument('device', help="Serial device")
    rm_parser.add_argument('-r', '--recursive', action='store_true', help="Delete directory and contents")
    rm_parser.add_argument('path', help="File/folder to delete")

    mkdir_parser.add_argument("device", help="Serial device")
    mkdir_parser.add_argument("folder_path", help="Folder path to create")
    mkdir_parser.add_argument("--overwrite", action="store_true", help="Overwrite the file if it exists")

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

    attach_parser.add_argument('device', help="Serial device")

    reboot_parser.add_argument("device", help="Serial device")

    # Re-parse with the remaining arguments
    args = parser.parse_args(remaining_argv, namespace=args)
    
    return args


def main():
    LOGGER.setLevel(logging.INFO)
    args = get_args()

    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)

    attach_only = args.command in ["attach"]

    if device := getattr(args, 'device', False):
        pico = Pico(
            serial_port=device,
            skip_coms_test=attach_only, # Skip testing coms if code should be already running
            skip_stop_exec=attach_only,
        )
    else:
        pico = False

    match args.command:
        case "repl":
            pico.start_repl()
        case "cat":
            try:
                pico.cat_file(args.file)
            except FileNotFoundError as err:
                LOGGER.error(f"File not found {args.file}")
                sys.exit(1)
        case "ls":
            for file in pico.get_file_list(args.path):
                print(file) # Print file list to stdout
        case "rm":
            remote_path = Path(args.path)
            try:
                pico.delete_path(remote_path, args.recursive)
            except FileNotFoundError:
                LOGGER.error(f"File not found {args.path}")
                sys.exit(1)
        case "mkdir":
            remote_path = Path(args.folder_path)
            try:
                pico.create_directory(remote_path, args.overwrite)
            except FileExistsError:
                LOGGER.error(f"Directory already exists {args.folder_path}")
                sys.exit(1)
        case "stop":
            pass # Technically just opening it successfully will stop it
        case "upload":
            with open(args.read_file, "rb") as read_file:
                try:
                    pico.upload_file(read_file, args.file, overwrite=args.overwrite)
                except FileExistsError as err:
                    LOGGER.error(err)
                    sys.exit(2)
        case "download":
            try:
                with open(args.save_file, "w") as save_file:
                    pico.download_file(args.file, save_file)
            except FileNotFoundError as err:
                LOGGER.error(err)
                sys.exit(1)
        case "exec":
            LOGGER.debug(f"Executing {args.file}")
            pico.execute_file(args.file)
        case "detect":
            if args.all:
                detected = get_all_pico_serial()
            else:
                detected = get_first_pico_serial()
            print(detected) # show device to stdout
        case "attach":
            try:
                pico.start_console_attach()
            except KeyboardInterrupt:
                LOGGER.info("Received KeyboardInterrupt. Exiting...")
        case "reboot":
            pico.send_soft_reboot()

if __name__ == "__main__":
    main()