import os

pico_filename = "{pico_filename}"

# Check file existance
S_IFDIR = 0o040000  # directory type

def S_IFMT(mode): # Format mode to get file type
    return mode & 0o170000

def S_ISDIR(mode): # Is a directory?
    return S_IFMT(mode) == S_IFDIR


# Does path exist already?
try:
    file_stat = os.stat(pico_filename)[0]
except OSError:
    raise ValueError(f"{pico_filename} does not exist!")

# Is this path a directory?
if S_ISDIR(file_stat):
    raise ValueError(f"{pico_filename} is a directory. Aborting download.")

# All good, file exists and is not a directory
with open(pico_filename, 'r') as f:
    print(f.read(), end='')