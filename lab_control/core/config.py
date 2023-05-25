from .types import *
from datetime import datetime
import os
from .types import *


class Configuration:
    def __init__(self) -> None:
        # saving options
        self._time_stamp: datetime = None
        self._arguments: Dict = None
        self._output_dirname: str = None

        # viewing options
        self.view: bool = False
        self.view_raw: bool = False
        self.view_real_time: bool = False

    @property
    def output_dirname(self):
        return self._output_dirname

    @output_dirname.setter
    def output_dirname(self, new_dirname):
        if not os.path.exists(new_dirname):
            print('Making directory', new_dirname)
            os.mkdir()
        self._output_dirname = new_dirname

        self._all_fnames = os.path.join(self._output_dirname, 'fnames.txt')
        if not os.path.exists(self._all_fnames):
            open(self._all_fnames, 'w').close()

        self._all_params = os.path.join(self._output_dirname, 'params.txt')
        if not os.path.exists(self._all_params):
            open(self._all_params, 'w').close()

    @property
    def all_fnames(self):
        return self._all_fnames

    @property
    def all_params(self):
        return self._all_params

    def append_fname(self, fname: str):
        with open(self.all_fnames, 'a') as f:
            f.write(fname+'\n')

    def append_param(self, params: str):
        with open(self.all_params, 'a') as f:
            f.write(params+'\n')

    @property
    def cnt(self):
        ret = 0
        with open(self.all_fnames) as f:
            while f.readline():
                ret += 1
        return ret

    @property
    def title(self):
        """ Convert parameter dict to title"""
        return ', '.join(f'{k}={v}' for k, v in self._arguments.items())

    @property
    def fname(self):
        """ Convert parameter dict to fname"""
        return f'{self.cnt}_'+'_'.join(f'{v}' for v in self._arguments.values()) + f'_{self._time_stamp:%Y%m%d%H%M%S}'

    @property
    def param_str(self):
        return f'{self.cnt}, ' + self.title + f', {self._time_stamp:%Y%m%d%H%M%S}'


config = Configuration()
config.output_dirname = rf'Q:\indium\data\2023\{datetime.now():%y%m%d}'
