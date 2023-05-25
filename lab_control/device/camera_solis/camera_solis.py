from ...core.target import Target
import asyncio
import rpyc
from ...core.types import *
from ...core.config import config


class CameraSolis(Target):
    def __init__(self) -> None:
        super().__init__()
        hostname = 'CASPERN-6AKOV6A'
        self.conn = rpyc.connect(hostname, 17733)

    async def run_preprocess(self):
        fname = config.fname
        config.append_param(config.param_str)
        config.append_fname(fname)
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self.conn.root.emccd_fnAcq,
            fname)

    def cleanup(self):
        self.conn.root.emccd_stopAcq()
