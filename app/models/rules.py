from collections import defaultdict
import random

from app.models.category_mapping import CATEGORY_ID_TO_NAME

# Celsius - threshold values to include jackets in outfit suggestions
JACKET_TEMP_C = 14          # below this → include jacket
COLD_TEMP_C = 8            # very cold
HOT_TEMP_C = 22            # warm/hot

# If raining (or strong wind), show jacket on even if slightly warmer
RAIN_JACKET_TEMP_C = 17
WIND_JACKET_TEMP_C = 18
STRONG_WIND_MPS = 8   # ~29 km/h

def seasons_from_temp(temp_c: float) -> list[str]:
    if temp_c <= 8:
        return ["Winter"]
    if temp_c <= 14:
        return ["Autumn", "Winter"]
    if temp_c <= 19:
        return ["Spring", "Autumn"]
    if temp_c <= 25:
        return ["Spring", "Summer"]
    return ["Summer"]


def jacket_required(temp_c: float, is_raining: bool, wind_mps: float) -> bool:
    if temp_c <= JACKET_TEMP_C:
        return True
    if is_raining and temp_c <= RAIN_JACKET_TEMP_C:
        return True
    if wind_mps >= STRONG_WIND_MPS and temp_c <= WIND_JACKET_TEMP_C:
        return True
    return False

def needs_jacket(weather: dict) -> bool:
    temp = float(weather.get("main", {}).get("temp", 0))
    feels_like = float(weather.get("main", {}).get("feels_like", temp))
    wind_speed = float(weather.get("wind", {}).get("speed", 0))
    is_raining = any(w.get("main", "").lower() in ["rain", "drizzle", "thunderstorm"] for w in (weather.get("weather") or []))  # rain check

    effective = feels_like - (2 if wind_speed >= 6 else 0)
    return jacket_required(effective, is_raining, wind_speed)

def  build_slots(clothes: list[dict]) -> dict[str, list[dict]]:
    slots = defaultdict(list)

    for c in clothes:
        cat = c.get("category_id")
        cat_name=CATEGORY_ID_TO_NAME.get(cat) #get category names by id
        if not cat_name:
            continue

        cat_name_lower = cat_name.lower()

        #This turns one big mixed list into grouped buckets.
        if cat_name_lower in ["outerwear"]:
            slots["outerwear"].append(c)
        elif cat_name_lower in ["top"]:
            slots["top"].append(c)
        elif cat_name_lower in ["bottom"]:
            slots["bottom"].append(c)
        elif cat_name_lower in ["shoes"]:
            slots["shoes"].append(c)
        elif cat_name_lower in ["jumpsuit"]:
            slots["jumpsuit"].append(c)

    return slots



def pick_one(items: list[dict]) -> dict | None:
    return random.choice(items) if items else None
