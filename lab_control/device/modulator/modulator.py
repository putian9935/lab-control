from lab_control.core.types import plot_map
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
from ...core.types import *
from ..time_sequencer import pulse 
import logging 
aio_ts_mapping = Dict[ActionMeta, int]
import asyncio
import pyvisa 
from async_lru import alru_cache 

rm = pyvisa.ResourceManager()

class Modulator(Target):
    def __init__(self, *, device_addr, ts_channel, output_channel, **kwargs) -> None:
        super().__init__()
        self.device_addr = device_addr 
        self.ts_channel = ts_channel 
        self.output_channel = output_channel
        self.inst : pyvisa.USBInstrument 

        try: 
            self.inst = rm.open_resource(self.device_addr)
        except: 
            raise 
        else: 
            self.inst.close()

        # TODO: cache disabled
        self.update_amplitude = (self.update_amplitude)
        self.update_frequency = (self.update_frequency)
        self.update_duty_cycle =(self.update_duty_cycle)

    async def update_amplitude(self, low, high):
        """
        Parameters
        ---
        - low, high: in V  
        """
        raise NotImplementedError
    async def update_frequency(self, freq):
        """
        Parameters
        ---
        - freq: in kHz 
        """
        raise NotImplementedError
    async def update_phase(self, phase):
        """
        Parameters
        ---
        - phase: in degree 
        """
        raise NotImplementedError
    async def update_duty_cycle(self, duty_cycle):
        """
        Parameters
        ---
        - duty_cycle: in percentage 
        """
        raise NotImplementedError
    async def update_burst_ncycle(self, ncycle):
        raise NotImplementedError 
    async def close(self):
        self.inst.close()
        
    async def at_acq_start(self):
        self.inst = rm.open_resource(self.device_addr)
        return await super().at_acq_start()
    
    async def at_acq_end(self):
        self.inst.close()
        return await super().at_acq_end()

    async def update_test(self):
        await self.at_acq_start() 
        await self.update_amplitude(1.2, 3.4)
        await self.update_frequency(12.3456)
        await self.update_phase(12.3)
        await self.update_duty_cycle(12.3)
        await self.at_acq_end()
    



class Modulator_AFG1022(Modulator):
    async def update_amplitude(self, low, high):
        self.inst.write(f'SOURCE{self.output_channel}:VOLT {high-low:.4f}Vpp')
        self.inst.write(f'SOURCE{self.output_channel}:VOLT:OFFS {(high+low)/2.:.4f}V')

    async def update_duty_cycle(self, duty_cycle):
        self.inst.write(f'SOURCE{self.output_channel}:PULS:DCYC {duty_cycle:.1f}')
    
    async def update_frequency(self, freq):
        if freq > 20000:
            raise ValueError("Modulation frequency must be less than 1MHz!")
        self.inst.write(f'SOURCE{self.output_channel}:FREQ {freq:.4f}kHz')

    async def update_phase(self, phase):     
        self.inst.write(f'SOURCE{self.output_channel}:PHAS {phase:.3f}DEG')
    async def update_burst_ncycle(self, ncycle):   
        self.inst.write(f'SOURCE{self.output_channel}:BURS:NCYC {ncycle}')
        
class Modulator_33500B(Modulator_AFG1022):
    """ Keysight 33500B 
    Note
    ---
    Exact interface for our purpose.  
    """
    async def update_duty_cycle(self, duty_cycle):
        self.inst.write(f'SOURCE{self.output_channel}:FUNC:SQU:DCYC {duty_cycle:.1f}')

class Modulator_RSDG5082(Modulator_AFG1022):
    """ RS-PRO RSDG5082 
    """    
    async def update_amplitude(self, low, high):
        self.inst.write(f'C{self.output_channel}:BSWV AMP, {high-low:.4f}')
        self.inst.write(f'C{self.output_channel}:BSWV OFST, {(high+low)/2.:.4f}')

    async def update_duty_cycle(self, duty_cycle):
        print(self.inst.write(f'C{self.output_channel}:BSWV DUTY, {duty_cycle:.1f}'))
    
    async def update_frequency(self, freq):
        if freq > 1000:
            raise ValueError("Modulation frequency must be less than 1MHz!")
        self.inst.write(f'C{self.output_channel}:BSWV FRQ,  {freq*1e3:.1f}')

    async def update_phase(self, phase):     
        self.inst.write(f'C{self.output_channel}:BSWV PHSE, {phase:.3f}')
    

class Modulator_RSDG5082_Pulse(Modulator_AFG1022):
    """ RS-PRO RSDG5082 pulse mode 
    """    
    async def update_amplitude(self, low, high):
        self.inst.write(f'C{self.output_channel}:BSWV AMP, {high-low:.4f}')
        self.inst.write(f'C{self.output_channel}:BSWV OFST, {(high+low)/2.:.4f}')

    async def update_width(self, width):
        self.inst.write(f'C{self.output_channel}:BSWV WIDTH, {width:.9f}')
    
    async def update_frequency(self, freq):
        self.inst.write(f'C{self.output_channel}:BSWV FRQ,  {freq*1e3:.1f}')

    async def update_delay(self, delay):     
        self.inst.write(f'C{self.output_channel}:BSWV DLY, {delay:.9f}')
    
    async def update_edge_time(self, edge_time):     
        self.inst.write(f'C{self.output_channel}:BSWV RISE, {edge_time:.9f}')
        self.inst.write(f'C{self.output_channel}:BSWV FALL, {edge_time:.9f}')

@Modulator_AFG1022.set_default
@Modulator_AFG1022.take_note
@Modulator.set_default
@Modulator.take_note
class modulate(pulse):
    '''
    Modulate the output 
    '''    
    def __init__(self, *, target: Modulator, **kwargs) -> None:
        super().__init__(channel=target.ts_channel, **kwargs)


    async def run_preprocess(self, target: Modulator):
        return 
    