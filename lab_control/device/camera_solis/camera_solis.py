from ...core.target import Target
import asyncio
import rpyc


class CameraSolis(Target):
    def __init__(self, fname_gen=None) -> None:
        super().__init__()
        hostname = 'CASPERN-6AKOV6A'
        self.conn = rpyc.connect(hostname, 17733)
        self.fname_gen = fname_gen 

    async def run_preprocess(self):
        return await asyncio.get_event_loop().run_in_executor(None, self.conn.root.emccd_fnAcq, 'haha')
