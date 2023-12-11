from .ports import setup_arduino_port, arduino_transaction
import time
import struct


def readback():
    while not ser.in_waiting:
        time.sleep(.05)
    while ser.in_waiting:
        print(ser.readline())

def readback_val():
    mess_buffer = []
    while not ser.in_waiting:
        time.sleep(.05)
    while ser.in_waiting:
        mess_buffer += [ser.readline()]
    return mess_buffer

@arduino_transaction(ser)
def sweep(ch, lower, upper, step):
    ser.write(struct.pack("<BBhhH", 1, ch, lower, upper, step))
    readback()

@arduino_transaction(ser)
def sweep_r(ch, lower, upper, step):
    ser.write(struct.pack("<BBhhH", 1, ch, lower, upper, step))
    return readback_val()

# @arduino_transaction(ser)
# def servo(ch, fi, g, wfm):
#     ser.write(struct.pack("<BBddd", 2, ch, fi, 0, g))
#     ser.write(wfm)
#     readback()

@arduino_transaction(ser)
def ref(ch, wfm):
    ser.write(struct.pack("<BB", 6, ch))
    ser.write(wfm)
    readback()

@arduino_transaction(ser)
def channel(ch, on):
    ser.write(struct.pack("<BB", 3, ch + (1 << 7) * on))
    readback()

@arduino_transaction(ser)
def hsp(ch, wfm):
    ser.write(struct.pack("<BB", 4, ch))
    ser.write(wfm)
    readback()

@arduino_transaction(ser)
def show(ch):
    ser.write(struct.pack("<BB", 5, ch)) 
    readback()

@arduino_transaction(ser)
def stop():
    ser.write(b'\x00')

if __name__ == '__main__':
    print(sweep(2, 0, 1500, 1))
