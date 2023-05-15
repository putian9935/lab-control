from core.target import Target
from core.action import Action, set_pulse
import asyncio
from . import gui
from . import config_editor as ce


class Camera(Target):
    def __init__(self, channel) -> None:
        self.channel = channel
        super().__init__()
        type(self).backgrounds.append(gui.main())

    async def wait_until_ready(self):
        await gui.wait_until_cam_ready() 

    async def close(self):
        await gui.shutdown_cam()
@set_pulse
@Camera.set_default
@Camera.take_note
class external(Action):
    def __init__(self, *, spooling=False, spool_func=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.spooling = spooling
        self.spool_func = spool_func
        ce.save_config(ce.open_config())

    async def run_preprocess(self, target):
        return gui.exported_funcs['external'](self.spooling, self.spool_func)()

    def to_time_sequencer(self, target: Camera) -> tuple[dict[int, list[int]], bool, str]:
        return {target.channel: (self.retv, self.polarity, self.signame)}


@set_pulse
@Camera.set_default
@Camera.take_note
class external_start(Action):
    def __init__(self, *, spooling=False, spool_func=None, kcc=None, nc=None, first_image_at=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.spooling = spooling
        self.spool_func = spool_func
        yml = ce.open_config()
        if kcc is not None:
            ce.set_config(yml, 'External start', 'KineticCycleTime', kcc)
        if nc is not None:
            ce.set_config(yml, 'External start', 'NumKinetics', nc)
        ce.save_config(yml)
        self.first_image_at = first_image_at

    async def run_preprocess(self, target):
        return gui.exported_funcs['external start'](self.spooling, self.spool_func)()

    def to_time_sequencer(self, target: Camera) -> tuple[dict[int, list[int]], bool, str]:
        return {target.channel: ([self.first_image_at], self.polarity, self.signame)}


if __name__ == '__main__':
    cam = Camera(channel=3)

    @cam(external)
    def trig():
        return [1, 20000]

    async def main():
        tasks = []
        for bg in Camera.backgrounds:
            tasks.append(asyncio.create_task(bg))
        await asyncio.sleep(5)
        await cam.run_preprocess()
        print(cam.to_time_sequencer())
        await asyncio.sleep(5)

    asyncio.run(main())
