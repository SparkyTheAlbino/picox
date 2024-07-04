import os

recursive = "{is_recursive}"
item_path = "{item_path}"

recursive = True if recursive == "True" else False

S_IFDIR = 0o040000  # directory type

def S_IFMT(mode): # Format mode to get file type
    return mode & 0o170000

def S_ISDIR(mode): # Is a directory?
    return S_IFMT(mode) == S_IFDIR

def delete_files_and_dirs(path, recursive=True):
    """Delete files and directories at a given path."""
    if recursive and S_ISDIR(os.stat(path)[0]):
        # List all items in the directory
        items = os.listdir(path)
        # Recursively delete each item
        for item in items:
            full_path = '/'.join([path, item])
            delete_files_and_dirs(full_path, recursive)
        
        # After all items are deleted, remove the directory
        os.rmdir(path)
    else:
        # If it's a file, remove it
        os.remove(path)

delete_files_and_dirs(item_path, recursive)