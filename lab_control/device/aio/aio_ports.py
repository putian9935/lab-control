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
def setup_arduino_port(port, baud=115200, timeout=.1):
    """ Returns an unopened port. """
    ser = aioserial.AioSerial(port, baudrate=baud, timeout=timeout)
    ser.close()
    # use this line for the suppression of Arduino auto-restart 
    # ser.dtr = False 
    return ser

