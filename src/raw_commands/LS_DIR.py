import os

path = "{directory}"


S_IFDIR = 0o040000  # directory type

def S_IFMT(mode): # Format mode to get file type
    return mode & 0o170000

def S_ISDIR(mode): # Is a directory?
    return S_IFMT(mode) == S_IFDIR

# Check if directory actually exists
try:
    os.stat(path)
except OSError:
    raise OSError(f"{path} does not exist!")

# Check if path is a directory
if not S_ISDIR(os.stat(path)[0]):  # If item not is a directory
    raise OSError(f"{path} is not a directory!")

# List all items in the directory
print(os.listdir(path))