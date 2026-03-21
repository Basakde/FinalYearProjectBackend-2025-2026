import traceback
import random as rnd
from typing import Optional

from fastapi import HTTPException

from app.helpers.similarity_function import item_similarity, pick_top_k, dot
from app.services.user_service import get_user_style_vec
from app.helpers.vector_math import l2_normalize
from app.models.rules import seasons_from_temp, needs_jacket, build_slots
from app.services.weather_service import get_weather_service


async def get_items_for_suggestions_service(
    pool,
    user_id: str,
    allowed_seasons: list[str],
    occasion_id: Optional[str],
) -> list[dict]:
    async with pool.acquire() as conn:
        #Get items not in laundry and check if the occasion selected
        rows = await conn.fetch(
            """
            SELECT DISTINCT ci.*
            FROM ClothingItems ci
            WHERE ci.user_id = $1
              AND (ci.in_laundry IS NULL OR ci.in_laundry = FALSE)

              -- Season filter:
              AND (
                    -- no season tags => allow
                    NOT EXISTS (
                        SELECT 1
                        FROM ItemSeasons is2
                        WHERE is2.item_id = ci.id
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM ItemSeasons is2
                        JOIN Seasons s ON s.id = is2.season_id
                        WHERE is2.item_id = ci.id
                          AND s.name = ANY($2::text[])
                    )
                  )

              -- Occasion filter: only if occasion_id is provided
              AND (
                    $3::uuid IS NULL
                    OR EXISTS (
                        SELECT 1
                        FROM ItemOccasions io
                        JOIN Occasions o ON o.id = io.occasion_id
                        WHERE io.item_id = ci.id
                          AND o.mapped_occasion_id = $3::uuid
                    )
                  );
            """,
            user_id,
            allowed_seasons,
            occasion_id,
        )

        return [dict(r) for r in rows]

