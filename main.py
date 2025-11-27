import base64
import json
import os
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from models import ClothingItemCreate, UserCreate, ItemUpdate
from db import connect_to_db, close_db, DATABASE_URL
from io import BytesIO
from rembg import remove, new_session
from PIL import Image

app = FastAPI()
SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase=create_client(SUPABASE_URL,SUPABASE_SERVICE_KEY)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = new_session("u2netp")
@app.on_event("startup")
async def startup():
    app.state.db = await connect_to_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db(app.state.db)

@app.get("/")
async def root():
    return {"message": "Backend connected to Supabase!"}


# TAG UPSERT HELPER

async def upsert_tags(conn, table_name, pivot_table, pivot_field, item_id, user_id, tags):

    if not tags:
        return

    for tag in tags:

        # Insert tag or return existing one
        tag_id = await conn.fetchval(
            f"""
            INSERT INTO {table_name} (user_id, name)
            VALUES ($1, $2)
            ON CONFLICT(user_id, name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            user_id, tag
        )

        # Insert pivot relation
        await conn.execute(
            f"""
            INSERT INTO {pivot_table} (item_id, {pivot_field})
            VALUES ($1::uuid, $2::uuid)
            ON CONFLICT DO NOTHING
            """,
            item_id, tag_id
        )


@app.get("/item/{item_id}")
async def get_item_by_id(item_id: str, request: Request):
    pool = request.app.state.db
    try:
        async with pool.acquire() as connection:

            # base item
            row = await connection.fetchrow(
                "SELECT * FROM ClothingItems WHERE id = $1;",
                item_id
            )
            if not row:
                raise HTTPException(status_code=404, detail="Item not found")

            item = dict(row)

            # Colors
            colors = await connection.fetch("""
                SELECT c.name 
                FROM Colors c
                JOIN ItemColors ic ON ic.color_id = c.id
                WHERE ic.item_id = $1;
            """, item_id)

            # Materials
            materials = await connection.fetch("""
                SELECT m.name 
                FROM Materials m
                JOIN ItemMaterials im ON im.material_id = m.id
                WHERE im.item_id = $1;
            """, item_id)

            # Season
            seasons = await connection.fetch("""
                SELECT s.name 
                FROM Seasons s
                JOIN ItemSeasons is2 ON is2.season_id = s.id
                WHERE is2.item_id = $1;
            """, item_id)

            # Occasion
            occasions = await connection.fetch("""
                SELECT o.name 
                FROM Occasions o
                JOIN ItemOccasions io ON io.occasion_id = o.id
                WHERE io.item_id = $1;
            """, item_id)

            # Attach them to the result
            item["colors"] = [r["name"] for r in colors]
            item["materials"] = [r["name"] for r in materials]
            item["seasons"] = [r["name"] for r in seasons]
            item["occasions"] = [r["name"] for r in occasions]

            return {"item": item}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.patch("/item/{item_id}")
async def update_item(item_id: str, request: Request):
    pool = request.app.state.db
    data = await request.json()

    print(data)

    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(400, "Missing user_id in request")

    async with pool.acquire() as conn:


        #  Main fields update

        updatable_fields = ["img_description", "category_id", "subcategory"]

        fields_to_update = {
            k: v for k, v in data.items()
            if k in updatable_fields
        }

        if fields_to_update:
            set_clause = ", ".join(
                [f"{k} = ${i+1}" for i, k in enumerate(fields_to_update)]
            )
            await conn.execute(
                f"UPDATE ClothingItems SET {set_clause} WHERE id = '{item_id}'",
                *fields_to_update.values()
            )

        # 2. TAG HANDLING

        if "colors" in data:
            await upsert_tags(conn, "Colors", "ItemColors", "color_id",
                              item_id, user_id, data["colors"])

        if "materials" in data:
            await upsert_tags(conn, "Materials", "ItemMaterials", "material_id",
                              item_id, user_id, data["materials"])

        if "season" in data:
            await upsert_tags(conn, "Seasons", "ItemSeason", "season_id",
                              item_id, user_id, data["season"])

        if "occasion" in data:
            await upsert_tags(conn, "Occasions", "ItemOccasion", "occasion_id",
                              item_id, user_id, data["occasion"])

        return {"status": "updated"}



@app.post("/items")
async def create_item(item: ClothingItemCreate, request: Request):
    pool = request.app.state.db
    body = await request.json()

    try:
        async with pool.acquire() as con:

            item_row = await con.fetchrow(
                """
                INSERT INTO clothingitems (
                    user_id, img_description, image_url, processed_img_url,
                    category_id, subcategory
                )
                VALUES ($1,$2,$3,$4,$5,$6)
                RETURNING id;
                """,
                item.user_id,
                item.img_description,
                item.image_url,
                item.processed_img_url,
                item.category_id,
                item.subcategory,
            )
            item_id = item_row["id"]

            # Helper: insert attribute + link table
            async def upsert_attribute(name, table, link_table, link_column):
                row = await con.fetchrow(
                    f"""
                    INSERT INTO {table} (user_id, name)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id, name)
                    DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                    """,
                    item.user_id,
                    name
                )
                attr_id = row["id"]

                await con.execute(
                    f"""
                    INSERT INTO {link_table} (item_id, {link_column})
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING;
                    """,
                    item_id,
                    attr_id
                )

            # colors
            for color in item.colors:
                await upsert_attribute(color, "Colors", "ItemColors", "color_id")

            #  Materials
            for mat in item.materials:
                await upsert_attribute(mat, "Materials", "ItemMaterials", "material_id")

            # Occasions
            for occ in item.occasion:
                await upsert_attribute(occ, "Occasions", "ItemOccasions", "occasion_id")

            # Seasons 
            for season_name in item.season:
                season_row = await con.fetchrow(
                    "SELECT id FROM Seasons WHERE name = $1",
                    season_name
                )
                if season_row:
                    await con.execute(
                        """
                        INSERT INTO ItemSeasons (item_id, season_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING;
                        """,
                        item_id,
                        season_row["id"],
                    )

            return {"message": "Item created", "item_id": item_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/users")
async def create_user(user: UserCreate, request: Request):
    pool = request.app.state.db
    try:
        async with pool.acquire() as connection:
            sql = """
                INSERT INTO users (id, email)
                VALUES ($1, $2)
                ON CONFLICT (id) DO NOTHING
                RETURNING *;
            """
            row = await connection.fetchrow(sql, user.id, user.email)
            return {"message": "User created", "user": dict(row) if row else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/{user_id}")
async def get_items_by_user(request: Request, user_id: str):
    pool = request.app.state.db
    try:
        async with pool.acquire() as connection:
            if user_id:
                query = "SELECT * FROM clothingItems WHERE user_id = $1;"
                rows = await connection.fetch(query, user_id)
            return {
                "message": "Items fetched successfully",
                "items": [dict(row) for row in rows],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        input_image = Image.open(BytesIO(image_data))
        # preloaded session
        output_image = remove(input_image, session=session)

        buffer = BytesIO()
        output_image.save(buffer, format="PNG")

        processed_base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return {"processed_base64": processed_base64_str}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories")
async def get_categories(request: Request):
    pool = request.app.state.db
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch("SELECT id, name FROM categories ORDER BY id;")
        return {"categories": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subcategories")
async def get_subcategories(user_id: str, category_id: int, query: str = ""):
    rows = await app.state.db.fetch(
        """
        SELECT id, name
        FROM Subcategories
        WHERE user_id = $1
          AND category_id = $2
          AND name ILIKE $3
        ORDER BY name;
        """,
        user_id, category_id, f"%{query}%"
    )
    return {"subcategories": [dict(r) for r in rows]}


@app.post("/subcategories")
async def add_subcategory(user_id: str, category_id: int, name: str):
    row = await app.state.db.fetchrow(
        """
        INSERT INTO Subcategories (user_id, category_id, name)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id, category_id, name)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING id, name, category_id;
        """,
        user_id, category_id, name
    )

    return {"subcategory": dict(row)}


@app.get("/subcategories/{category_id}")
async def get_subcategories(category_id: int, user_id: str):
    rows = await app.state.db.fetch(
        """
        SELECT id, name
        FROM Subcategories
        WHERE category_id = $1 AND user_id = $2
        ORDER BY name;
        """,
        category_id, user_id
    )

    return {"subcategories": [dict(r) for r in rows]}


ATTRIBUTE_TABLES = {
    "colors": ("Colors", "ItemColors"),
    "materials": ("Materials", "ItemMaterials"),
    "occasions": ("Occasions", "ItemOccasions")
}
@app.get("/attributes/{attr_type}")
async def get_attributes(attr_type: str, user_id: str, query: str = ""):
    if attr_type not in ATTRIBUTE_TABLES:
        return {"error": "Invalid attribute type"}

    table, _ = ATTRIBUTE_TABLES[attr_type]

    rows = await app.state.db.fetch(
        f"""
        SELECT id, name
        FROM {table}
        WHERE user_id = $1
          AND name ILIKE $2
        ORDER BY name;
        """,
        user_id, f"%{query}%"
    )

    return {"results": [dict(r) for r in rows]}


@app.post("/attributes/{attr_type}")
async def add_attribute(attr_type: str, user_id: str, name: str):
    if attr_type not in ATTRIBUTE_TABLES:
        return {"error": "Invalid attribute type"}

    table, _ = ATTRIBUTE_TABLES[attr_type]

    row = await app.state.db.fetchrow(
        f"""
        INSERT INTO {table} (user_id, name)
        VALUES ($1, $2)
        ON CONFLICT (user_id, name)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING id, name;
        """,
        user_id, name
    )

    return {"attribute": dict(row)}


@app.post("/ai/classify")
async def ai_classify(image_base64: str):
    # TODO: later replace with real MobileNetV2
    return {"category": None, "subcategory": None, "tags": []}


@app.delete("/item/{item_id}")
async def delete_item(item_id: str, request: Request):
    pool = request.app.state.db
    try:
        async with pool.acquire() as con:
            result = await con.execute(
                "DELETE FROM ClothingItems WHERE id = $1;", item_id
            )
            return {"message": "Item deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
