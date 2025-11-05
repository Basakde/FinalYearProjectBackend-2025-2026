import base64
import os
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from models import ClothingItemCreate, UserCreate
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

@app.post("/items")
async def create_item(item: ClothingItemCreate,request: Request):
    pool = request.app.state.db
    try:

        async with pool.acquire() as connection:
            query = """
                INSERT INTO clothingitems (
                    user_id, img_description, image_url, processed_img_url, category, subcategory
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *;
            """
            row = await connection.fetchrow(
                query,
                item.user_id,
                item.img_description,
                item.image_url,
                item.processed_img_url,
                item.category,
                item.subcategory,
            )
            return {"message": "Item created successfully", "item": dict(row)}

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
    print("🟢 Fetching items for user:", user_id)
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
        # ✅ Use preloaded session
        output_image = remove(input_image, session=session)

        buffer = BytesIO()
        output_image.save(buffer, format="PNG")

        processed_base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return {"processed_base64": processed_base64_str}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



