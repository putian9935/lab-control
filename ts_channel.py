# from load_decay_seq import *
import numpy as np
import matplotlib.pyplot as plt

sequences = {}
init_states = {}
names = {}
full_sequence = []


class TSChannel:
    def __init__(self, channel, init_state=0) -> None:
        init_states[channel] = init_state
        self.ch = channel

    def __call__(self, func):
        sequences[self.ch] = func()
        names[self.ch] = func.__name__

        def ret():
            return sequences[self.ch]
        return ret


def save_sequences(fname):
    global full_sequence
    s = set()
    for seq in sequences.values():
        for t in seq:
            s.add(t)
    full_sequence = sorted(list(s))

    inv = {k: v for v, k in enumerate(full_sequence)}

    @np.vectorize
    def inv_f(v):
        return inv[v]

    full_ch = [full_sequence]

    headers = (
        'device,'+','.join(['TS']*len(sequences)),
        'sub device,'+','.join('TS ch%d %s' % (ch, name)
                               for ch, name in names.items()),
        'time,'+','.join(map(str, names.values()))
    )

    for i in sequences.keys():
        new_row = np.zeros(len(full_sequence), dtype=int)
        if len(sequences[i]):
            new_row[inv_f(sequences[i])] = 1
        full_ch.append(init_states[i] ^ (np.cumsum(new_row) & 1))

    np.savetxt(fname, np.array(full_ch).T, delimiter=",",
               fmt="%i", header='\n'.join(headers), comments='')


def show_sequences():
    def square(init_s, n):
        for _ in range(n):
            yield init_s
            yield init_s ^ 1
            yield init_s ^ 1
            yield init_s

    _, axes = plt.subplots(len(init_states.keys()), 1, sharex=True)
    for init_s, name, seq, ax in zip(init_states.values(), names.values(), sequences.values(), axes):
        x = [0] + list(_ for _ in seq for __ in range(2)) + \
            [full_sequence[-1]+1]
        y = [init_s] + list(square(init_s, len(seq)//2)) + [init_s]
        ax.plot(x, y)
        ax.set_ylabel(name, rotation='horizontal', ha='right')
    plt.tight_layout()
    plt.show()


s = 1000*1000  # us
ms = 1000  # us
us = 1  # us

if __name__ == '__main__':
    from load_decay_seq import *

    save_sequences("2.csv")
    show_sequences()
