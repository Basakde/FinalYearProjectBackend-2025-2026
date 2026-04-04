import math
import random
from app.helpers.vector_math import l2_normalize


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