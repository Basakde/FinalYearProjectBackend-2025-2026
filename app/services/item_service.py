from datetime import datetime

from fastapi import HTTPException

from app.models.category_mapping import CATEGORY_ID_TO_NAME, SEASON_MAP
from app.models.vector_helpers import build_item_feature_vector
from app.utils.upsert_tags import upsert_tags
from app.models.item_modal import ClothingItemCreate
from datetime import datetime, timedelta, timezone


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
                "SELECT * FROM ClothingItems WHERE user_id = $1 ORDER BY created_at DESC",
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
                    category_id, subcategory_id, in_laundry
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                RETURNING id;
                """,
                item.user_id,
                item.img_description,
                item.image_url,
                item.processed_img_url,
                item.category_id,
                item.subcategory_id,
                item.in_laundry,
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
                item_id, item.user_id, item.occasions
            )
            for season in item.seasons:
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

            cat_name = CATEGORY_ID_TO_NAME.get(item.category_id)

            # after you have item_id and the tag lists:
            feature_vector = build_item_feature_vector(
                category_name=[cat_name] if cat_name else [],
                color_names=item.colors or [],
                material_names=item.materials or [],
                occasion_names=item.occasions or [],
                season_names=item.seasons or [],
            )

            await con.execute(
                """
                UPDATE clothingItems 
                SET attr_vector = $1, 
                    attr_schema_version = 1
                WHERE id = $2
                """,
                feature_vector,
                item_id
            )
            return {"status": "created","id":str(item_id)}



    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE ITEM
async def delete_item_service(pool, item_id: str):
    try:
        async with pool.acquire() as con:
            async with con.transaction():
                await con.execute(
                    """
                    UPDATE Outfits
                    SET is_favorite = FALSE
                    WHERE is_favorite = TRUE
                      AND id IN (
                          SELECT outfit_id
                          FROM OutfitItems
                          WHERE item_id = $1
                      );
                    """,
                    item_id
                )

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

            if "in_laundry" in data:
                await conn.execute(
                    "UPDATE ClothingItems SET in_laundry = $1 WHERE id = $2",
                    data["in_laundry"],
                    item_id
                )

            # 2. HANDLE ALL TAG TYPES

            # Colors
            if "colors" in data and data["colors"] is not None:
                # delete all existing relations first
                await conn.execute("DELETE FROM ItemColors WHERE item_id = $1", item_id)

                # then insert new ones (if list not empty)
                await upsert_tags(
                    conn, "Colors", "ItemColors", "color_id",
                    item_id, user_id, data["colors"]
                )

            # Materials
            if "materials" in data and data["materials"] is not None:
                await conn.execute("DELETE FROM ItemMaterials WHERE item_id = $1", item_id)
                await upsert_tags(conn, "Materials", "ItemMaterials", "material_id",
                                  item_id, user_id, data["materials"])

            if "occasions" in data and data["occasions"] is not None:
                await conn.execute("DELETE FROM ItemOccasions WHERE item_id = $1", item_id)
                await upsert_tags(conn, "Occasions", "ItemOccasions", "occasion_id",
                                  item_id, user_id, data["occasions"])

            # Seasons
            if "seasons" in data and data["seasons"] is not None:
                await conn.execute("DELETE FROM ItemSeasons WHERE item_id = $1", item_id)

                for season in data["seasons"]:
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

            cat_name = CATEGORY_ID_TO_NAME.get(data["category_id"])

            feature_vector = build_item_feature_vector(
                category_name=[cat_name] if cat_name else [],
                color_names=data["colors"] or [],
                material_names=data["materials"] or [],
                occasion_names=data["occasions"] or [],
                season_names=data["seasons"] or [],
            )

            await conn.execute(
                """
                UPDATE clothingItems 
                SET attr_vector = $1, 
                    attr_schema_version = 1
                WHERE id = $2
                """,
                feature_vector,
                item_id
            )
            return {"status": "created", "id": str(item_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_unworn_cutoff(days: int):
    return datetime.now(timezone.utc) - timedelta(days=days)

async def get_unworn_items_service(pool, user_id: str, days: int = 14):
    cutoff_date = get_unworn_cutoff(days)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ci.id,
                ci.image_url,
                ci.processed_img_url,
                ci.img_description,
                MAX(owl.worn_at) AS last_worn_at
            FROM clothingItems ci
            LEFT JOIN outfitItems oi
                ON oi.item_id = ci.id
            LEFT JOIN outfit_wear_log owl
                ON owl.outfit_id = oi.outfit_id
            WHERE ci.user_id = $1
            GROUP BY ci.id, ci.image_url, ci.processed_img_url, ci.img_description
            HAVING MAX(owl.worn_at) IS NULL
                OR MAX(owl.worn_at) < $2
            ORDER BY last_worn_at NULLS FIRST
            """,
            user_id,
            cutoff_date,
        )

    return [dict(r) for r in rows]

async def get_most_worn_items_service(pool, user_id: str, limit: int = 10):
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    ci.id,
                    ci.image_url,
                    ci.img_description,
                    COUNT(owl.id) AS wear_count,
                    MAX(owl.worn_at) AS last_worn_at
                FROM ClothingItems ci
                JOIN OutfitItems oi
                    ON oi.item_id = ci.id
                JOIN outfit_wear_log owl
                    ON owl.outfit_id = oi.outfit_id
                WHERE ci.user_id = $1
                GROUP BY
                    ci.id,
                    ci.image_url,
                    ci.img_description
                 ORDER BY wear_count DESC, last_worn_at DESC
                LIMIT $2;
                """,
                user_id,
                limit,
            )

            return {"items": [dict(row) for row in rows]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))