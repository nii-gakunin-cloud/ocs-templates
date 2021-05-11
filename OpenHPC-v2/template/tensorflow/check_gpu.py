from tensorflow.python.client import device_lib


devices = device_lib.list_local_devices()
print(devices)
if len([x for x in devices if x.device_type=='GPU']) == 0:
    raise RuntimeError("GPU device not found.")
