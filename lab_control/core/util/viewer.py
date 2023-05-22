import matplotlib.pyplot as plt
import matplotlib.axes
from ..types import *
from ..stage import Stage


def append_max(pm: plot_map, max_time):
    for x, y in pm.values():
        x.append(max_time)
        y.append(y[-1])


def normalize_x(pm: plot_map, all_x: List[int]) -> Tuple[Dict, List[int], List[int]]:
    xtick = list(range(len(all_x)))
    inv_f = {x: i for i, x in enumerate(all_x)}
    xlabel = list(map(str, all_x))
    ret = dict()
    for k, (x, y) in pm.items():
        ret[k] = [inv_f[_] for _ in x[:]], y
    return ret, xtick, xlabel


def annotate_stage(axes, all_x, xtick, xlabel):
    inv_f = {x: i for i, x in enumerate(all_x)}
    for c, st in enumerate(Stage.stages):
        xlabel[inv_f[st.start]] += '\n'+'%s.start' % (st.__name__)
        xlabel[inv_f[st.end]] += '\n'+'%s.end' % (st.__name__)
        for ax in axes:
            ax: matplotlib.axes.Axes 
            lim = ax.get_ylim()
            ax.fill_between([inv_f[st.start], inv_f[st.end]],*lim, color=f'C{c%9+1}', alpha=.2)
            ax.set_ylim(*lim)


def show_sequences(pm: plot_map, real_time=False):
    _, axes = plt.subplots(len(pm.keys()), 1, sharex=True, figsize=(15, 10))
    times = set(xx for x, y in pm.values() for xx in x)
    if not real_time:
        for st in Stage.stages:
            times.add(st.start)
            times.add(st.end)
    all_x = sorted(times)
    append_max(pm, all_x[-1])  # make graph look better
    if not real_time:
        pm, xtick, xlabel = normalize_x(pm, all_x)
    for ax, ((channel, name, act_name), (x, y)) in zip(axes, pm.items()):
        ax: matplotlib.axes.Axes
        ax.plot(x, y, lw=2)
        ax.set_ylabel(f'{name}\n{act_name}@{channel}')
        if not real_time:
            for x in xtick:
                ax.axvline(x, color='k', ls='dashed', lw=1, alpha=.5)
    if not real_time:
        annotate_stage(axes, all_x, xtick, xlabel)
        ax.set_xticks(xtick)
        ax.set_xticklabels(xlabel)
    plt.tight_layout()
    plt.subplots_adjust(hspace=.0)
    plt.savefig('1.pdf')
    plt.show()
