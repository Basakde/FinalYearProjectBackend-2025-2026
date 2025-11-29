import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from app.db.connection import connect_to_db, close_db
from rembg import  new_session
from app.api.user_api import router as user_router
from app.api.item_api import router as item_router
from app.api.bg_api import router as bg_router
from app.api.category_api import router as category_router
from app.api.weather_api import router as weather_router


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


@app.on_event("startup")
async def startup():
    app.state.db = await connect_to_db()
    app.state.bg_session = new_session("u2net") #Loads the expensive bg removal model once


# Mount routers
app.include_router(user_router)
app.include_router(item_router)
app.include_router(bg_router)
app.include_router(category_router)
app.include_router(weather_router)

@app.on_event("shutdown")
async def shutdown():
    await close_db(app.state.db)






















