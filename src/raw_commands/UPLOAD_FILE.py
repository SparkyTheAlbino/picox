import os

hex_data = "{hex_data}"
pico_file_path = "{pico_file_path}"
overwrite = "{overwrite}"
overwrite = True if overwrite == "True" else False

# Check file existance
S_IFDIR = 0o040000  # directory type

def S_IFMT(mode): # Format mode to get file type
    return mode & 0o170000

def S_ISDIR(mode): # Is a directory?
    return S_IFMT(mode) == S_IFDIR


try:
    # Does path exist already?
    file_stat = os.stat(pico_file_path)[0]
    # Is this path a directory?
    if S_ISDIR(file_stat):
        raise ValueError(f"{pico_file_path} is a directory. Aborting upload.")
    # If not a directory, then can we overwrite it?
    if overwrite:
        os.remove(pico_file_path)
    else:
        raise ValueError(f"File {pico_file_path} already exists! Set '--overwrite' to delete it and create a new one.")
except OSError:
    pass # File does not exist

decoded_data = bytes.fromhex(hex_data)
with open(pico_file_path, "wb") as f: 
    f.write(decoded_data)
print("File uploaded successfully!")