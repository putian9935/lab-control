import rpyc
import rpyc.utils.classic as classic
import lab_control
import socket 
from functools import cache 
class ToRemote:
    uploaded = False

    def __init__(self, remote_hostname=None):
        if remote_hostname is None:
            remote_hostname = "localhost"
        try:
            self.conn = rpyc.classic.connect(remote_hostname)
        except (socket.timeout, ConnectionRefusedError) as e:
            raise type(e)(f"Cannot connect to {remote_hostname}. Did you forget to start rpyc slave?") from e
            
        if not ToRemote.uploaded:
            classic.upload_package(self.conn, lab_control)
            ToRemote.uploaded = True

    @cache
    def __call__(self, cls):
        def init(this, *args, **kwds):
            remote_device = self.conn.modules.lab_control.device
            remote_server = self.conn.modules.lab_control.server
            if cls.__name__ not in remote_device.__dict__:
                raise TypeError(
                    f"Cannot find device {cls.__name__} in module {lab_control.device}! Did you forget to include them?\nIf so,\n1. shutdown the rpyc slave on the remote\n2. edit the local files\n3. restart the slave on the remote")
            this.loop, this.proxy, this.thread = remote_server.init(remote_device.__dict__[cls.__name__], *args, **kwds)
            type(this).instances.append(this)
        async def wait_until_ready(this):
            pass
        def test_precondition(this):
            return this.proxy.test_precondition()
        async def close(this):
            remote_server = self.conn.modules.lab_control.server
            remote_server.close(this.loop, this.proxy, this.thread)
        d = dict(cls.__dict__)
        d["__init__"] = init
        d["wait_until_ready"] = wait_until_ready
        d["test_precondition"] = test_precondition
        d["close"] = close
        return type(cls.__name__+'_r', (cls,), d)

# to_local = ToRemote()
to_sr_remote = ToRemote("192.168.107.200")
