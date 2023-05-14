from typing import Dict
import numpy as np
ts_mapping = tuple[Dict[int, list[int]], bool]


def merge_seq(*seqs: tuple[ts_mapping]) -> ts_mapping:
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
                    print(f'[WARNING] Signal {name} and {names[k]} use the same time sequencer channel {k}')

    ret: ts_mapping = dict()
    for k in tmp.keys():
        ret[k] = (sorted(tmp[k]), pols[k], names[k])
    return ret


def pulsify(l: list, width=50):
    state = 1

    def f(x):
        nonlocal state
        state ^= 1
        return x if not state else x + width
    return [f(x) for x in l for _ in range(2)]


def to_pulse(mapping: ts_mapping, pulse: bool):
    if not pulse:
        return mapping
    ret: ts_mapping = dict()
    for k, (l, p, n) in mapping.items():
        ret[k] = pulsify(l), p, n
    return ret



def save_sequences(sequences : dict[int, tuple[list[int], bool, str]], fname):
    s = set()
    names = dict()
    for k, (seq, p, n) in sequences.items():
        for t in seq:
            s.add(t)
        names[k] = n
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

    for seq, init, n in sequences.values():
        new_row = np.zeros(len(full_sequence), dtype=int)
        if len(seq):
            new_row[inv_f(seq)] = 1
        full_ch.append(init ^ (np.cumsum(new_row) & 1))
    np.savetxt(fname, np.array(full_ch).T, delimiter=",",
               fmt="%i", header='\n'.join(headers), comments='')
    
    ch_inv = {ch:i+1 for i, ch in enumerate(sequences.keys())}
    with open('out', 'w'):
        pass 
    with open('out', 'a') as f:
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
    print(save_sequences(merge_seq(*({1: ([1, 2, 3], 0, 'a'), 2: ([2, 3, 4],1, 'b')}, {1: ([2, 3, 4],0, 'a')})), 'a'))
