# picox
`picox` is a tool that facilitates the interaction with Raspberry Pi Pico running MicroPython boards through (CLI) or within a Python script. This uses the USB serial port for communication.

Windows, Linux and macOS are supported.

## Features
- Detect a connected Raspberry Pi Pico device running MicroPython
- REPL session
- File operations: Upload, download, execute, and list files on Pi Pico
- Stop current execution on device

## Known issues
- REPL can timeout on long operations such as sleep. Its in the nature of how it scans for the end
- Line endings of files coming out can get a little strange. watch out if there are som extra spaces etc. Best bet is to ensure you always work in the same line endings
- File operations do not include folder operations __yet__

## Installation
Install via `pip`:

``` bash 
pip install picox
```


## CLI Usage


### Detecting Pi Pico:
``` bash
picox detect

# Output: COM7 or /dev/ttyUSB0
```

### REPL session on Pi Pico
``` bash
picox repl /dev/ttyUSB0
```

### Listing files on Pi Pico:
``` bash
picox ls /dev/ttyUSB0

# exmaple output:
# demo.py
# home.py
```

### Uploading a file:
``` bash
picox upload  /dev/ttyUSB0 local.py remote.py --overwrite

# --overrite to force update the file on the Pi Pico
```

### Downloading a file:
``` bash
picox download /dev/ttyUSB0 remote.py local.py
```

### Executing a file on Pi Pico:
``` bash
picox exec /dev/ttyUSB0 remote.py
```

### Stopping any ongoing operation on Pi Pico:
``` bash
picox stop /dev/ttyUSB0
```


## Python Script Usage
You can also use picox within your Python scripts as follows:

``` python
from picox import RP2040
from picox.detect import get_serial_ports, scan_for_pico

# Get device
ports = get_serial_ports()
pico_port = scan_for_pico(ports)

# Initialize the Pico board
pico = RP2040(pico_port)

# Coms test
if not pico.coms_test():
    print("Coms test failed. Try re-inserting the Pi Pico USB")

# List files
print(pico.get_file_list())

# Upload a file
with open("local.py", "rb") as file:
    pico.upload_file(file, "remote.py")

# Download a file
with open("local.py", "w") as save_file:
    pico.download_file("remote.py", save_file)

# Execute a file
pico.execute_file("remote.py")

# Run basic python commands
pico.run_python_command("x = 1 + 1; print(x)")
```

## Local development
1. Create virtual env
``` bash
python -m venv _env
```
2. Activate env
``` bash
# Win
_env/Scripts/activate.ps1
# nix
source _env/bin/activate
```
3. Install requirements
``` bash
pip install -r requirement.txt
```
4. Install module editable
```
pip install -e .
```