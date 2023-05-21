from typing import Dict, Tuple, List, Union

ts_key = int  # channel
ts_value = Tuple[List[int], int, str]  # sequence, init_state, signal_name
ts_map = Dict[ts_key, ts_value]

reals = Union[int, float]

plot_key = Tuple[int, str] # channel, name
plot_value = Tuple[List[int], List[reals]]
plot_map = Dict[plot_key, plot_value]
