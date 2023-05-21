from lab_control.core.target import Target
from lab_control.core.util.ts import pulsify, square, to_plot
from lab_control.core import types
from ...core.target import Target
from ...core.action import Action, set_pulse
from collections import defaultdict

from typing import Optional, Tuple, Dict, List


class TimeSequencer(Target):
    pass


@TimeSequencer.set_default
@TimeSequencer.take_note
class hold(Action):
    def __init__(self, *, channel, **kwargs) -> None:
        self.channel = channel
        super().__init__(**kwargs)

    def to_time_sequencer(self, target: TimeSequencer) -> Tuple[Dict[int, List[int]], bool]:
        return {self.channel: (self.retv, self.polarity, self.signame)}

    @classmethod
    def to_plot_cls(cls, target: Target):
        edges = defaultdict(list)
        init_state = defaultdict()
        for act in target.actions[hold]:
            edges[act.channel, act.signame] += act.retv
            init_state[act.channel, act.signame] = act.polarity
        ret = defaultdict(list)
        for (ch, name), data in edges.items():
            ret[ch, name].append(
                to_plot(init_state[ch, name], sorted(data)))
        return ret


@set_pulse
@TimeSequencer.take_note
class pulse(hold):
    def to_plot(self, target, *, expand_pulse=False):
        if not expand_pulse:
            return {(self.channel, self.signame): to_plot(self.polarity, pulsify(self.retv, width=0))}
        else:
            return {(self.channel, self.signame): to_plot(self.polarity, pulsify(self.retv))}


if __name__ == '__main__':
    raw_ts = TimeSequencer()

    @raw_ts(action=hold, channel=2,)
    def ch2():
        return [2, 4]

    @raw_ts(pulse, channel=2)
    def ch2():
        return [2000]

    print(hold.to_plot_cls(raw_ts))
