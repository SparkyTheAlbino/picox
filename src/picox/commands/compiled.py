# Auto-generated with compile.py at 2024-05-19 15:21:37.486884+00:00

# src/raw_commands/DOWNLOAD_FILE.py
DOWNLOAD_FILE = lambda pico_filename : f"exec('try:\\n    with open(\\\'{pico_filename}\\\', \\\'r\\\') as f:\\n        print(f.read(), end=\\\'\\\')\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR\\\")')"

# src/raw_commands/UPLOAD_FILE.py
UPLOAD_FILE = lambda hex_data, pico_file_path : f"exec('try:\\n    decoded_data = bytes.fromhex(\\\'{hex_data}\\\')\\n    with open(\\\"{pico_file_path}\\\", \\\"wb\\\") as f: \\n        f.write(decoded_data)\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---0dfe99a5-4543-4fc0-8986-5d7fd5e51d7b---ERROR\\\")')"