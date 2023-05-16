import rpyc
import rpyc.utils.classic as classic
import lab_control.device
import socket 

class ToRemote:
    uploaded = False

    def __init__(self, remote_hostname=None):
        if remote_hostname is None:
            remote_hostname = "localhost"
        try:
            self.conn = rpyc.classic.connect(remote_hostname)
        except socket.timeout:
            print(f"[ERROR] Cannot connect to {remote_hostname}")
            raise 
            
        if not ToRemote.uploaded:
            classic.upload_package(self.conn, lab_control.device)
            ToRemote.uploaded = True

    def __call__(self, cls):
        def new(remote_target, *args):
            if cls.__name__ not in self.conn.modules['lab_control.device'].__dict__:
                raise TypeError(
                    f"Cannot find device {cls.__name__} in module {lab_control.device}! Did you forget to include them?")
            remote_target = self.conn.modules['lab_control.device'].__dict__[
                cls.__name__](*args)
            return remote_target

        d = dict(cls.__dict__)
        d["__new__"] = new
        return type(cls.__name__+'_r', (cls,), d)

to_local = ToRemote()
# to_sr_remote = ToRemote("192.168.107.200")
