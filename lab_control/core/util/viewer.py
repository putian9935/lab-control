import matplotlib.pyplot as plt
from ..types import *


def show_sequences(pm: plot_map):
    _, axes = plt.subplots(len(pm.keys()), 1, sharex=True)
    for ax, ((channel, name, act_name), (x, y)) in zip(axes, pm.items()):
        ax.plot(x, y)
        ax.set_ylabel(f'{name}, {act_name}@{channel}')
    plt.tight_layout()
    plt.show()
