from lab_control.core.target import Target
from lab_control.core.types import *
from lab_control.core.util.ts import pulsify, square, to_plot
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
from collections import defaultdict


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
    def to_plot_cls(cls, target: Target, expand_pulse, *args, **kwargs):
        if cls is not hold:
            return ActionMeta.to_plot_cls(cls, target, expand_pulse, *args, **kwargs)
        edges = defaultdict(list)
        init_state = defaultdict()
        for act in target.actions[cls]:
            k = act.channel, act.signame, 'hold'
            edges[k] += act.retv
            init_state[k] = act.polarity
        ret = dict()
        for k, data in edges.items():
            if k not in ret:
                ret[k] = to_plot(init_state[k], sorted(data))
            else:
                new = to_plot(init_state[k], sorted(data))
                ret[k][0].extend(new[0])
                ret[k][1].extend(new[1])
        return ret

    def to_plot(self, target: Target = None, *args, **kwargs):
        return {(self.channel, self.signame, 'hold'): to_plot(self.polarity, self.retv)}


@set_pulse
@TimeSequencer.take_note
class pulse(hold):
    def to_plot(self, target=None, expand_pulse=False, *args, **kwargs):
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
