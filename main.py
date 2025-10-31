from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import connect_to_db, close_db

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