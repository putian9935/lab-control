from typing import Dict, Tuple, List

ts_key = int  # channel
ts_value = Tuple[List[int], int, str]  # sequence, init_state, signal_name
ts_map = Dict[ts_key, ts_value]
