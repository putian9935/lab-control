from lab_control.core.target import Target
from lab_control.core.types import *
from lab_control.core.util.ts import pulsify, to_plot
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
from ...device.time_sequencer import hold 

from .valon5019 import Synth 

class ValonSynthesizer(Target):
    def __init__(self) -> None:
        super().__init__()
        self.synth = Synth()
        self.loaded = True


@ValonSynthesizer.set_default
@ValonSynthesizer.take_note
class switch(hold):
    def __init__(self, *, channel, frequency=None, **kwargs) -> None:
        self.channel = channel
        if frequency is not None:
            self.frequency = frequency 
        super().__init__(**kwargs)

    async def run_preprocess(self, target: Target):
        if self.frequency is not None:
            target.synth : Synth 
            target.synth.set_freq(self.frequency) 

    async def run_postprocess(self, target: Target):
        return 

    # def to_time_sequencer(self, target) -> Tuple[Dict[int, List[int]], bool]:
    #     return super().to_time_sequencer(target)
    #     # return {self.channel: (self.retv, self.polarity, self.signame)}

    def to_plot(self, target: Target = None, *args, **kwargs):
        return {(self.channel, self.signame, 'switch'): to_plot(self.polarity, self.retv)}

    # def __eq__(self, __value: object) -> bool:
    #     return super().__eq__(__value) and self.channel == __value.channel 

    # def weak_equal(self, __value: object) -> bool:
    #     return super().weak_equal(__value) and self.channel == __value.channel

