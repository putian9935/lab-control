from .target import Target, TargetMeta
from .action import Action, ActionMeta
import asyncio
import importlib.util
from .util.ts import save_sequences, merge_seq
import typing


def all_target_types() -> typing.Generator[TargetMeta, None, None]:
    """ Generator for all types that are subclassed from Target """
    for cls in TargetMeta.instances:
        yield cls


def all_target_instances() -> typing.Generator[Target, None, None]:
    """ Generator for all instances of type subclassed from Target """
    for cls in all_target_types():
        for tar in cls.instances:
            yield tar


def list_actions():
    for cls in all_target_types():
        print(cls.__name__, ':', ', '.join(map(str, cls.supported_actions)))


def get_action_usage(act: ActionMeta):
    print('>- Action name:', act.__name__)
    print('>- Parent target type:', ActionMeta.targets[act.__name__])
    code = act.__init__.__code__
    print('>- Arguments:')
    if code.co_argcount > 1:
        print('>--- Normal argument(s):', end=' ')
        print(', '.join(code.co_varnames[1:code.co_argcount]))
    if code.co_posonlyargcount > 0:
        print('>--- Positional only argument(s):', end=' ')
        print(
            ', '.join(code.co_varnames[code.co_argcount:][:code.co_posonlyargcount]))
    if code.co_kwonlyargcount > 0:
        print('>--- Keyword only argument(s):', end=' ')
        print(', '.join(
            code.co_varnames[code.co_argcount+code.co_posonlyargcount:][:code.co_kwonlyargcount]))

def to_action(s: str) -> ActionMeta:
    if s in ActionMeta.instances:
        return ActionMeta.instances[s] 

def list_targets():
    for cls in all_target_types():
        print(cls.__name__, ':', ', '.join(map(str, cls.instances)))


async def wait_until_ready():
    await asyncio.gather(*[
        tar.wait_until_ready()
        for tar in all_target_instances()])


def test_precondition():
    return all(tar.test_precondition()
               for tar in all_target_instances())


async def run_preprocess():
    await asyncio.gather(*[
        tar.run_preprocess()
        for tar in all_target_instances()])


def test_postcondition():
    return all(tar.test_postcondition()
               for tar in all_target_instances())


async def run_postprocess():
    await asyncio.gather(*[
        tar.run_postprocess()
        for tar in all_target_instances()])


def cleanup():
    print('[INFO] cleanup')
    for cls in Action.__subclasses__():
        cls.cleanup()
    for tar in all_target_instances():
        tar.cleanup()


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
                   for tar in all_target_instances())
    check_channel_clash(*to_seq)
    exp_time = save_sequences(merge_seq(*to_seq), '1')
    print('[INFO] Time sequencer CSV and OUT file saved.')
    return exp_time


async def run_sequence(fpga, exp_time: int):
    fpga.backend.main('out')
    await asyncio.sleep(exp_time * 1e-6 + .5)


async def run_exp(module_fname, attr, **exp_param):
    spec = importlib.util.find_spec("lab_control.experiments."+module_fname)
    if spec is None:
        raise FileNotFoundError(
            f"Cannot find experiment {module_fname}. Did you forgot to put it under experiments folder?")
    exp = importlib.util.module_from_spec(spec)
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
