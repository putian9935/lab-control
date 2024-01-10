import aioserial

class CachedPort:
    ports = {}

    def __init__(self, func) -> None:
        self.func = func

    def __call__(self, *args):
        if args[0] in CachedPort.ports:
            return CachedPort.ports[args[0]]
        CachedPort.ports[args[0]] = self.func(*args)
        return CachedPort.ports[args[0]]


@CachedPort
def setup_arduino_port(port, baud=115200, timeout=.5):
    """ Returns an unopened port. """
    ser = aioserial.AioSerial(port, baudrate=baud, timeout=timeout)
    ser.close()
    # use this line for the suppression of Arduino auto-restart 
    # ser.dtr = False 
    return ser

def arduino_transaction(ser):
    def ret(f):
        async def _inner(*args, **kwargs):
            ser.open()
            r = await f(*args, **kwargs)
            ser.close() 
            return r
        return _inner
    return ret 
