# Auto-generated with compile.py at 2024-05-10 21:26:18.949596+00:00

# src/raw_commands/DOWNLOAD_FILE.py
DOWNLOAD_FILE = lambda pico_filename : f"exec('try:\\n    with open(\\\'{pico_filename}\\\', \\\'r\\\') as f:\\n        print(f.read(), end=\\\'\\\')\\n    print(\\\"{{hello world}}\\\")\\n    x = 10\\n    print(f\\\"{{x}}\\\")\\n    print(f\\\"{{x}} - {{x + 40}}\\\")\\n\\nexcept Exception as e:\\n    print(f\\\"{{str(e)}}FAILED---f81b734f-7be3-4747-ae0b-c449006b33dd---ERROR\\\")')"