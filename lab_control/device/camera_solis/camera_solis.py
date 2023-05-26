from ...core.target import Target
import asyncio
import rpyc
from ...core.types import *
from ...core.config import config


class CameraSolis(Target):
    def __init__(self) -> None:
        super().__init__()
        self.load()

    @Target.disable_if_offline
    @Target.ensure_loaded
    async def run_preprocess(self):
        config.append_param(config.param_str)
        config.append_fname(config.fname)
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self.conn.root.emccd_fnAcq,
            config.fname)

    @Target.disable_if_offline
    @Target.ensure_loaded
    def cleanup(self):
        self.conn.root.emccd_stopAcq()
    
    @Target.disable_if_offline
    @Target.load_wrapper
    def load(self, *args, **kwds):
        hostname = 'CASPERN-6AKOV6A'
        self.conn = rpyc.connect(hostname, 17733)
