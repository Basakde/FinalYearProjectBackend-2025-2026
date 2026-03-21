import math
import random
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

#After normalization, dot product behaves like cosine similarity.
def dot(a: list[float], b: list[float]) -> float:
    return sum(x*y for x, y in zip(a, b))

#It compares the user style vector with item feature vector using dot product.
def item_similarity(style_vec: list[float], item: dict) -> float:
    v = item.get("attr_vector")
    if v is None: # no item vector
        return -1e9 #gives very bad score
    v = l2_normalize([float(x) for x in v])
    return dot(style_vec, v)

def pick_top_k(items: list[dict], style_vec: list[float] | None, k: int) -> dict | None:
    if not items:
        return None
    if not style_vec:
        # no style yet -> fallback random
        return random.choice(items)

    #for each item it in the list, calculate a score using item_similarity
    scored = sorted(items, key=lambda it: item_similarity(style_vec, it), reverse=True) #Score items based on similarity and sort from best to worst
    k = min(k, len(scored)) # take top k item
    return random.choice(scored[:k]) #randomly choose one from that group