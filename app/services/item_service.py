from fastapi import HTTPException
from app.utils.upsert_tags import upsert_tags
from app.models.item_modal import ClothingItemCreate




# GET ITEM BY ID

async def get_item_by_id_service(pool, item_id: str):
    try:
        async with pool.acquire() as connection:
            # Base item
            row = await connection.fetchrow(
                "SELECT * FROM ClothingItems WHERE id = $1;",
                item_id
            )


            if not row:
                raise HTTPException(status_code=404, detail="Item not found")

            item = dict(row)
            print("Incoming subcategory:", item)

            # Fetch tags
            colors = await connection.fetch("""
                SELECT c.name FROM Colors c
                JOIN ItemColors ic ON ic.color_id = c.id
                WHERE ic.item_id = $1;
            """, item_id)

            materials = await connection.fetch("""
                SELECT m.name FROM Materials m
                JOIN ItemMaterials im ON im.material_id = m.id
                WHERE im.item_id = $1;
            """, item_id)

            seasons = await connection.fetch("""
                SELECT s.name FROM Seasons s
                JOIN ItemSeasons is2 ON is2.season_id = s.id
                WHERE is2.item_id = $1;
            """, item_id)

            occasions = await connection.fetch("""
                SELECT o.name FROM Occasions o
                JOIN ItemOccasions io ON io.occasion_id = o.id
                WHERE io.item_id = $1;
            """, item_id)

            # Attach arrays
            item["colors"] = [r["name"] for r in colors]
            item["materials"] = [r["name"] for r in materials]
            item["seasons"] = [r["name"] for r in seasons]
            item["occasions"] = [r["name"] for r in occasions]

            return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# GET ITEMS BY USER ID
async def get_items_by_user_service(pool, user_id: str):
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT * FROM ClothingItems WHERE user_id = $1;",
                user_id
            )
            return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# CREATE ITEM
async def create_item_service(pool, item: ClothingItemCreate):
    """
    Creates a new wardrobe item and attaches all tags.
    """
    try:
        async with pool.acquire() as con:

            # Insert the base item row
            item_row = await con.fetchrow(
                """
                INSERT INTO clothingItems (
                    user_id, img_description, image_url, processed_img_url,
                    category_id, subcategory_id
                )
                VALUES ($1,$2,$3,$4,$5,$6)
                RETURNING id;
                """,
                item.user_id,
                item.img_description,
                item.image_url,
                item.processed_img_url,
                item.category_id,
                item.subcategory_id,
            )

            item_id = item_row["id"]


            # TAGS

            #user generated colors
            await upsert_tags(
                con, "Colors", "ItemColors", "color_id",
                item_id, item.user_id, item.colors
            )
            # user generated materials
            await upsert_tags(
                con, "Materials", "ItemMaterials", "material_id",
                item_id, item.user_id, item.materials
            )
            # user generated  occasions
            await upsert_tags(
                con, "Occasions", "ItemOccasions", "occasion_id",
                item_id, item.user_id, item.occasion
            )
            for season in item.season:
                season = season.strip().lower()

                season_row = await con.fetchrow(
                    "SELECT id FROM Seasons WHERE LOWER(name) = $1;",
                    season
                )
                if not season_row:
                    continue

                season_id = season_row["id"]

                # Directly link
                await con.execute(
                    """
                    INSERT INTO ItemSeasons (item_id, season_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING;
                    """,
                    item_id,
                    season_id
                )

            return {"message": "Item created", "item_id": item_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# DELETE ITEM
async def delete_item_service(pool, item_id: str):
    try:
        async with pool.acquire() as con:
            await con.execute(
                "DELETE FROM ClothingItems WHERE id = $1;",
                item_id
            )
            return {"message": "Item deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# UPDATE ITEM

async def update_item_service(pool, item_id: str, data: dict):
    """
    Updates item fields AND all tag relations.
    """
    user_id = data.get("user_id")
    print("Incoming subcategory:", data.get("subcategory_id"))
    if not user_id:
        raise HTTPException(400, "Missing user_id in request")

    try:
        async with pool.acquire() as conn:


            # 1. UPDATE MAIN FIELDS (description, category,subcategory)

            if "img_description" in data:
                await conn.execute(
                    "UPDATE ClothingItems SET img_description = $1 WHERE id = $2",
                    data["img_description"],
                    item_id
                )

            if "category_id" in data:
                await conn.execute(
                    "UPDATE ClothingItems SET category_id = $1 WHERE id = $2",
                    data["category_id"],
                    item_id
                )

            if "subcategory_id" in data:
                await conn.execute(
                    "UPDATE ClothingItems SET subcategory_id = $1 WHERE id = $2",
                    data["subcategory_id"],
                    item_id
                )

            # 2. HANDLE ALL TAG TYPES

            # Colors
            if "colors" in data:
                await upsert_tags(
                    conn, "Colors", "ItemColors", "color_id",
                    item_id, user_id, data["colors"]
                )

            # Materials
            if "materials" in data:
                await upsert_tags(
                    conn, "Materials", "ItemMaterials", "material_id",
                    item_id, user_id, data["materials"]
                )

            # Seasons
            print("Incoming seasons:", data.get("season"))
            if "season" in data and data["season"] is not None:
                await conn.execute("DELETE FROM ItemSeasons WHERE item_id = $1", item_id)

                SEASON_MAP = {
                    "spring": "Spring",
                    "summer": "Summer",
                    "autumn": "Autumn",
                    "fall": "Autumn",
                    "winter": "Winter",
                }

                for season in data["season"]:
                    key = (season or "").strip().lower()
                    canonical = SEASON_MAP.get(key)
                    if not canonical:
                        continue

                    season_row = await conn.fetchrow(
                        "SELECT id FROM Seasons WHERE name = $1;",
                        canonical
                    )
                    if not season_row:
                        continue

                    await conn.execute(
                        """
                        INSERT INTO ItemSeasons (item_id, season_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING;
                        """,
                        item_id,
                        season_row["id"]
                    )

            # Occasions
            if "occasion" in data:
                await upsert_tags(
                    conn, "Occasions", "ItemOccasions", "occasion_id",
                    item_id, user_id, data["occasion"]
                )


            return {"status": "updated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
