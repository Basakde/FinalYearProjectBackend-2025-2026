from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from models import ClothingItemCreate, UserCreate
from db import connect_to_db, close_db, DATABASE_URL

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
