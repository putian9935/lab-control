import matplotlib.pyplot as plt
import matplotlib.axes
from ..types import *
from ..stage import Stage


class Viewer:
    def __init__(self, pm: plot_map, real_time=False) -> None:
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

    def plot(self):
        _, axes = plt.subplots(
            len(self.pm.keys()), 1, sharex=True, figsize=(15, 10), squeeze=False)
        axes = axes[:, 0]
        self.normalize_x()
        for ax, ((channel, name, act_name), (x, y)) in zip(axes, self.pm.items()):
            ax: matplotlib.axes.Axes
            ax.plot(x, y, lw=2)
            ax.set_ylabel(f'{name}\n{act_name}@{channel}')
            if not self.real_time:
                for x in self.xtick:
                    ax.axvline(x, color='k', ls='dashed', lw=1, alpha=.5)
        self.annotate_stage(axes)
        ax.set_xticks(self.xtick)
        ax.set_xticklabels(self.xlabel)
        plt.tight_layout()
        plt.subplots_adjust(hspace=.0)
        return self

    def show(self):
        plt.savefig('1.pdf')
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
                                    *lim, color=f'C{c%9+1}', alpha=.2)
                ax.set_ylim(*lim)


def show_sequences(pm):
    # TODO: add attribute for command line input
    Viewer(pm).plot().show()

