import rpyc
import rpyc.utils.classic as classic
import lab_control
from functools import cache
import asyncio


class ToRemote:
    uploaded = False
    exc_check = None 

    def __init__(self, daemon: lab_control.device.RPyCSlaveDaemon):
        self.conn = rpyc.classic.connect(daemon.addr)
        print(f'[INFO] Connected to RPyC slave at {daemon.addr}')
        if not ToRemote.uploaded:
            classic.upload_package(self.conn, lab_control)
            ToRemote.uploaded = True
        print('[INFO] Waiting slave to spawn all tasks..')

    @cache
    def __call__(self, cls):
        def init(this, *args, **kwds):
            async def check_for_exc():
                while True:
                    if not remote_server.exc_queue.empty():
                        e = remote_server.exc_queue.get()
                        print(e) 
                    await asyncio.sleep(.1)
            if ToRemote.exc_check is None:
                ToRemote.exc_check = asyncio.create_task(check_for_exc())
            remote_device = self.conn.modules.lab_control.device
            remote_server = self.conn.modules.lab_control.server
            if cls.__name__ not in remote_device.__dict__:
                raise TypeError(
                    f"Cannot find device {cls.__name__} in module {lab_control.device}! Did you forget to include them?\nIf so,\n1. shutdown the rpyc slave on the remote\n2. edit the local files\n3. restart the slave on the remote")

            this.loop, this.proxy, this.thread = remote_server.init(
                remote_device.__dict__[cls.__name__], *args, **kwds)
            type(this).instances.append(this)
            async def keep_running():
                # seems like RPyC forgets the event loop if we are not working with it
                # therefore poll remote something cheap
                while True:
                    this.loop.is_running()
                    await asyncio.sleep(0)
            this.keep_alive = asyncio.create_task(keep_running())
   
        async def wait_until_ready(this):
            pass

        def test_precondition(this):
            ret = this.proxy.test_precondition()
            if not ret:
                print(f'[ERROR] Precondition failed for {cls.__name__}')
            return ret 

        def test_postcondition(this):
            ret = this.proxy.test_postcondition()
            if not ret:
                print(f'[ERROR] Postcondition failed for {cls.__name__}')
            return ret 


        async def close(this):
            remote_server = self.conn.modules.lab_control.server
            await asyncio.get_running_loop().run_in_executor(None, remote_server.close, this.loop, this.proxy, this.thread)
            await asyncio.sleep(.2) # wait for remote shutdown
            if not this.keep_alive.cancelled() and not this.keep_alive.done():
                this.keep_alive.cancel()
        d = dict(cls.__dict__)
        d["__init__"] = init
        d["wait_until_ready"] = wait_until_ready
        d["test_precondition"] = test_precondition
        d["test_postcondition"] = test_postcondition
        d["close"] = close
        return type(cls.__name__+'_r', (cls,), d)


to_sr_remote = ToRemote(lab_control.RPyCSlaveDaemon("192.168.107.200"))
