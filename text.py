import asyncio, os, asyncpg
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")

async def test():
    pool = await asyncpg.create_pool(url, ssl="require")
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT NOW()")
        print(row)
    await pool.close()

asyncio.run(test())
