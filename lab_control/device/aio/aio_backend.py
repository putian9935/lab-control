""" async backend """
from .aio_ports import setup_arduino_port, arduino_transaction
import struct

async def readback():
    print(await ser.readline_async())

@arduino_transaction(ser)
async def ref(ch, wfm):
    await ser.write_async(struct.pack("<BB", 6, ch)  + wfm)
    await readback()


@arduino_transaction(ser)
async def hsp(ch, wfm):
    await ser.write_async(struct.pack("<BB", 4, ch) + wfm)
    await readback()

@arduino_transaction(ser)
async def stop():
    await ser.write_async(b'\x00')
