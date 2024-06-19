# Auto-generated with compile.py at 2024-06-19 20:36:59.707075+00:00

# src/raw_commands/DOWNLOAD_FILE.py
DOWNLOAD_FILE = lambda pico_filename : f"exec('try:\\n    with open(\\\'{pico_filename}\\\', \\\'r\\\') as f:\\n        print(f.read(), end=\\\'\\\')\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR\\\")')"

# src/raw_commands/CREATE_DIR.py
CREATE_DIR = lambda directory : f"exec('try:\\n    import os\\n    os.mkdir(\\\"{directory}\\\")\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR\\\")')"

# src/raw_commands/UPLOAD_FILE.py
UPLOAD_FILE = lambda hex_data, pico_file_path : f"exec('try:\\n    decoded_data = bytes.fromhex(\\\'{hex_data}\\\')\\n    with open(\\\"{pico_file_path}\\\", \\\"wb\\\") as f: \\n        f.write(decoded_data)\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR\\\")')"

# src/raw_commands/DELETE_PATH.py
DELETE_PATH = lambda is_recursive, folder_path : f"exec('try:\\n    import os\\n    recursive = {is_recursive}\\n    item_path = \\\"{folder_path}\\\"\\n    if recursive:\\n        for root, dirs, files in os.walk(item_path, topdown=False):\\n            for name in files:\\n                os.remove(os.path.join(root, name))\\n            for name in dirs:\\n                os.rmdir(os.path.join(root, name))\\n        os.rmdir(item_path)\\n    else:\\n        os.remove(item_path)\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR\\\")')"