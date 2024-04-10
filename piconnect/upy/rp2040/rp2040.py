import serial
import ast
import time
import re
from enum import Enum
from typing import IO
from itertools import cycle

TERMINATOR = '\r\n'     # Newlines, for terminating a message or simulating an "enter"
MPY_PROMPT = "\r\n>>>"  # New prompt, for looking when serial coms is finsihed
BLOCK_PROMPT = "..."   # Block command prompt
EOR_MARKER = "---f81b734f-7be3-4747-ae0b-c449006b33dd---" # A Special tag to aid finding the end of response
EOR_TOKEN  = f"{EOR_MARKER}{MPY_PROMPT}" # Token to look for to end reading from serial
EOR_MARKER_COMMAND = f";print('{EOR_MARKER}')" # Add this to ensure the special tag is printed at the end of the response
EOM_MARKER = f';pass;pass;pass;pass{EOR_MARKER_COMMAND}' # End of message marker to remove it easily from the response
RE_MATCH_BACKSPACE_BEGINNING = re.compile('^' + re.escape("\x08") + '+')

class MicroPython_Version(Enum):
    v1_21_0 = "1.21.0"


class RP2040:
    def __init__(self, 
                 serial_port: str, 
                 micropython_version: MicroPython_Version = MicroPython_Version.v1_21_0, 
                 start_closed=False, 
                 verbose=False,
                 serial_read_timeout=15,
                 serial_write_timeout=1,
                 ):
        self.verbose = verbose
        self._serial_read_timeout = serial_read_timeout
        self._upy_version = micropython_version
        self._serial_port = serial_port
        self._serial = None
        if not start_closed:
            self._open_serial()

    def _open_serial(self):
        self._serial = serial.Serial(
            self._serial_port, 
            115200, 
            timeout=self._serial_read_timeout,
            write_timeout=0.5
        )

    def _serial_read(self, eor_token=EOR_TOKEN) -> bytearray:
        response = self._serial.read_until(eor_token.encode("utf8")).strip()
        if self.verbose:
            print(f"RECV {self._serial_port} :: {response}")
        return response

    def _repl_read(self, wait_interval=0.2) -> str:
        """ Try to read rapidly to find the end """
        response = "" # Final response
        end_markers = (MPY_PROMPT, BLOCK_PROMPT)
        self._serial.timeout = wait_interval # Read quickly to find the correct prompt
        start_time = time.monotonic()

        for end_marker in cycle(end_markers):
            # Check if we have waited too long
            if (time.monotonic() - start_time) > self._serial_read_timeout:
                break

            # Seek for a response marker
            try:
                response += self._serial_read(eor_token=end_marker).decode("utf-8")
            except serial.SerialTimeoutException:
                pass # don't care about timeouts for now
            else:
                # Got a response, check if there are any more bytes to read
                time.sleep(0.2)
                if not self._serial.in_waiting:
                    break

        self._serial.timeout = self._serial_read_timeout
        if not response:
            raise serial.SerialTimeoutException
        return response

    def _serial_write(self, command: bytes):
        self._serial.reset_output_buffer()
        self._serial.reset_input_buffer()
        if self.verbose:
            print(f"SEND {self._serial_port} :: {command}")
        self._serial.write(command)

    def _clean_response(self, response: str, command, extras: set = None) -> str:
        if extras is None:
            extras = set()

        response = response.strip()
        response = response.replace(f"{command}", "") # Remove echoed command
        for extra in extras:
            response = response.replace(f"{extra}", "") # Remove any extras (Such as block_command altering the EOM)
        if response.endswith(EOR_TOKEN):
            response = response[:-len(EOR_TOKEN)] # Remove EOR marker and prompt
        if response.startswith(BLOCK_PROMPT):
            response = response[6:] # Remove starting dots created by block commands
        return response.strip()

    def _communicate(self, 
                     command: str, 
                     block_command: bool = False,
                     ignore_response: bool = False
                     ):
        """ Perform Write and Read of the serial with filtering to get just the output 
            Block commands are ones that would require an indented level such as a with or for statement
        """
        extra_clean = set()
        response = None
        if block_command:
            # More needed for cleaning after the response due to the MPY prompt not being returned here
            extra_clean.add(f"{command}{EOM_MARKER}{TERMINATOR}{BLOCK_PROMPT}{TERMINATOR}")
            command = f"{command}{EOM_MARKER}{TERMINATOR}{TERMINATOR}"
        else:
            command = f"{command}{EOM_MARKER}{TERMINATOR}"

        self._serial_write(command.encode("utf8"))
        if not ignore_response:
            response = self._serial_read().decode()
            response = self._clean_response(response, command, extras=extra_clean)

        return response

    def get_file_list(self):
        """ Get a list of files stored on the device """
        string_list = self._communicate('import os; os.listdir()')
        
        # Ensure response looks like a list
        if not string_list:
            raise RuntimeError("Empty response from Pico")
        if string_list[0] != "[" and string_list[-1] != "]":
            raise RuntimeError(f"Did not get back a list from file listing command :: {string_list}")
        else:
            return ast.literal_eval(string_list) if string_list else []

    def stop_exec(self):
        """ Send keyboard interrupt to stop execution """
        self._serial_write(b'\x03')  # Ctrl+C -> stop execution
        time.sleep(0.2) # Give the device time to respond and be flushed

    def soft_reboot(self):
        """ Send soft reboot command (Ctrl+D) """
        self._serial_write(b'\x04')  # Ctrl+D -> Soft reboot if nothing executing and blank REPL
        time.sleep(0.2) # Give the device time to respond and be flushed

    def send_enter(self):
        """ Send a blank enter to exit a block statement """
        self._serial_write(b'\r\n')
        time.sleep(0.2) # Give the device time to respond and be flushed

    def coms_test(self):
        response = self._communicate("x = 1 + 1; print(x)")
        return response == "2"

    def run_python_command(self, command, block_command=False):
        """ Run a generic python command """
        return self._communicate(command, block_command)

    def download_file(self, pico_filename, save_fp: IO[str]):
        """ Download a file from the Pico to the host """
        file_data = self._communicate(
            f'with open("{pico_filename}", "r") as f: print(f.read(), end="")',
            block_command=True
        )
        save_fp.write(file_data)

    def upload_file(self, local_fp: IO[bytes], pico_file_path, overwrite=False):
        """ Upload a file from the host to the Pico """
        if pico_file_path in self.get_file_list():
            if not overwrite:
                raise FileExistsError(f"File '{pico_file_path}' already exists on the Pico. Set overwrite=True to overwrite.")
            else:
                self._communicate(f"import os; os.remove('{pico_file_path}')")

        # Read the file data from the host
        local_data = local_fp.read()

        # Upload the file to the pico
        self._communicate(
            f'with open("{pico_file_path}", "wb") as f: f.write({local_data})',
            block_command=True
        )

    def execute_file(self, file_name):
        print(f"Executing file {file_name}")
        self.stop_exec()
        return self._communicate(f'exec(open("{file_name}").read())', ignore_response=True)

    def start_repl(self):
        import readline # Required import to support cursor navigation with inputs

        self.stop_exec()
        self.soft_reboot()

        # Read serial here to get prompt
        prompt = self._serial_read(eor_token=MPY_PROMPT).decode("utf-8")
        while True:
            raw_command = input(f"{prompt} ")
            if raw_command == "exit()":
                raise SystemExit

            command = f"{raw_command}\r" # Add an enter to submit
            self._serial_write(command.encode("utf-8"))
            prompt = self._repl_read()
            prompt = re.sub(RE_MATCH_BACKSPACE_BEGINNING, "", prompt)
            #prompt = self._serial_read(eor_token=end_token).decode("utf-8")
            # TODO do another quicker read to see if there is anything in the in-buffer, Ensures we caught the end rather than some output from command
            prompt = prompt.replace(raw_command.strip(), "").strip()