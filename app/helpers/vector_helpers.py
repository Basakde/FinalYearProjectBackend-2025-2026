# app/services/feature_vector.py

from __future__ import annotations
from typing import List

from app.models.vector_ import CATEGORIES, COLORS, MATERIALS, OCCASIONS, SEASONS


def normalize_label(value: str) -> str:
    """Lowercase + trim. Keeps matching consistent."""
    return (value or "").strip().lower()


def multi_hot_encode(selected_values: List[str], vocabulary: List[str]) -> List[int]:
    """
    Multi-hot encoding:
    - Each known selected value sets its index to 1
    - Unknown values map to 'other' if vocabulary includes it
    """
    vector = [0] * len(vocabulary)
    index_by_value = {value: index for index, value in enumerate(vocabulary)}

    for raw in (selected_values or []):
        key = normalize_label(raw)
        if not key:
            continue

        if key in index_by_value:
            vector[index_by_value[key]] = 1
        elif "other" in index_by_value:
            vector[index_by_value["other"]] = 1

    return vector

def build_item_feature_vector(
    category_name: List[str],
    color_names: List[str],
    material_names: List[str],
    occasion_names: List[str],
    season_names: List[str],
) -> List[int]:
    """
    Builds one feature vector for a wardrobe item.
    Vector layout (concatenated in this exact order):
      [categories | colors | materials | occasions | seasons]
    """
    category_vec = multi_hot_encode(category_name, CATEGORIES)
    color_vec = multi_hot_encode(color_names, COLORS)
    material_vec = multi_hot_encode(material_names, MATERIALS)
    occasion_vec = multi_hot_encode(occasion_names, OCCASIONS)
    season_vec = multi_hot_encode(season_names, SEASONS)
    return category_vec + color_vec + material_vec + occasion_vec + season_vec
