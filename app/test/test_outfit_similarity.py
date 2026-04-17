
import os
# Fake env vars so importing the service file does not crash during testing
os.environ["SUPABASE_URL"] = "https://fake.supabase.co"
os.environ["SUPABASE_KEY"] = "fake-key"
os.environ["SUPABASE_ANON_KEY"] = "fake-anon-key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "fake-service-role-key"


from app.services.outfit_suggestions_service import outfit_vec_from_outfit, outfit_score
from app.helpers.vector_math import l2_normalize
from app.helpers.vector_helpers import  build_item_feature_vector


def test_outfit_similarity_ranking():
    user_vec = build_item_feature_vector(
        category_name=["top"],
        color_names=["black", "white"],
        material_names=["cotton", "denim"],
        occasion_names=["casual", "work"],
        season_names=["summer", "spring"],
    )

    good_outfit = {
        "top": {
            "attr_vector": build_item_feature_vector(
                category_name=["top"],
                color_names=["black"],
                material_names=["cotton"],
                occasion_names=["casual"],
                season_names=["summer"],
            )
        },
        "bottom": {
            "attr_vector": build_item_feature_vector(
                category_name=["bottom"],
                color_names=["white"],
                material_names=["denim"],
                occasion_names=["work"],
                season_names=["spring"],
            )
        },
        "shoes": {
            "attr_vector": build_item_feature_vector(
                category_name=["shoes"],
                color_names=["black"],
                material_names=["leather"],
                occasion_names=["casual"],
                season_names=["summer"],
            )
        },
        "outerwear": None,
        "jumpsuit": None,
    }

    bad_outfit = {
        "top": {
            "attr_vector": build_item_feature_vector(
                category_name=["top"],
                color_names=["pink"],
                material_names=["silk"],
                occasion_names=["party"],
                season_names=["winter"],
            )
        },
        "bottom": {
            "attr_vector": build_item_feature_vector(
                category_name=["bottom"],
                color_names=["green"],
                material_names=["wool"],
                occasion_names=["formal"],
                season_names=["winter"],
            )
        },
        "shoes": {
            "attr_vector": build_item_feature_vector(
                category_name=["shoes"],
                color_names=["orange"],
                material_names=["rubber"],
                occasion_names=["sport"],
                season_names=["winter"],
            )
        },
        "outerwear": None,
        "jumpsuit": None,
    }

    norm_user = l2_normalize(user_vec)

    good_outfit_vec = outfit_vec_from_outfit(good_outfit, len(user_vec))
    bad_outfit_vec = outfit_vec_from_outfit(bad_outfit, len(user_vec))

    good_score = outfit_score(norm_user, good_outfit_vec)
    bad_score = outfit_score(norm_user, bad_outfit_vec)

    print("\nGood outfit score:", good_score)
    print("\nBad outfit score:", bad_score)

    assert good_score > bad_score