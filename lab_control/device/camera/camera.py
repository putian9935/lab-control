from ...core.target import Target
from ...core.action import Action, set_pulse
import asyncio
from . import gui
from . import config_editor as ce
import msvcrt
import time
from typing import Tuple, Dict, List
from ...core.util.ts import to_plot, pulsify


class Camera(Target):
    def __init__(self, channel) -> None:
        self.channel = channel
        super().__init__()
        type(self).backgrounds.append(gui.main())

    @Target.disable_if_offline
    async def wait_until_ready(self):
        await gui.wait_until_cam_initialized()
        self.loaded = True

    @Target.disable_if_offline
    @Target.ensure_loaded
    def test_precondition(self):
        is_stabilized = gui.is_temperature_stabilized()
        if not is_stabilized:
            print('[WARNING] Camera temperature is not stablized! Do you want to proceed? Press q to abort and any other key to proceed.')
            while not msvcrt.kbhit():
                time.sleep(0.1)
            if msvcrt.getch() == b'q':
                print('[INFO] Abort experiment due to non-stabilized temperature.')
                return False
        return True

    @Target.disable_if_offline
    @Target.ensure_loaded
    async def close(self):
        await gui.shutdown_cam()


@set_pulse
@Camera.set_default
@Camera.take_note
class external(Action):
    def __init__(self, *, spooling=False, spool_func=None, exposure_time=None, emccd_gain=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.spooling = spooling
        self.spool_func = spool_func
        self.yml = ce.open_config()
        if exposure_time is not None:
            if exposure_time > 1:
                raise ValueError(
                    "Camera exposure time > 1 second! Did you forget to change unit from microsecond to second?")
            ce.set_config(self.yml, 'External start',
                          'ExposureTime', exposure_time/1e3)
        if emccd_gain is not None:
            ce.set_config(self.yml, 'External start', 'EMCCDGain', emccd_gain)

    async def run_preprocess(self, target):
        ce.save_config(self.yml)
        return gui.exported_funcs[type(self).__name__](self.spooling, self.spool_func)()

    def to_time_sequencer(self, target: Camera) -> Tuple[Dict[int, List[int]], bool, str]:
        return {target.channel: (self.retv, self.polarity, self.signame)}

    def to_plot(self, target=None, **kwargs):
        return {(target.channel, self.signame, 'external'): to_plot(self.polarity, pulsify(self.retv, width=0))}


@set_pulse
@Camera.take_note
class external_start(external):
    def __init__(self, *, first_image_at, kcc=None, nc=None, **kwargs) -> None:
        super().__init__(**kwargs)
        if kcc is not None:
            ce.set_config(self.yml, 'External start',
                          'KineticCycleTime', kcc/1e3)
        if nc is not None:
            ce.set_config(self.yml, 'External start', 'NumKinetics', nc/1e3)
        self.first_image_at = first_image_at

    def to_time_sequencer(self, target: Camera) -> Tuple[Dict[int, List[int]], bool, str]:
        return {target.channel: ([self.first_image_at], self.polarity, self.signame)}

    def to_plot(self, target=None, **kwargs):
        # display all actual fires, NOTE up to 50us delay 
        return {
            (target.channel, self.signame, 'external_start'):
            to_plot(self.polarity,
                    pulsify([
                        self.first_image_at + _ * self.nc
                        for _ in range(self.kcc)],
                        width=0))}


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
