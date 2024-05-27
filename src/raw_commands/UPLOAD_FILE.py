decoded_data = bytes.fromhex('{hex_data}')
with open("{pico_file_path}", "wb") as f: 
    f.write(decoded_data)