import ast
import time
import re
import platform
from enum import Enum
from typing import IO, Optional, List
from pathlib import Path
from io import StringIO

import serial

from .exceptions import RemotePicoException
from .logconfig import LOGGER
from .commands.compiled import DOWNLOAD_FILE, UPLOAD_FILE

# Constants for communication patterns
TERMINATOR = '\r\n'  
UPY_PROMPT = "\r\n>>>"  
BLOCK_PROMPT = "..."  
EOR_MARKER = "---f81b734f-7be3-4747-ae0b-c449006b33dd---"
EOR_TOKEN  = f"{EOR_MARKER}{UPY_PROMPT}"
EOR_MARKER_COMMAND = f";print('{EOR_MARKER}')"
EOM_MARKER = f';pass;pass;pass;pass{EOR_MARKER_COMMAND}'
FAILED_MARKER = f"FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR"
RE_MATCH_BACKSPACE_BEGINNING = re.compile('^' + re.escape("\x08") + '+')


class MicroPython_Version(Enum):
    """Enumeration of supported MicroPython versions."""
    v1_21_0 = "1.21.0"


class Pico:
    """Manage communications with a MicroPython RP2040 device via serial."""
    def __init__(self, 
                 serial_port: str, 
                 micropython_version: MicroPython_Version = MicroPython_Version.v1_21_0, 
                 start_closed: bool=False,
                 skip_stop_exec: bool=False,
                 skip_coms_test: bool=False,
                 serial_read_timeout: int=15, 
                 serial_write_timeout: Optional[int]=None
                 ):
        """
        New RP2040 device running MicroPython.
        args:
            serial_port (str): serial device of Pico
            micropython_version (str): Version of MicroPython on device. Does not currently matter
            start_closed (bool): Creates object without opening the serial port
            skip_stop_exec (bool): Skip stopping execution of pico running code. Good if your Pico has a main autoexec script
            skip_coms_test (bool) : Skip a coms test that verifies the coms is good between the computer and Pico
            serial_read_timeout (int): Read timeout supplied to serial.Serial
            serial_write_timeout (int): Write timeout supplied to serial.Serial
        """
        self._serial_read_timeout = serial_read_timeout
        self._serial_write_timeout = serial_write_timeout
        self._upy_version = micropython_version
        self._serial_port = serial_port
        self._serial = None
        if not start_closed:
            # Open the serial device here
            self._open_serial()

            # Send stop and reboot to reset Pico state
            if not skip_stop_exec:
                self.stop_exec()
                self._serial.reset_output_buffer()
                self._serial.reset_input_buffer()

            # Run a sanity test to ensure the serial device responds as expected (e.g. does it run micropython)
            if not skip_coms_test:
                if not self.coms_test():
                    raise IOError("Did not get expected response from device during coms test")

    def _open_serial(self):
        """Initializes the serial connection with the specified parameters."""
        self._serial = serial.Serial(
            port=self._serial_port, 
            baudrate=115200, 
            timeout=self._serial_read_timeout,
            write_timeout=0.5
        )

    def _serial_read(self, end_markers: List[str] = None, command_failed_marker: str = FAILED_MARKER) -> bytearray:
        """
        Read from serial byte-by-byte and check if we hit an end marker
        """
        if not end_markers:
            end_markers = [EOR_TOKEN] # Default to end of response marker

        max_failed_marker_occurances = 2 # Failure marker will show once in the command and once again if failed
        failed_marker_occurances = 0 # Count times encountered failure markers

        end_markers_encoded = list(map(lambda marker: marker.encode('utf-8'), end_markers))
        failed_marker_encoded = command_failed_marker.encode('utf-8')

        recv_buffer = b''
        while True:
            recv_bytes = self._serial.read()
            if not recv_bytes:
                break # did not recv any bytes

            recv_buffer += recv_bytes
            LOGGER.debug(f"RECV(part) {self._serial_port} :: {recv_buffer}")

            # Check if the buffer ends with any of the markers
            if any(recv_buffer.endswith(end_marker) for end_marker in end_markers_encoded):
                break

            # Check if the error marker has been hit
            if recv_buffer.endswith(failed_marker_encoded):
                failed_marker_occurances += 1
                if failed_marker_occurances >= max_failed_marker_occurances:
                    break
    
        recv_buffer = recv_buffer.strip()
        LOGGER.debug(f"RECV {self._serial_port} :: {recv_buffer}")
        return recv_buffer
    
    def _serial_read_endless(self):
        """Endless read from serial, useful for viewing all console output"""
        self._serial.timeout = 0
        while True:
            if data_from_serial := self._serial.read(self._serial.in_waiting or 1).decode("utf-8"):
                print(f"{data_from_serial}")
            else:
                time.sleep(0.05)

    def _serial_write(self, command: bytes):
        """Writes a command to the serial port after clearing the input and output buffers."""
        LOGGER.debug(f"SEND {self._serial_port} :: {command}")
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
            # Windows does odd things with line endings
            response = response.replace("\r\r\n", "\n")
        if response.startswith(BLOCK_PROMPT):
            # Block prompt can add '...', spaces and newlines
            try:
                # Sometimes this part can be a char out!
                if response[5].isspace():
                    response = response[6:]
                else:
                    response = response[5:]
            except IndexError as err:
                raise ValueError(f'Unable to parse response :: {err}')
        if response.endswith("\r\n"):
            response = response[:-2] # Take only the last newline off
        return response

    def _communicate(self,
                     command: str, 
                     is_block_command: bool = False, 
                     ignore_response: bool = False
                     ) -> Optional[str]:
        """Handles the sending and receiving of a command to/from the MicroPython device."""
        command += EOM_MARKER + TERMINATOR
        if is_block_command:
            command += TERMINATOR

        self._serial.reset_output_buffer()
        self._serial.reset_input_buffer()

        self._serial_write(command.encode("utf8"))

        if not ignore_response:
            if response := self._serial_read().decode():
                # Did the response show an exception on the Pico?
                if response.endswith(FAILED_MARKER):
                    raise RemotePicoException("Detected exception from device", response)
                
                # Good response, Get the payload and return it
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
        """ Stop execution by a combinatino of reboot and Ctrl+C. Flushes buffers afterwards to get device in known state """
        self._send_stop_exec(quantity=5)
        self.send_soft_reboot()
        time.sleep(0.2)
        self._send_stop_exec(quantity=5) # If there is an auto boot script, this will clear it
        time.sleep(0.2)
        self._send_enter()

    def _send_stop_exec(self, quantity=1):
        """ Send keyboard interrupt to stop execution 
        args:
            quantity (int) : How many Ctrl+C to send
        """
        LOGGER.debug("Sending stop exec (Ctrl+C) to Pico")
        for _ in range(quantity):
            self._serial_write(b'\x03')  # Ctrl+C -> stop execution

    def send_soft_reboot(self):
        """ Send soft reboot command (Ctrl+D) """
        LOGGER.debug("Sending soft reboot to Pico (Ctrl+D)")
        self._serial_write(b'\x04')  # Ctrl+D -> Soft reboot if nothing executing and blank REPL

    def _send_enter(self):
        """ Send a blank enter to exit a block statement """
        self._serial_write(b'\r\n')
        
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

        try:
            file_data = self._communicate(
                DOWNLOAD_FILE(pico_filename)
            )
        except RemotePicoException as err:
            LOGGER.error(f"Upload was not successful: {err}")
        else:
            # Fix line endings to \n and write to file!
            source = StringIO(file_data)
            normalized_lines = []
            for line in source:
                line = line.rstrip('\r\n') + '\n'
                normalized_lines.append(line)
            save_fp.write(''.join(normalized_lines))

    def create_directory(self, path: Path, overwrite=False):
        if str(path) in self.get_file_list():
            if not overwrite:
                raise FileExistsError(f"'{path}' already exists on the Pico. Set overwrite=True to overwrite.")
        
        result = self._communicate(f"import os; os.mkdir('{path}')")
        LOGGER.debug(f"Response from mkdir: {result}")
        if "Traceback" in result:
            LOGGER.error(f"Pico raised Exception during upload :: {result}")

    def upload_file(self, local_fp: IO[str], pico_file_path, overwrite=False):
        """ Upload a file from the host to the Pico """
        if pico_file_path in self.get_file_list():
            if not overwrite:
                raise FileExistsError(f"File '{pico_file_path}' already exists on the Pico. Set overwrite=True to overwrite.")

        # Read the file data from the host
        local_data = local_fp.read()
        if not isinstance(local_data, bytes):
            raise ValueError(f"File is not open in binary format got {type(local_data)}")
        
        # Upload the file to the pico
        try:
            result = self._communicate(
                UPLOAD_FILE(local_data.hex(), pico_file_path)
            )
        except RemotePicoException as err:
            LOGGER.error(f"Upload was not successful: {err}")
            raise
        return result

    def execute_file(self, file_name):
        LOGGER.debug(f"Executing file {file_name}")
        self.stop_exec()
        return self._communicate(f'exec(open("{file_name}").read())', ignore_response=True)

    def start_console_attach(self):
        LOGGER.info(f"Starting console read from device {self._serial_port}...")
        self._serial_read_endless()

    def start_repl(self):
        end_markers = (UPY_PROMPT, BLOCK_PROMPT)

        # import readline to support familiar command input (arrows, history)
        if platform.system == "Windows":
            import pyreadline3
        else:
            import readline

        # Get the Pico in a known state
        self.stop_exec()
        self.send_soft_reboot()
        time.sleep(0.5)
        self._serial.reset_output_buffer()
        self._serial.reset_input_buffer()
        self.stop_exec()
        time.sleep(0.5)

        prompt = self._serial_read(end_markers=[UPY_PROMPT]).decode("utf-8")
        self._serial.reset_output_buffer()
        self._serial.reset_input_buffer()
        while True:
            raw_command = input(f"{prompt} ")
            if raw_command == "exit()":
                raise SystemExit
            
            command = f"{raw_command}\r" # Add an enter to submit
            self._serial_write(command.encode("utf-8"))

            prompt = self._serial_read(end_markers=end_markers).decode("utf-8")
            
            # Sometimes a backspace character appears at the left, remove it
            prompt = re.sub(RE_MATCH_BACKSPACE_BEGINNING, "", prompt)
            # Remove the command from the response
            prompt = prompt.replace(raw_command.strip(), "", 1).strip()

            self._serial.reset_output_buffer()
            self._serial.reset_input_buffer()