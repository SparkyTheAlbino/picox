import serial
import ast
import time
import re
import platform
from enum import Enum
from typing import IO, Optional
from itertools import cycle


# Constants for communication patterns
TERMINATOR = '\r\n'  
UPY_PROMPT = "\r\n>>>"  
BLOCK_PROMPT = "..."  
EOR_MARKER = "---f81b734f-7be3-4747-ae0b-c449006b33dd---"
EOR_TOKEN  = f"{EOR_MARKER}{UPY_PROMPT}"
EOR_MARKER_COMMAND = f";print('{EOR_MARKER}')"
EOM_MARKER = f';pass;pass;pass;pass{EOR_MARKER_COMMAND}'
RE_MATCH_BACKSPACE_BEGINNING = re.compile('^' + re.escape("\x08") + '+')

class MicroPython_Version(Enum):
    """Enumeration of supported MicroPython versions."""
    v1_21_0 = "1.21.0"

class RP2040:
    """Manage communications with a MicroPython RP2040 device via serial."""
    def __init__(self, serial_port: str, micropython_version: MicroPython_Version = MicroPython_Version.v1_21_0, start_closed: bool=False, verbose: bool=False, serial_read_timeout: int=15, serial_write_timeout: Optional[int]=None):
        self.verbose = verbose
        self._serial_read_timeout = serial_read_timeout
        self._serial_write_timeout = serial_write_timeout
        self._upy_version = micropython_version
        self._serial_port = serial_port
        self._serial = None
        if not start_closed:
            self._open_serial()

    def _open_serial(self):
        """Initializes the serial connection with the specified parameters."""
        self._serial = serial.Serial(
            port=self._serial_port, 
            baudrate=115200, 
            timeout=self._serial_read_timeout,
            write_timeout=0.5
        )

    def _serial_read(self, eor_token: str = EOR_TOKEN) -> bytearray:
        """Reads from serial until the end-of-response token is encountered."""
        response = self._serial.read_until(eor_token.encode("utf8")).strip()
        if self.verbose:
            print(f"RECV {self._serial_port} :: {response}")
        return response

    def _repl_read(self, wait_interval: float = 0.2) -> str:
        """Attempts to read from the REPL prompt"""
        response = ""
        end_markers = (UPY_PROMPT, BLOCK_PROMPT)
        self._serial.timeout = wait_interval
        start_time = time.monotonic()

        for end_marker in cycle(end_markers):
            if (time.monotonic() - start_time) > self._serial_read_timeout:
                break
            try:
                response += self._serial_read(eor_token=end_marker).decode("utf-8")
            except serial.SerialTimeoutException:
                pass
            else:
                time.sleep(0.1)
                if not self._serial.in_waiting:
                    break

        self._serial.timeout = self._serial_read_timeout
        if not response:
            raise serial.SerialTimeoutException("Timeout while reading from serial.")
        return response

    def _serial_write(self, command: bytes):
        """Writes a command to the serial port after clearing the input and output buffers."""
        self._serial.reset_output_buffer()
        self._serial.reset_input_buffer()
        if self.verbose:
            print(f"SEND {self._serial_port} :: {command}")
        self._serial.write(command)

    def _extract_response_payload(self, response: str, start_marker: str, end_marker: str) -> Optional[str]:
        """Extracts a payload from a response delimited by specified start and end markers."""
        last_start_index = response.rfind(start_marker)
        if last_start_index == -1:
            return ""
        start_index = last_start_index + len(start_marker)

        last_end_index = response.rfind(end_marker)
        if last_end_index == -1 or last_end_index < start_index:
            # Could not find end tag - lets see if we can find the UPY prompt
            if response.endswith(UPY_PROMPT):
                return response[start_index:]
            else:
                return "" # Could not find a valid end marker
        
        return response[start_index:last_end_index]

    def _clean_response(self, response: str) -> str:
        """Cleans up the response string from a MicroPython device to remove unnecessary prompts and markers."""
        response = self._extract_response_payload(response, EOM_MARKER, EOR_MARKER)
        response = response.lstrip()

        if platform.system() == "Windows":
            response = response.replace("\r\r\n", "\n")
        if response.startswith(BLOCK_PROMPT):
            response = response[6:]
        if response.endswith("\r\n"):
            response = response[:-2] # Take only the last newline off
        return response

    def _communicate(self, command: str, is_block_command: bool = False, ignore_response: bool = False) -> Optional[str]:
        """Handles the sending and receiving of a command to/from the MicroPython device."""
        command += EOM_MARKER + TERMINATOR
        if is_block_command:
            command += TERMINATOR

        self._serial_write(command.encode("utf8"))

        if not ignore_response:
            if response := self._serial_read().decode():
                return self._clean_response(response)
            else:
                raise Exception("No response when expected")
        return None

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

        if pico_filename not in self.get_file_list():
            raise FileNotFoundError(f"File '{pico_filename}' does not exist on Pico")

        file_data = self._communicate(
            f'with open("{pico_filename}", "r") as f: print(f.read(), end="")',
            is_block_command=True
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
            is_block_command=True
        )

    def execute_file(self, file_name):
        print(f"Executing file {file_name}")
        self.stop_exec()
        return self._communicate(f'exec(open("{file_name}").read())', ignore_response=True)

    def start_repl(self):
        if platform.system == "Windows":
            import pyreadline3
        else:
            import readline # Required import to support cursor navigation with inputs

        self.stop_exec()
        self.soft_reboot()

        # Read serial here to get prompt
        prompt = self._serial_read(eor_token=UPY_PROMPT).decode("utf-8")
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