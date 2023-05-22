import matplotlib.pyplot as plt
import matplotlib.axes
from ..types import *


def append_max(pm: plot_map, max_time):
    for x, y in pm.values():
        x.append(max_time)
        y.append(y[-1])

def normalize_x(pm: plot_map, all_x: List[int]) -> Tuple[Dict, List[int], List[int]]:
    xtick = list(range(len(all_x)))
    inv_f = {x: i for i, x in enumerate(all_x)}
    xlabel = all_x
    ret = dict()
    for k, (x, y) in pm.items():
        ret[k] = [inv_f[_] for _ in x[:]], y
    return ret, xtick, xlabel
    

def show_sequences(pm: plot_map, real_time=False):
    _, axes = plt.subplots(len(pm.keys()), 1, sharex=True, figsize=(15, 10))
    all_x = sorted(set(xx for x, y in pm.values() for xx in x))
    append_max(pm, all_x[-1]) # make graph look better 
    if not real_time:
        pm, xtick, xlabel = normalize_x(pm, all_x)
        
    for ax, ((channel, name, act_name), (x, y)) in zip(axes, pm.items()):
        ax: matplotlib.axes.Axes
        ax.plot(x, y, lw=2)
        if not real_time:
            ax.set_xticks(xtick)
            ax.set_xticklabels(xlabel)
            for x in xtick:
                ax.axvline(x, color='k',ls='dashed', lw=1, alpha=.5)
        ax.set_ylabel(f'{name}\n{act_name}@{channel}')
    plt.tight_layout()
    plt.subplots_adjust(hspace=.0)
    plt.savefig('1.pdf')
    plt.show()
    
