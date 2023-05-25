from ...core.target import Target
import asyncio
import rpyc
from ...core.types import *
from ...core import config


def param2fname(param: Dict):
    """ Convert parameter dict to k=v string"""
    return f'{config.get_cnt()}_'+'_'.join(f'{v}' for v in param.values()) + f'_{config.time_stamp:%Y%m%d%H%M%S}'


class CameraSolis(Target):
    def __init__(self, fname_gen=None) -> None:
        super().__init__()
        hostname = 'CASPERN-6AKOV6A'
        self.conn = rpyc.connect(hostname, 17733)
        self.fname_gen = fname_gen

    async def run_preprocess(self):
        fname = param2fname(config.arguments)
        config.append_fname(fname)
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self.conn.root.emccd_fnAcq,
            fname)

    def cleanup(self):
        self.conn.root.emccd_stopAcq()
