from .types import *
from datetime import datetime
import os
from .types import *
import shlex
from ast import literal_eval
from collections.abc import Iterable

class ConfMeta(type):
    def __init__(cls, *args):
        cls.writable_property_names = set(
            attr
            for attr in cls.__dict__.keys()
            if isinstance(cls.__getattribute__(cls, attr), property)
            if cls.__getattribute__(cls, attr).fset is not None)


class Configuration(metaclass=ConfMeta):
    def __init__(self) -> None:
        # saving
        self._time_stamp: datetime = None
        self._arguments: Dict = None
        self._output_dirname: str = None
        self._cnt = None
        self._all_fnames: str = None
        self._all_params: str = None
        self.exp_name: str = None

        # viewing
        self.view: bool = False  # False = can save pdf, no show plt
        self.view_raw: bool = False  # False = trig plot mode
        self.view_real_time: bool = False  # seq plot not equal spacing

        # loading and running
        self.offline: bool = True
        self.strict: bool = False

    def append_fname(self, fname: str):
        with open(self.all_fnames, 'a') as f:
            f.write(fname+'\n')

    def append_param(self, params: str):
        with open(self.all_params, 'a') as f:
            f.write(params+'\n')

    def update_cnt(self):
        if self.all_fnames is None:
            return
        ret = 0
        with open(self.all_fnames) as f:
            while f.readline():
                ret += 1
        self._cnt = ret

    def update(self, cmd: str):
        for x in shlex.split(cmd, posix=False):
            try:
                k, v = x.split('=', 1)
            except ValueError as e:
                raise ValueError(
                    f"Cannot parse line {x}. Is it in the format of key=value?") from e
            if (k not in self.__dict__ and
                    k not in Configuration.writable_property_names):
                raise KeyError(
                    f"Cannot find attribute {k}. Did you misspell it?")
            try:
                self.__setattr__(k, literal_eval(v))
            except (ValueError, SyntaxError) as e:
                raise ValueError(
                    f"Cannot parse value {v}. Did you forget to add r-prefix for raw strings?") from e

    @property
    def output_dir(self):
        return self._output_dirname

    @output_dir.setter
    def output_dir(self, new_dirname):
        if not os.path.exists(new_dirname):
            print('Making directory', new_dirname)
            os.mkdir(new_dirname)
        self._output_dirname = new_dirname

        self._all_fnames = os.path.join(self._output_dirname, 'fnames.txt')
        if not os.path.exists(self._all_fnames):
            open(self._all_fnames, 'w').close()

        self._all_params = os.path.join(self._output_dirname, 'params.txt')
        if not os.path.exists(self._all_params):
            open(self._all_params, 'w').close()

    @property
    def time_stamp(self):
        return self._time_stamp

    @property
    def all_fnames(self):
        return self._all_fnames

    @property
    def all_params(self):
        return self._all_params

    @property
    def cnt(self):
        return self._cnt

    @property
    def title(self):
        """ Convert parameter dict to title"""
        return self.exp_name+', '+', '.join(f'{k}={v}' for k, v in self._arguments.items())

    @property
    def fname(self):
        """ Convert parameter dict to fname"""
        def to_str(x):
            if isinstance(x, Iterable):
                return '-'.join(str(_) for _ in x)
            return str(x)
        
        return f'{self.cnt}_'+'_'.join(to_str(v) for v in self._arguments.values()) + f'_{self._time_stamp:%Y%m%d%H%M%S}'

    @property
    def param_str(self):
        return f'{self.cnt}, ' + self.title + f', {self._time_stamp:%Y%m%d%H%M%S}'


config = Configuration()
