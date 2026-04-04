import math
from typing import List

#Normalization makes vectors have length 1

def l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def ema_update(user_vec: List[float], signal_vec: List[float], learning_rate: float, feedback_direction: int = +1) -> List[float]:
    """
    feedback_direction=+1  -> pull user taste toward signal
    feedback_direction=-1  -> push user taste away from signal
    """
    current_user_style_vector = l2_normalize(user_vec)
    outfit_feature_vector = l2_normalize(signal_vec)

    updated_vector = [
        (1 - learning_rate) * current_preference
        + learning_rate * (feedback_direction * outfit_feature_strength)
        for current_preference, outfit_feature_strength
        in zip(current_user_style_vector, outfit_feature_vector)
    ]
    return l2_normalize(updated_vector)