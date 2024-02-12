from lab_control.core.target import Target
from lab_control.core.types import *
from lab_control.core.util.ts import pulsify, to_plot
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
from ...device.time_sequencer import hold 
from functools import wraps 

from .valon5019 import Synth 

class ValonSynthesizer(Target):
    """ Valon Synthesizer 
    
    Parameters 
    --- 
    - port: the COM port 
    the port number is same as VISA device name, e.g., if the VISA name is ASRL16::INSTR, then the COM port 
    is COM16
    - channel: time sequencer channel; 
    - freq: initial output frequency in MHz;  
    - power: output power in dBm. 
    """
    def __init__(self, *, port, channel, freq, power=+1) -> None:
        super().__init__()
        self.synth = Synth(port)
        self.channel = channel 
        self.freq = freq
        self.power = power 
        self.loaded = True

    async def at_acq_start(self):
        self.synth.ser.open()

    async def at_acq_end(self):
        self.synth.ser.close()

@ValonSynthesizer.set_default
@ValonSynthesizer.take_note
class switch(hold):
    def __init__(self, *, target: ValonSynthesizer, **kwargs) -> None:
        super().__init__(channel=target.channel, **kwargs)

    async def run_preprocess(self, target: Target):
        target.synth : Synth 
        from numbers import Number  
        await target.synth.set_power(target.power) 
        if isinstance(target.freq, list):
            await target.synth.set_mode('list')
            await target.synth.set_freq2(target.freq[0], target.freq[1])
        elif isinstance(target.freq, Number):
            await target.synth.set_mode('cw')
            await target.synth.set_freq(target.freq)  

    async def run_postprocess(self, target: Target):
        return 

    def to_plot(self, target: Target = None, *args, **kwargs):
        return {(self.channel, self.signame, 'switch'): to_plot(self.polarity, self.retv)}

