from core.target import Target
from core.action import Action
import asyncio
import importlib.util
from util.ts import save_sequences, merge_seq


def list_actions():
    for cls in Target.__subclasses__():
        print(cls.__name__, ':', *cls.supported_actions)

def list_targets():
    for cls in Target.__subclasses__():
        print(cls.__name__, ':', *cls.instances)

async def wait_until_ready():
    await asyncio.gather(*[
        tar.wait_until_ready()
        for cls in Target.__subclasses__()
        for tar in cls.instances])

async def run_preprocess():
    await asyncio.gather(*[
        tar.run_preprocess()
        for cls in Target.__subclasses__()
        for tar in cls.instances])


def run_postprocess():
    print('[INFO] cleanup')
    for cls in Action.__subclasses__():
        cls.restart()
    for cls in Target.__subclasses__():
        for inst in cls.instances:
            inst.run_postprocess()


def check_channel_clash(*to_seq):
    s = set()
    for seq in to_seq:
        for k in seq.keys():
            if k not in s:
                s.add(k)
            else:
                raise ValueError(
                    "Incompatible channel assignment! Same time sequencer channel is assigned to different targets!")


def prepare_sequencer_files():
    to_seq = tuple(tar.to_time_sequencer()
                   for cls in Target.__subclasses__()
                   for tar in cls.instances)
    check_channel_clash(*to_seq)
    exp_time = save_sequences(merge_seq(*to_seq), '1')
    print('[INFO] Time sequencer CSV and OUT file saved.')
    return exp_time


async def run_sequence(fpga, exp_time: int):
    fpga.backend.main('out')
    await asyncio.sleep(exp_time * 1e-6 + .5)


async def run_exp(module_fname, attr, **exp_param):
    spec = importlib.util.find_spec('experiments.'+module_fname)
    exp = importlib.util.module_from_spec(spec)
    for k, v in attr.items():
        exp.__setattr__(k, v)
    spec.loader.exec_module(exp)
    await exp.main(**exp_param)
