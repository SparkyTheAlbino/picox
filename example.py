from piconnect.upy.rp2040 import RP2040, MicroPython_Version

#TODO Add file compare for updating
# Add tooling
# make into an installable package

pico = RP2040("/dev/tty.usbmodem11101", MicroPython_Version.v1_21_0)
pico.stop_exec()
pico.send_enter()
pico.soft_reboot

if not pico.coms_test():
    print("Coms test failed. Try re-inserting the Pi Pico USB")
else:
    print("Coms test pass!")

# for i in range(1, 11):
#     result = pico.run_python_command(f"x = {i} + {i}; print(x)")
#     print(f"Python command result {i} :: {result}")

# files = pico.get_file_list()
# print(f"Got file listing from pico :: {files}")
# for file in files:
#     print(f"Downloading file {file}...")
#     with open(f"./downloads/{file}", "w") as download_file:
#         pico.download_file(file, download_file)

# print(f"Adding new file")
# with open("testpi.py", "rb") as upload_file:
#     pico.upload_file(upload_file, "testpi.py", overwrite=True)

print("Executing file")
pico.execute_file("max7219.py")
