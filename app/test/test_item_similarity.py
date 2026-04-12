from app.helpers.similarity_function import item_similarity
from app.helpers.vector_math import l2_normalize
from app.models.vector_helpers import  build_item_feature_vector


def test_item_similarity():
    # This test checks whether an item that is similar to the user's style
    # receives a higher similarity score than a different item.
    user_vec = build_item_feature_vector(
        category_name=["top"],
        color_names=["black", "white"],
        material_names=["cotton", "denim"],
        occasion_names=["casual", "work"],
        season_names=["summer", "spring"],
    )

    close_item = {
        "attr_vector": build_item_feature_vector(
            category_name=["top"],
            color_names=["black", "white"],
            material_names=["cotton"],
            occasion_names=["casual"],
            season_names=["summer"],
        )
    }

    far_item = {
        "attr_vector": build_item_feature_vector(
            category_name=["shoes"],
            color_names=["pink"],
            material_names=["leather"],
            occasion_names=["party"],
            season_names=["winter"],
        )
    }

    sim_close = item_similarity(l2_normalize(user_vec), close_item)
    sim_far = item_similarity(l2_normalize(user_vec), far_item)

    print("\nSimilarity close item",sim_close)
    print("\nSimilarity far item", sim_far)
    assert sim_close > sim_far

def test_item_similarity2():
    # This test checks whether an item with exactly the same attributes as the user style
    # receives a higher similarity score than an item with a less relevant attributes.
    user_vec = build_item_feature_vector(
        category_name=["top"],
        color_names=["black", "white"],
        material_names=["cotton", "denim"],
        occasion_names=["casual", "work"],
        season_names=["summer", "spring"],
    )

    close_item = {
        "attr_vector": build_item_feature_vector(
            category_name=["top"],
            color_names=["black", "white"],
            material_names=["cotton", "denim"],
            occasion_names=["casual", "work"],
            season_names=["summer", "spring"],
        )
    }

    far_item = {
        "attr_vector": build_item_feature_vector(
            category_name=["top"],
            color_names=["pink"],
            material_names=["leather"],
            occasion_names=["party"],
            season_names=["winter"],
        )
    }

    sim_close = item_similarity(l2_normalize(user_vec), close_item)
    sim_far = item_similarity(l2_normalize(user_vec), far_item)

    print("Similarity",sim_close)
    print("Similarity", sim_far)
    assert sim_close > sim_far