import os
import traceback
from random import random
import random as rnd

import requests
from fastapi import HTTPException

from app.models.rules import seasons_from_temp, needs_jacket, build_slots, pick_one
from app.services.weather_service import get_weather_service
from typing import Optional

async def get_items_for_suggestions_service(
    pool,
    user_id: str,
    allowed_seasons: list[str],
    occasion_id: Optional[str],
) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ci.*
            FROM ClothingItems ci
            WHERE ci.user_id = $1
              AND (ci.in_laundry IS NULL OR ci.in_laundry = FALSE)

              --  Season filter:
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

              --  Occasion filter: only if occasion_id is provided
              AND (
            $3::uuid IS NULL
            OR EXISTS (
                SELECT 1
                FROM ItemOccasions io
                JOIN Occasions o ON o.id = io.occasion_id
                WHERE io.item_id = ci.id
                  AND o.mapped_occasion_id = $3::uuid
            )
          )
    """,
            user_id,
            allowed_seasons,
            occasion_id,
        )
        print("PRINT", rows)
        print(">>> occasion_master_id:", occasion_id)
        print(">>> allowed_seasons:", allowed_seasons)

        return [dict(r) for r in rows]



async def get_outfit_suggestions_service(pool,lat: float, lon: float, user_id:str, occasion_id: Optional[str] , n:int = 5):
    try:
        weather = await get_weather_service(lat,lon)

        seasons = seasons_from_temp(weather["main"]["temp"])
        include_jacket = needs_jacket(weather)

        clothes = await get_items_for_suggestions_service(pool, user_id, seasons, occasion_id)

        slots = await build_slots(clothes)

        outfits = []
        attempts = 0
        max_attempts = n * 10
        seen = set()

        while len(outfits) < n and attempts < max_attempts:
            outfit = await make_one_outfit(slots, include_jacket)
            if outfit is None:
                attempts += 1
                continue
            sig = outfit_signature(outfit)
            if sig not in seen:
                seen.add(sig)
                outfits.append(outfit)
            attempts += 1

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
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR MESSAGE:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def make_one_outfit(slots: dict, include_jacket: bool) -> dict:
    tops = slots.get("top", [])
    bottoms = slots.get("bottom", [])
    jumpsuit = slots.get("jumpsuit", [])
    shoes_list = slots.get("shoes", [])
    outerwear_list = slots.get("outerwear", [])

    can_twopiece = bool(tops and bottoms and shoes_list)
    can_onepiece = bool(jumpsuit and shoes_list)

    # If neither possible -> return None (so caller skips it)
    if not can_twopiece and not can_onepiece:
        return None

    # Choose which kind to build
    if can_twopiece and can_onepiece:
        make_one = rnd.choice([True, False])   # 50/50
    elif can_onepiece:
        make_one = True
    else:
        make_one = False

    if make_one:
        outfit = {
            "type":"onepiece",
            "top": None,
            "bottom": None,
            "jumpsuit": await pick_one(jumpsuit),
            "shoes": await pick_one(shoes_list),
            "outerwear": None,
        }
    else:
        outfit = {
            "type":"twopiece",
            "top": await pick_one(tops),
            "bottom": await pick_one(bottoms),
            "jumpsuit": None,
            "shoes": await pick_one(shoes_list),
            "outerwear": None,
        }

    if include_jacket:
        outfit["outerwear"] = await pick_one(outerwear_list)

    return outfit


def outfit_signature(outfit : dict) -> tuple:
    return (
        outfit.get("type"),
        item_key(outfit.get("top")),
        item_key(outfit.get("bottom")),
        item_key(outfit.get("shoes")),
        item_key(outfit.get("outerwear")),
        item_key(outfit.get("jumpsuit"))
    )

def item_key(x:dict | None) ->str:
    return str(x.get("id") if x else "none")


