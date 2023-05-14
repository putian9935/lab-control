def merge_seq_aio(ts: list[list[int]] = None, dts: list[list] = None, dvs: list[list] = None):
    ret = []
    if ts is None or not len(ts):
        return ret
    full_sequence = sorted(set(t for seq in ts for t in seq))
    for t, dt, dv in zip(ts, dts, dvs):
        inv_t = {v: k for k, v in enumerate(t)}
        new_dt, new_dv = [], []
        for tt in full_sequence:
            if tt in inv_t:
                new_dt.append(dt[inv_t[tt]])
                new_dv.append(dv[inv_t[tt]])
            else:
                if len(new_dv):
                    new_dv.append(new_dv[-1])
                else:
                    new_dv.append(dv[-1])
                new_dt.append(1)
        ret.append((list(full_sequence), new_dt, new_dv))
    return ret


if __name__ == '__main__':
    print(merge_seq_aio([[1, 2, 3], [2, 3, 10]], [
          [10, 20, 30], [20, 30, 10]], [[1, 2, 3], [1, 2, 3]]))
