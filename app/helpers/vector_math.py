import math
from typing import List

#DELETE THIS FILE LATER IT IS MOVED TO IMILARITY FUNCTION

def l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]

def ema_update(user_vec: List[float], signal_vec: List[float], alpha: float, sign: int = +1) -> List[float]:
    """
    sign=+1  -> pull user taste toward signal
    sign=-1  -> push user taste away from signal
    """
    u = l2_normalize(user_vec)
    v = l2_normalize(signal_vec)

    mixed = [(1 - alpha) * ui + alpha * (sign * vi) for ui, vi in zip(u, v)]
    return l2_normalize(mixed)