import numpy as np
from datetime import datetime
import os
from ..types import *


def merge_seq(*seqs: Tuple[ts_map]) -> ts_map:
    tmp: Dict[int, set] = dict()
    pols = dict()
    names = dict()
    for seq in seqs:
        for k, (v, pol, name) in seq.items():
            if k not in tmp:
                tmp[k] = set(v)
                pols[k] = pol
                names[k] = name
            else:
                tmp[k] = tmp[k].union(v)
                if pols[k] ^ pol:
                    raise ValueError(
                        f"Contradicting polarity for time sequencer channel {k}!")
                if name != names[k]:
                    print(
                        f'[WARNING] Signal {name} and {names[k]} use the same time sequencer channel {k}')

    ret: ts_map = dict()
    for k in tmp.keys():
        ret[k] = (sorted(tmp[k]), pols[k], names[k])
    return ret


def pulsify(l: List[int], width=50):
    state = 1

    def f(x: int):
        nonlocal state
        state ^= 1
        return x if not state else x + width
    return [f(x) for x in l for _ in range(2)]


def to_pulse(mapping: ts_map, pulse: bool):
    if not pulse:
        return mapping
    ret: ts_map = dict()
    for k, (l, p, n) in mapping.items():
        ret[k] = pulsify(l), p, n
    return ret


def square(init_s, n):
    for _ in range(n):
        yield init_s
        yield init_s ^ 1
        yield init_s ^ 1
        yield init_s


def to_plot(init_s, seq):
    x = [0] + list(_ for _ in seq for __ in range(2))
    y = [init_s] 
    for _ in seq:
        y.append(y[-1])
        y.append(y[-1]^1)
    print(x, y)
    return x, y

def merge_plot_maps(*pms: plot_map) -> plot_map:
    ret: plot_map = dict()
    for pm in pms:
        if pm is None: continue
        for k, (x, y) in pm.items():
            if k in ret:
                # don't use +=, error with tuples
                ret[k][0].extend(x) 
                ret[k][1].extend(y) 
            else:
                ret[k] = x, y
    return ret 


def save_sequences(sequences: ts_map, fname: str):
    """ Returns the full experiment time """
    s = set()
    names = dict()
    for k, (seq, p, n) in sequences.items():
        for t in seq:
            s.add(t)
        names[k] = n
    if not len(s):
        raise ValueError(
            "Empty sequence detected! Aborted. Did you forgot to set to_fpga=False in the Experiment definition?")

    full_sequence: list[int] = sorted(list(s))

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

    for seq, init, n in sequences.values():
        new_row = np.zeros(len(full_sequence), dtype=int)
        if len(seq):
            new_row[inv_f(seq)] = 1
        full_ch.append(init ^ (np.cumsum(new_row) & 1))
    # save csv
    np.savetxt(fname, np.array(full_ch).T, delimiter=",",
               fmt="%i", header='\n'.join(headers), comments='')

    if not os.path.exists('saved_sequences'):
        os.mkdir('saved_sequences')
    np.savetxt(f'saved_sequences/{datetime.now():%Y%m%d%H%M%S}.csv', np.array(full_ch).T, delimiter=",",
               fmt="%i", header='\n'.join(headers), comments='')

    # save out
    ch_inv = {ch: i+1 for i, ch in enumerate(sequences.keys())}
    with open('out', 'w') as f:
        f.write('1\n')
        f.write(';'.join(map(lambda _: str(int(_)), full_ch[0]))+'\n')
        for ch in range(1, 65):
            if ch in ch_inv:
                f.write(';'.join(map(str, full_ch[ch_inv[ch]]))+'\n')
            else:
                f.write(';'.join(map(str, np.zeros_like(full_ch[0])))+'\n')
    return full_ch[0][-1]


if __name__ == '__main__':
    print(pulsify([1000, 2000]))
    print(save_sequences(merge_seq(
        *({1: ([1, 2, 3], 0, 'a'), 2: ([2, 3, 4], 1, 'b')}, {1: ([2, 3, 4], 0, 'a')})), 'a'))
