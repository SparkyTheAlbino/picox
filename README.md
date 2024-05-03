# picox
`picox` is a tool that facilitates the interaction with Raspberry Pi Pico running MicroPython boards through the terminal or within a Python script. This uses the USB serial port for communication.

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
- Most commands will halt what is running on the pico. Such as a detect will stop execution in order to get a good communication test. For a more manual detection, you can use `picox attach <device>` to try and stream stdout from the pico

## Installation
Install via `pip`:

``` bash 
pip install picox
```


## CLI Usage


### Detecting Pi Pico:
``` bash
# get first found device
picox detect

# get a list of all connected pico devices
pico detect --all

# Output: COM7 or /dev/ttyUSB0
```

### REPL session on Pi Pico
``` bash
picox repl /dev/ttyUSB0
```

### View console output from already running pico
``` bash
picox attach /dev/ttyUSB0
```

### Soft reboot pico
``` bash
picox reboot /dev/ttyUSB0
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
picox upload /dev/ttyUSB0 local.py remote.py --overwrite

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
from picox import Pico
from picox.detect import get_first_pico_serial


# Init device
serial_device = get_first_pico_serial()
pico = Pico(serial_device)

# File listing
for file in pico.get_file_list():
    print(file)

# Download
with open("./local/demo.py", "w") as download_file:
    pico.download_file("remote_demo.py", download_file)

# Upload
with open("./local/demo.py", "rb") as upload_file:
    pico.upload_file(upload_file, "remote_demo.py", overwrite=True)

# Execute
pico.execute_file("remote_demo.py")

# Halt execution on device
pico.stop_exec()

# Soft reboot device
pico.send_soft_reboot()
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