import matplotlib.pyplot as plt
import matplotlib.axes
from ..types import *
from ..stage import Stage
from ..run_experiment import all_target_instances
from .ts import merge_plot_maps
from ..config import config
import logging 

class Viewer:
    def __init__(self, pm: plot_map, real_time) -> None:
        times = set(xx for x, y in pm.values() for xx in x)
        # if not real_time:
        for st in Stage.stages:
            times.add(st.start)
            times.add(st.end)
        self.all_x = sorted(times)
        self.inv_f = {x: i for i, x in enumerate(self.all_x)}
        self.pm = pm
        self.append_max()  # make graph look better
        self.real_time = real_time

        if self.real_time:
            self.xtick = self.all_x
        else:
            self.xtick = list(range(len(self.all_x)))
        self.xlabel = list(map(str, self.all_x))

    def plot(self, title):
        fig, axes = plt.subplots(
            len(self.pm.keys()), 1, sharex=True, figsize=(20, 13), squeeze=False)
        axes = axes[:, 0]
        self.normalize_x()
        keys = list(self.pm.keys())
        order = sorted(range(len(self.pm)), key=lambda _: keys[_])
        for ax, k in zip(axes, order):
            ax: matplotlib.axes.Axes
            channel, name, act_name = keys[k]
            x, y = self.pm[keys[k]]
            ax.plot(x, y, lw=2)
            ax.get_yaxis().set_label_coords(-.1, .5)
            ax.set_ylabel(f'{name}\n{act_name}@{channel}',
                          rotation=0, ha='left',
                          rotation_mode='anchor',
                          labelpad=100,
                          )
            ax.margins(0, .1)
            if not self.real_time:
                for x in self.xtick:
                    ax.axvline(x, color='k', ls='dashed', lw=0.5, alpha=.3)
        self.annotate_stage(axes)
        ax.set_xticks(self.xtick)
        ax.set_xticklabels(self.xlabel, rotation=90,
                           ha='right', rotation_mode='anchor')
        self.remove_middle_spines(axes)
        fig.suptitle(title)
        plt.tight_layout()
        plt.subplots_adjust(hspace=.0)
        plt.savefig('1.pdf', bbox_inches='tight')
        return self

    def remove_middle_spines(self, axes: List[matplotlib.axes.Axes]):
        if len(axes) == 1:
            return
        axes[0].spines['bottom'].set_visible(False)
        for ax in axes[1:-1]:
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
        axes[-1].spines['top'].set_visible(False)

    def show(self):
        plt.show()

    def append_max(self):
        for x, y in self.pm.values():
            x.append(self.all_x[-1])
            y.append(y[-1])

    def normalize_x(self) -> Tuple[Dict, List[int], List[int]]:
        ret = dict()
        for k, (x, y) in self.pm.items():
            ret[k] = [self.xtick[self.inv_f[_]] for _ in x[:]], y
        self.pm = ret

    def annotate_stage(self, axes):
        for c, st in enumerate(Stage.stages):
            self.xlabel[self.inv_f[st.start]] += '\n' + \
                '%s.start' % (st.__name__)
            self.xlabel[self.inv_f[st.end]] += '\n'+'%s.end' % (st.__name__)
            for ax in axes:
                ax: matplotlib.axes.Axes
                lim = ax.get_ylim()
                ax.fill_between([self.xtick[self.inv_f[st.start]], self.xtick[self.inv_f[st.end]]],
                                *lim, color=f'C{c%9+1}', alpha=.15)
                ax.set_ylim(*lim)


def show_sequences():
    pm = merge_plot_maps(*[tar.to_plot(raw=config.view_raw)
                           for tar in all_target_instances()])
    if not len(pm):
        logging.warning('Empty sequence has nothing to plot')
        return

    viewer = Viewer(pm, config.view_real_time).plot(config.title)
    viewer.show()
