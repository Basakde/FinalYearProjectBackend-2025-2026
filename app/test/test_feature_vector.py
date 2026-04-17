
from app.helpers.vector_helpers import  build_item_feature_vector
from app.models.vector_ import CATEGORIES, COLORS, MATERIALS, OCCASIONS, SEASONS


def test_build_item_feature_vector():
    vec = build_item_feature_vector(
        category_name=["top"],
        color_names=["black", "white"],
        material_names=["cotton", "denim"],
        occasion_names=["casual", "work"],
        season_names=["summer", "spring"],
    )

    expected = (
        [1 if x == "top" else 0 for x in CATEGORIES] +
        [1 if x in ["black", "white"] else 0 for x in COLORS] +
        [1 if x in ["cotton", "denim"] else 0 for x in MATERIALS] +
        [1 if x in ["casual", "work"] else 0 for x in OCCASIONS] +
        [1 if x in ["summer", "spring"] else 0 for x in SEASONS]
    )

    assert vec == expected