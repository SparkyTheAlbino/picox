from piconnect.upy.rp2040 import RP2040

local_file = "./downloads/test.py"
remote_file = "demo.py"
# download_file = "./downloads/aaa.py"

pico = RP2040("COM7", verbose=True)
pico.stop_exec()
pico.send_enter()

# with open(local_file, "rb") as read_file:
#     pico.upload_file(read_file, remote_file, overwrite=True)
# raise SystemExit

with open(local_file, "w") as save_file:
    pico.download_file(remote_file, save_file)