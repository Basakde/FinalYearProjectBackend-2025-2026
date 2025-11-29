import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

import asyncpg

async def connect_to_db():
    # Supabase requires SSL
    return await asyncpg.create_pool(DATABASE_URL, ssl="require")


async def close_db(pool):
    await pool.close()
