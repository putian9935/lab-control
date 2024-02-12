from functools import lru_cache, partial  
from aioserial import AioSerial 
from async_lru import alru_cache

class Synth:
    def __init__(self, com_port):
        self.ser = AioSerial(timeout=.5)
        self.ser.port = com_port
        # if self.device_name not in rmlist:
        #     raise ValueError(
        #         f'Could not find valon synthesizer {device_name};\nAvailable devices are {rmlist}.'
        #     )
        # stops uploading if the frequency does not change 
        self.write_async = self.ser.write_async 
        self.read_all = partial(self.ser.read_until_async, expected='>')
        self.set_freq = alru_cache(maxsize=1)((self.set_freq))
        self.set_power = alru_cache(maxsize=1)((self.set_power))
        self.get_freq = (self.get_freq)
        self.get_power = (self.get_power)
        self.set_mode = alru_cache(maxsize=1)(self.set_mode)
        
    def transaction(self, f):
        async def wrapper(*args, **kwds):
            self.ser.open()
            ret = await f(*args, **kwds)
            self.ser.close()
            return ret 
        return wrapper 
    
    
    async def set_mode(self, mod_str):
        """ 
        - mod_str: "cw" | "list" 
        """
        await self.write_async(f'MOD {mod_str}\r'.encode())
    
    async def set_freq(self, freq):
        # set frequency in MHz
        await self.write_async(f'cw {freq} mhz\r'.encode())
    

    async def set_freq2(self, freq1, freq2):
        """ Set two frequencies, controlled by TTL 
        
        Freq 1: when TTL is low 
        Freq 2: when TTL is high  
        """
        print(freq1, freq2)
        await self.write_async(f'list 31 {freq1} mhz')
        await self.write_async(f'list 32 {freq2} mhz')

    async def get_freq(self):
        # for some reason, we can read one line at a time
        await self.ser.write_async(b'FREQ\r')
        print(await self.read_all())

    async def set_power(self, new_power):
        """ Set power level; currently the level is +1dBm """ 
        if new_power > 8 or new_power < -30:
            raise ValueError("New power must be within +1dBm and -30dBm")
        # set power in dBm 
        await self.write_async(f'PWR {new_power}\r'.encode())

    async def get_power(self):
        # for some reason, we can read one line at a time
        await self.write_async(b'PWR\r')
        print(await self.read_all())
    
        
if __name__ == '__main__':
    import asyncio
    synth = Synth('COM16')