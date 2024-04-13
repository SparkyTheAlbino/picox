# piconnect
`piconnect` is a tool that facilitates the interaction with Raspberry Pi Pico running MicroPython boards through (CLI) or within a Python script. This uses the USB serial port for communication.

Windows, Linux and macOS are supported.

## Features
- Detect a connected Raspberry Pi Pico device running MicroPython
- REPL session
- File operations: Upload, download, execute, and list files on Pi Pico
- Stop current execution on device

## Installation
Install via `pip`:

``` bash 
pip install piconnect
```


## CLI Usage


### Detecting Pi Pico:
``` bash
piconnect detect

# Output: COM7 or /dev/ttyUSB0
```

### REPL session on Pi Pico
``` bash
piconnect repl /dev/ttyUSB0
```

### Listing files on Pi Pico:
``` bash
piconnect ls /dev/ttyUSB0

# exmaple output:
# demo.py
# home.py
```

### Uploading a file:
``` bash
piconnect upload  /dev/ttyUSB0 local.py remote.py --overwrite

# --overrite to force update the file on the Pi Pico
```

### Downloading a file:
``` bash
piconnect download /dev/ttyUSB0 remote.py local.py
```

### Executing a file on Pi Pico:
``` bash
piconnect exec /dev/ttyUSB0 remote.py
```

### Stopping any ongoing operation on Pi Pico:
``` bash
piconnect stop /dev/ttyUSB0
```


## Python Script Usage
You can also use piconnect within your Python scripts as follows:

``` python
from piconnect import RP2040

# Initialize the Pico board
pico = RP2040('/dev/tty.usbmodem0001')

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

## Local developmnt
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