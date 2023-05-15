from core.target import Target
from core.action import Action
import asyncio
import importlib.util
from util.ts import save_sequences, merge_seq
import typing


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


def test_precondition():
    return all(tar.test_precondition()
               for cls in Target.__subclasses__()
               for tar in cls.instances)


async def run_preprocess():
    await asyncio.gather(*[
        tar.run_preprocess()
        for cls in Target.__subclasses__()
        for tar in cls.instances])


def test_postcondition():
    return all(tar.test_postcondition()
               for cls in Target.__subclasses__()
               for tar in cls.instances)


async def run_postprocess():
    await asyncio.gather(*[
        tar.run_postprocess()
        for cls in Target.__subclasses__()
        for tar in cls.instances])


def cleanup():
    print('[INFO] cleanup')
    for cls in Action.__subclasses__():
        cls.cleanup()
    for cls in Target.__subclasses__():
        for inst in cls.instances:
            inst.cleanup()


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
    if exp is None: 
        raise FileNotFoundError(f"Cannot find experiment {module_fname}. Did you forgot to put it under experiments folder?")
    
    for k, v in attr.items():
        exp.__setattr__(k, v)
    spec.loader.exec_module(exp)

    if 'main' not in exp.__dict__:
        raise AttributeError(
            f"Cannot find function main() from experiment {module_fname}. Did you forgot to define one?")
    main = exp.main(**exp_param)

    if not isinstance(main, typing.Coroutine):
        raise TypeError(
            f"Cannot execute main() from experiment {module_fname}. Did you forgot to wrap it with Experiment?")
    await main
