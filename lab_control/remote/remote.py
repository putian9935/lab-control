import rpyc
import rpyc.utils.classic as classic
import lab_control
from functools import cache
import asyncio

class ToRemote:
    uploaded = False

    def __init__(self, daemon: lab_control.device.RPyCSlaveDaemon):
        self.conn = rpyc.classic.connect(daemon.addr)
        self.exc_check = None

        print(f'[INFO] Connected to RPyC slave at {daemon.addr}')
        if not ToRemote.uploaded:
            classic.upload_package(self.conn, lab_control)
            ToRemote.uploaded = True
        print('[INFO] Waiting slave to spawn all tasks..')
        self.rs = rpyc.classic.redirected_stdio(self.conn)
        self.rs.__enter__()

    @cache
    def __call__(self, cls):
        remote_server = self.conn.modules.lab_control.server

        async def check_for_exc():
            while True:
                if not remote_server.exc_queue.empty():
                    e = remote_server.exc_queue.get()
                    print(e)
                await asyncio.sleep(.001)
        if self.exc_check is None:
            self.exc_check = asyncio.create_task(check_for_exc())

        ainit = rpyc.async_(remote_server.init)

        def init(this, *args, **kwds):
            remote_device = self.conn.modules.lab_control.device
            if cls.__name__ not in remote_device.__dict__:
                raise TypeError(
                    f"Cannot find device {cls.__name__} in module {lab_control.device}! Did you forget to include them?\nIf so,\n1. shutdown the rpyc slave on the remote\n2. edit the local files\n3. restart the slave on the remote")

            this.result = ainit(
                remote_device.__dict__[cls.__name__], *args, **kwds)
            type(this).instances.append(this)
            this.actions = {}
            this.loaded = True

        async def wait_until_ready(this):
            while not this.result.ready:
                await asyncio.sleep(0.01)
            this.loop, this.proxy, this.thread = this.result.value

        def test_precondition(this):
            return this.proxy.test_precondition()

        def test_postcondition(this):
            return this.proxy.test_postcondition()

        async def close(this):
            await asyncio.get_running_loop().run_in_executor(None, remote_server.close, this.loop, this.proxy, this.thread)
            await asyncio.sleep(.2)  # wait for remote shutdown

        d = dict(cls.__dict__)
        d["__init__"] = init
        d["wait_until_ready"] = wait_until_ready
        d["test_precondition"] = test_precondition
        d["test_postcondition"] = test_postcondition
        d["close"] = close

        return type(cls.__name__+'_r', (cls,), d)


# to_sr_remote = ToRemote(lab_control.RPyCSlaveDaemon("192.168.107.200"))
to_in_desktop2 = ToRemote(lab_control.RPyCSlaveDaemon("192.168.107.192"))
