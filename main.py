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
from app.api.subcategory_api import router as subcategory_router
from app.api.outfit_api import router as outfit_router
from app.api.colors_api import router as colors_router
from app.api.materials_api import router as materials_router
from app.api.occasions_api import router as occasions_router
from app.api.outfit_suggestions_api import router as suggestions_router
from app.api.outfit_log_api import router as logged_outfits_router
from app.api.outfit_preference_api import router as preference_router
from app.api.favorites_api import router as favorites_router
from app.api.virtual_try_on_api import router as tryon_router
from app.api.consent_api import router as consent_router
from fastapi.staticfiles import StaticFiles






app = FastAPI()
import os

os.makedirs("generated_tryons", exist_ok=True)
app.mount("/generated_tryons", StaticFiles(directory="generated_tryons"), name="generated_tryons")


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
app.include_router(subcategory_router)
app.include_router(outfit_router)
app.include_router(colors_router)
app.include_router(materials_router)
app.include_router(occasions_router)
app.include_router(suggestions_router)
app.include_router(logged_outfits_router)
app.include_router(preference_router)
app.include_router(favorites_router)
app.include_router(tryon_router)
app.include_router(consent_router)


@app.on_event("shutdown")
async def shutdown():
    await close_db(app.state.db)






