#Main recommendation engine
async def get_outfit_suggestions_service(
    pool,
    lat: float,
    lon: float,
    user_id: str,
    occasion_id: Optional[str]
):
    try:
        weather = await get_weather_service(lat, lon) #get weather data will be used later for filtering

        seasons = seasons_from_temp(weather["main"]["temp"])#convert weather into allowed seasons
        include_jacket = needs_jacket(weather)

        # FIRST: Get clothes list (not in laundry+ season + optional occasion)
        clothes = await get_items_for_suggestions_service(pool, user_id, seasons, occasion_id)

        # SECOND :  Build slots
        slots = await build_slots(clothes)
        print("SLOT COUNTS (filtered):", {k: len(v) for k, v in slots.items()})

        # THIRD: This checks whether the filtered wardrobe is too strict and now missing basic pieces.
        need_shoes = len(slots.get("shoes", [])) == 0
        need_bottoms = len(slots.get("bottom", [])) == 0
        need_tops = len(slots.get("top", [])) == 0

        #Fallback : If occasion filtering caused missing essentials, it retries without occasion filter
        if occasion_id and (need_shoes or need_bottoms or need_tops):
            fallback_clothes = await get_items_for_suggestions_service(pool, user_id, seasons, None)
            fallback_slots = await build_slots(fallback_clothes)

            if need_shoes:
                slots["shoes"] = fallback_slots.get("shoes", [])
            if need_bottoms:
                slots["bottom"] = fallback_slots.get("bottom", [])
            if need_tops:
                slots["top"] = fallback_slots.get("top", [])

        # FOURTH: Load user style vector
        style_vec = await get_user_style_vec(pool, user_id)
        print("style_vec exists?", style_vec is not None)

        # FIFTH: Generate outfits (unique signatures)
        candidates = [] #all generated outfit possibilities
        attempts = 0 #how many times generation was tried
        seen = set() #used to prevent duplicates

        candidate_target = 30 #try to build 30 unique outfits
        max_attempts = candidate_target * 10 #safety limit so it doesn’t loop forever

        while len(candidates) < candidate_target and attempts < max_attempts:
            outfit = await make_one_outfit(slots, include_jacket, style_vec) #Builds one outfit
            if outfit is None:
                attempts += 1
                continue

           # avoid duplicates using signature
            sig = outfit_signature(outfit)
            if sig in seen:
                attempts += 1
                continue

            #score whole outfit
            seen.add(sig)
            score = 0.0
            if style_vec:
                oufit_vector = outfit_vec_from_outfit(outfit, len(style_vec))
                if oufit_vector:
                    score = dot(l2_normalize(style_vec), oufit_vector)

            #append the candidate with outfit itself and its score
            candidates.append({"outfit": outfit, "score": score})
            attempts += 1

        print("CANDIDATES:", len(candidates), "attempts:", attempts)

        #sort outfits so best one comes first
        candidates.sort(key=lambda x: x["score"], reverse=True)

        N_TOTAL = 15 # choose 15 outfit
        N_TOP = 10 # top 10 good
        N_RANDOM_LOW = 5 # last 5 inn the sorted list

        top_band = candidates[:min(N_TOP, len(candidates))] #10 top strong match

        low_pool = candidates[-10:] if len(candidates) > 10 else candidates[N_TOP:]# if there are more than 10 candidates, take the last 10 ranked candidates
        low_band = rnd.sample(low_pool, k=min(N_RANDOM_LOW, len(low_pool))) if low_pool else [] # pick random 5 outfit from low ranked

        picked = top_band + low_band # combine them together

        #Since some outfit could theoretically appear in both top and low lists, this removes duplicates again.
        seen2 = set()
        final_scored = []
        for c in picked:
            sig = outfit_signature(c["outfit"])
            if sig in seen2:
                continue
            seen2.add(sig)
            final_scored.append(c)

    #If after deduplication if we still have fewer than 15, it fills from remaining sorted candidates
        if len(final_scored) < N_TOTAL:
            for c in candidates:
                sig = outfit_signature(c["outfit"])
                if sig in seen2:
                    continue
                seen2.add(sig)
                final_scored.append(c)
                if len(final_scored) >= N_TOTAL:
                    break


       #final result sent to frontend is only the outfit dictionaries, not the scores
        final_scored = final_scored[:N_TOTAL]
        outfits = [c["outfit"] for c in final_scored]
        scores = [float(c["score"]) for c in final_scored]
        labels = [f"Top {i + 1}" if i < N_TOP else f"D{i - N_TOP + 1}" for i in range(len(final_scored))]

        print("TOP SCORES:", [round(c["score"], 3) for c in final_scored[:N_TOP]])
        print("RANDOM LOW SCORES:", [round(c["score"], 3) for c in final_scored[N_TOP:]])

        return {
            "weather": {
                "temp": float(weather["main"]["temp"]),
                "icon": weather["weather"][0]["icon"],
                "wind": float((weather.get("wind") or {}).get("speed", 0)),
            },
            "rules": {
                "allowed_seasons": seasons,
                "include_jacket": include_jacket,
                "occasion_id": occasion_id,
            },
            "suggestions": outfits,
            "scores": scores,
            "labels": labels
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR MESSAGE:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def make_one_outfit(slots: dict, include_jacket: bool, style_vec: list[float] | None) -> dict | None:
    tops = slots.get("top", [])
    bottoms = slots.get("bottom", [])
    jumpsuits = slots.get("jumpsuit", [])
    shoes_list = slots.get("shoes", [])
    outerwear_list = slots.get("outerwear", [])

     #check if it possible to build one piece and two piece outfits
    can_twopiece = bool(tops and bottoms and shoes_list)
    can_onepiece = bool(jumpsuits and shoes_list)

    if not can_twopiece and not can_onepiece:
        return None

    # choose outfit type
    if can_twopiece and can_onepiece:
        make_one = rnd.choice([True, False])  # randomly select one piece outfits or two piece outfits to generate
    elif can_onepiece:
        make_one = True
    else:
        make_one = False

    if make_one:
        outfit = {
            "type": "onepiece",
            "top": None,
            "bottom": None,
            "jumpsuit": pick_top_k(jumpsuits, style_vec, k=6),
            "shoes": pick_top_k(shoes_list, style_vec, k=6),
            "outerwear": None,
        }
    else:
        outfit = {
            "type": "twopiece",
            "top": pick_top_k(tops, style_vec, k=6),
            "bottom": pick_top_k(bottoms, style_vec, k=6),
            "jumpsuit": None,
            "shoes": pick_top_k(shoes_list, style_vec, k=6),
            "outerwear": None,
        }

    if include_jacket:
        outfit["outerwear"] = pick_top_k(outerwear_list, style_vec, k=4)

    # Debug sims (optional)
    #if style_vec:
      #  chosen_outer = outfit.get("outerwear")
       # if chosen_outer:
       #     print("Chosen OUTER sim:", item_similarity(style_vec, chosen_outer))

      #  chosen_top = outfit.get("top")
      #  if chosen_top:
     #       print("Chosen TOP sim:", item_similarity(style_vec, chosen_top))

      #  chosen_bottom = outfit.get("bottom")
       # if chosen_bottom:
      #      print("Chosen BOTTOM sim:", item_similarity(style_vec, chosen_bottom))

     #   chosen_shoes = outfit.get("shoes")
      #  if chosen_shoes:
      #      print("Chosen SHOES sim:", item_similarity(style_vec, chosen_shoes))

       # chosen_jumpsuit = outfit.get("jumpsuit")
        #if chosen_jumpsuit:
       #     print("Chosen JUMPSUIT sim:", item_similarity(style_vec, chosen_jumpsuit))

    return outfit

def outfit_signature(outfit: dict) -> tuple:
    return (
        outfit.get("type"),
        item_key(outfit.get("top")),
        item_key(outfit.get("bottom")),
        item_key(outfit.get("shoes")),
        item_key(outfit.get("outerwear")),
        item_key(outfit.get("jumpsuit")),
    )


def item_key(x: dict | None) -> str:
    return str(x.get("id") if x else "none")

#It gathers item vectors from outfit pieces.
def outfit_vec_from_outfit(outfit: dict, style_len: int) -> list[float] | None:
    vecs: list[list[float]] = []

    #skips: missing items,items without vectors,vectors with wrong length
    for key in ("top", "bottom", "shoes", "outerwear", "jumpsuit"):
        it = outfit.get(key)
        if not it:
            continue
        v = it.get("attr_vector")
        if v is None:
            continue
        v = [float(x) for x in v]
        if len(v) != style_len:
            continue
        vecs.append(l2_normalize(v))

    if len(vecs) < 2:
        return None

    #It averages the normalized item vectors to create one combined outfit representation.
    L = len(vecs[0])
    sums = [0.0] * L
    for v in vecs:
        for i, x in enumerate(v):
            sums[i] += x

    avg = [s / len(vecs) for s in sums]
    return l2_normalize(avg)


def outfit_score(style_vec: list[float] | None, outfit_vec: list[float] | None) -> float:
    if not style_vec or not outfit_vec:
        return 0.0
    return dot(style_vec, outfit_vec)