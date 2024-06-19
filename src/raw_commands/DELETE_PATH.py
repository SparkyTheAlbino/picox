import os

recursive = {is_recursive}
item_path = "{folder_path}"

if recursive:
    for root, dirs, files in os.walk(item_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(item_path)
else:
    os.remove(item_path)

