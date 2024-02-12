""" async backend """
import struct

async def readback():
    print(await ser.readline_async())

async def ref(ch, wfm):
    await ser.write_async(struct.pack("<BB", 6, ch)  + wfm)
    await readback()


async def hsp(ch, wfm):
    await ser.write_async(struct.pack("<BB", 4, ch) + wfm)
    await readback()

async def stop():
    await ser.write_async(b'\x00')
