from core.target import Target
from core.action import Action, set_pulse


class TimeSequencer(Target):
    pass


@TimeSequencer.set_default
@TimeSequencer.take_note
class hold(Action):
    def __init__(self, *, channel, **kwargs) -> None:
        self.channel = channel
        super().__init__(**kwargs)

    def to_time_sequencer(self, target: TimeSequencer) -> tuple[dict[int, list[int]], bool]:
        return {self.channel: (self.retv, self.polarity, self.signame)}


@set_pulse
@TimeSequencer.take_note
class pulse(hold):
    pass


if __name__ == '__main__':
    raw_ts = TimeSequencer()

    @raw_ts(hold, channel=2,)
    def ch2():
        return [2, 4]

    @raw_ts(pulse, channel=2)
    def ch2():
        return [2000]
    print(raw_ts.to_time_sequencer())
