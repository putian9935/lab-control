from lab_control.core.target import Target
from lab_control.core.types import *
from lab_control.core.util.ts import pulsify, to_plot
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
from ...device.time_sequencer import hold 
from functools import wraps 

from .valon5019 import Synth 

class ValonSynthesizer(Target):
    def __init__(self, channel, freq) -> None:
        super().__init__()
        self.synth = Synth()
        self.channel = channel 
        self.freq = freq 
        self.loaded = True


@ValonSynthesizer.set_default
@ValonSynthesizer.take_note
class switch(hold):
    def __init__(self, *, target: ValonSynthesizer, **kwargs) -> None:
        super().__init__(channel=target.channel, **kwargs)

    async def run_preprocess(self, target: Target):
        target.synth : Synth 
        target.synth.set_freq(target.freq) 

    async def run_postprocess(self, target: Target):
        return 

    def to_plot(self, target: Target = None, *args, **kwargs):
        return {(self.channel, self.signame, 'switch'): to_plot(self.polarity, self.retv)}
