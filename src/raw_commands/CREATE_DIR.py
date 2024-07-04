import os

overwrite = "{overwrite}"
directory = "{directory}"

overwrite = True if overwrite == "True" else False

S_IFDIR = 0o040000  # directory type

def S_IFMT(mode): # Format mode to get file type
    return mode & 0o170000

def S_ISDIR(mode): # Is a directory?
    return S_IFMT(mode) == S_IFDIR

def delete_dir(path):
    items = os.listdir(path)  # List all items in the directory

    for item in items:
        full_path = '/'.join([path, item]) 
        if S_ISDIR(os.stat(full_path)[0]):  # If item is a directory
            delete_dir(full_path)  # Recurse into the directory
            os.rmdir(full_path)  # Remove the directory after emptying it
        else:
            os.remove(full_path)  # Remove the file
    os.rmdir(path)  # Remove the top directory after all contents are deleted

if overwrite:
    delete_dir(directory)

try:
    if S_ISDIR(os.stat(directory)[0]):
        raise ValueError(f"Directory {directory} already exists! Set '--overwrite' to delete it and create a new one.")
except OSError:
    pass

os.mkdir(directory)
