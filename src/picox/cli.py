import argparse
import logging
import sys
import os
from pathlib import Path

from .upy import Pico
from .exceptions import RemotePicoError
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
    upload_parser.add_argument("read_file", help="Local file to upload")
    upload_parser.add_argument("file", help="Save name for file to upload")
    upload_parser.add_argument('-r', '--recursive', action='store_true', help="Upload directory recursively")
    upload_parser.add_argument("--overwrite", action="store_true", help="Overwrite the file if it exists")

    download_parser.add_argument("device", help="Serial device")
    download_parser.add_argument("file", help="Remote file on device to download")
    download_parser.add_argument("save_file", help="Local location to save to")
    download_parser.add_argument('-r', '--recursive', action='store_true', help="Download directory recursively")
    download_parser.add_argument("--overwrite", action="store_true", help="Overwrite the file if it exists")

    exec_parser.add_argument("device", help="Serial device")
    exec_parser.add_argument("file", help="File to execute")

    stop_parser.add_argument("device", help="Serial device")

    attach_parser.add_argument('device', help="Serial device")

    reboot_parser.add_argument("device", help="Serial device")

    # Re-parse with the remaining arguments
    args = parser.parse_args(remaining_argv, namespace=args)
    
    return args

def process_command(pico: Pico, args: argparse.Namespace):
    match args.command:
        case "repl":
            pico.start_repl()
        case "cat":
            try:
                pico.cat_file(args.file)
            except RemotePicoError as err:
                sys.exit(1)
        case "ls":
            try:
                file_list = pico.get_file_list(args.path)
            except RemotePicoError as err:
                sys.exit(1)
            for file in file_list:
                print(file)
        case "rm":
            remote_path = Path(args.path)
            try:
                pico.delete_path(remote_path, args.recursive)
            except RemotePicoError as err:
                sys.exit(1)
        case "mkdir":
            remote_path = Path(args.folder_path)
            try:
                pico.create_directory(remote_path, args.overwrite)
            except RemotePicoError as err:
                sys.exit(1)
        case "stop":
            pass # Technically just opening it successfully will stop it
        case "upload":
            try:
                is_directory = os.path.isdir(args.read_file)
            except FileNotFoundError:
                LOGGER.error(f"File/Folder not found: {args.read_file}")
                sys.exit(1)

            if is_directory and not args.recursive:
                raise ValueError("Directory upload requires -r/--recursive flag")
            
            # TODO handle recursive upload
            if is_directory:
                pico.upload_folder(args.read_file, args.file, overwrite=args.overwrite)
            else:
                with open(args.read_file, "rb") as read_file:
                    try:
                        pico.upload_file(read_file, args.file, overwrite=args.overwrite)
                    except RemotePicoError as err:
                        sys.exit(1)
        case "download":
            # Check if file/folder to download to exists and not in override mode
            if not args.override and os.path.exists(args.save_file):
                LOGGER.error(f"File/Folder already exists: {args.save_file}")
                sys.exit(1)
            
            # Directory download requires recursive flag
            if os.path.isdir(args.save_file) and not args.recursive:
                raise ValueError("Directory download requires -r/--recursive flag")
            
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    source_path = os.path.join(root, file)
                    destination_path = os.path.join(destination_folder, os.path.relpath(source_path, source_folder))
                    
                    # Create directories if they don't exist
                    destination_dir = os.path.dirname(destination_path)
                    if not os.path.exists(destination_dir):
                        os.makedirs(destination_dir)
                    
                    # Write the file
                    with open(destination_path, 'w') as destination_file:
                        with open(source_path, 'r') as source_file:
                            destination_file.write(source_file.read())

            #TODO handle recursive download
            try:
                with open(args.save_file, "w") as save_file:
                    pico.download_file(args.file, save_file)
            except RemotePicoError as err:
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


def main():
    LOGGER.setLevel(logging.INFO)
    args = get_args()

    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)

    # IF attach command, then set the flag to avoid closing what is already running
    attach_only = args.command in ["attach"]

    # If we have a 'device' in our command, we need to create a Pico object
    if device := getattr(args, 'device', False):
        pico = Pico(
            serial_port=device,
            skip_coms_test=attach_only, # Skip testing coms if code should be already running
            skip_stop_exec=attach_only,
        )
    else:
        pico = False

    process_command(pico, args)

if __name__ == "__main__":
    main()