from lab_control.core.target import Target
from lab_control.core.types import *
from lab_control.core.util.ts import pulsify, to_plot
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta


class TimeSequencer(Target):
    def __init__(self) -> None:
        super().__init__()
        self.loaded = True


@TimeSequencer.set_default
@TimeSequencer.take_note
class hold(Action):
    def __init__(self, *, channel, **kwargs) -> None:
        self.channel = channel
        super().__init__(**kwargs)

    async def run_preprocess(self, target: Target):
        return  

    async def run_postprocess(self, target: Target):
        return 

    def to_time_sequencer(self, target: TimeSequencer) -> Tuple[Dict[int, List[int]], bool]:
        return {self.channel: (self.retv, self.polarity, self.signame)}

    def to_plot(self, target: Target = None, *args, **kwargs):
        return {(self.channel, self.signame, 'hold'): to_plot(self.polarity, self.retv)}

    def __eq__(self, __value: object) -> bool:
        return super().__eq__(__value) and self.channel == __value.channel 


@set_pulse
@TimeSequencer.take_note
class pulse(hold):
    def to_plot(self, target=None, expand_pulse=False, **kwargs):
        key = self.channel, self.signame, 'pulse'
        if not expand_pulse:
            return {key: to_plot(self.polarity, pulsify(self.retv, width=0))}
        else:
            return {key: to_plot(self.polarity, pulsify(self.retv))}


if __name__ == '__main__':
    raw_ts = TimeSequencer()

    @raw_ts(action=hold, channel=2,)
    def ch2():
        return [2, 4]

    @raw_ts(pulse, channel=2)
    def ch2():
        return [2000]

    print(hold.to_plot_cls(raw_ts))
