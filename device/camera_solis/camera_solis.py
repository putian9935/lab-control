from core.target import Target
from core.action import Action, set_pulse
import asyncio 
class CameraSolis(Target):
    def __init__(self, channel) -> None:
        self.channel = channel 
        super().__init__() 

@set_pulse
@CameraSolis.set_default
@CameraSolis.take_note
class external_purge(Action):
    async def run_preprocess(self, target):
        return await asyncio.get_event_loop().run_in_executor(None, input, "Terminate the current (if any) acquisition from Andor Solis, and start a new acquisition with 'external with purge'.\nPress enter when you are done.") 
    
    def to_time_sequencer(self, target: CameraSolis) -> tuple[dict[int, list[int]], bool]:
        return {target.channel: (self.retv, self.polarity, self.signame)}


if __name__ == '__main__':
    cam = CameraSolis(channel=3)

    @cam(external_purge)
    def trig():
        return [1, 20000]

    asyncio.run(cam.run_preprocess())
    print(cam.to_time_sequencer())
