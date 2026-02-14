# app/services/colors_service.py
from typing import Any, Dict, List
from fastapi import HTTPException
from app.utils.normalize import normalize_label, display_label

# Table name is "Colors" in your schema (capital C)
# Columns: id, user_id, name, mapped_color_id (optional), is_active (you added)

async def list_user_colors_service(pool, user_id: str, active_only: bool):
    async with pool.acquire() as conn:
        if active_only:
            rows = await conn.fetch(
                """
                select id::text, name, is_active, mapped_color_id::text
                from Colors
                where user_id = $1 and is_active = true
                order by lower(name) asc
                """,
                user_id,
            )
        else:
            rows = await conn.fetch(
                """
                select id::text, name, is_active, mapped_color_id::text
                from Colors
                where user_id = $1
                order by is_active desc, lower(name) asc
                """,
                user_id,
            )
        return [dict(r) for r in rows]



async def create_user_color_service(pool, user_id: str, name: str) -> Dict[str, Any]:
    clean = name.strip()
    async with pool.acquire() as conn:
        # Optional: auto-map if name exists in colors_master
        # If you don't want auto-map now, remove mapped lookup block.
        mapped = await conn.fetchval(
            """
            select id
            from colors_master
            where lower(name) = lower($1)
            limit 1
            """,
            clean,
        )

        row = await conn.fetchrow(
            """
            insert into Colors(user_id, name, mapped_color_id, is_active)
            values ($1, $2, $3, true)
            on conflict (user_id, name) do update
              set is_active = true
            returning id::text, name, is_active, mapped_color_id::text
            """,
            user_id,
            clean,
            mapped,
        )
        return dict(row)


async def rename_user_color_service(pool, color_id: str, name: str) -> bool:
    clean = name.strip()
    async with pool.acquire() as conn:
        mapped = await conn.fetchval(
            """
            select id
            from colors_master
            where lower(name) = lower($1)
            limit 1
            """,
            clean,
        )

        result = await conn.execute(
            """
            update Colors
            set name = $2,
                mapped_color_id = $3
            where id = $1
            """,
            color_id,
            clean,
            mapped,
        )
        # asyncpg returns strings like "UPDATE 1"
        return result.endswith("1")


async def set_user_color_active_service(pool, color_id: str, is_active: bool) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            update Colors
            set is_active = $2
            where id = $1
            """,
            color_id,
            is_active,
        )
        return result.endswith("1")


async def delete_user_color_service(pool, color_id: str, user_id: str):
    async with pool.acquire() as conn:

        # 1️⃣ Make sure this color belongs to the user
        owner = await conn.fetchval(
            """
            select user_id
            from "Colors"
            where id = $1
            """,
            color_id,
        )

        if owner is None:
            return False  # not found

        if str(owner) != str(user_id):
            raise PermissionError("Not allowed to delete this color")

        # 2️⃣ Check if color is used by any item
        used = await conn.fetchval(
            """
            select 1
            from "ItemColors"
            where color_id = $1
            limit 1
            """,
            color_id,
        )

        if used:
            raise ValueError("Color is used by items. Disable it instead.")

        # 3️⃣ Safe to delete
        result = await conn.execute(
            """
            delete from "Colors"
            where id = $1
            """,
            color_id,
        )

        return result.endswith("1")



async def get_color_options_service(pool, user_id: str, active_only: bool = True):
    """
    Returns merged list of color options: master (colors_meta) + user (Colors),
    de-duplicated by normalized name, display formatted, alphabetically sorted.
    """
    try:
        async with pool.acquire() as conn:

            # 1) Fetch master colors
            master_sql = """
                SELECT id::text AS id, name
                FROM colors_master
            """
            if active_only:
                master_sql += " WHERE is_active = true"
            master_rows = await conn.fetch(master_sql)

            # 2) Fetch user colors
            user_sql = """
                SELECT c.id::text AS id, c.name, cm.id::text AS mapped_to_id, cm.name AS mapped_to_name
                FROM Colors c
                LEFT JOIN colors_master cm ON cm.id = c.mapped_color_id
                WHERE c.user_id = $1
            """
            if active_only:
                user_sql += " AND c.is_active = true"
            user_rows = await conn.fetch(user_sql, user_id)

            # 3) Merge + dedupe (case/space insensitive)
            merged = {}
            # Add masters first (so master wins if same name exists)
            for r in master_rows:
                name_raw = r["name"]
                key = normalize_label(name_raw)
                merged[key] = {
                    "id": r["id"],
                    "name": display_label(name_raw),
                    "source": "master",
                    "mapped_to": None
                }

            # Add user colors if they don't duplicate a master name
            for r in user_rows:
                name_raw = r["name"]
                key = normalize_label(name_raw)

                if key in merged:
                    # Duplicate of a master (e.g. "Blue" vs "blue") -> ignore user version
                    continue

                mapped_to = None
                if r["mapped_to_id"] and r["mapped_to_name"]:
                    mapped_to = {
                        "id": r["mapped_to_id"],
                        "name": display_label(r["mapped_to_name"]),
                    }

                merged[key] = {
                    "id": r["id"],
                    "name": display_label(name_raw),
                    "source": "user",
                    "mapped_to": mapped_to
                }

            # 4) Sort alphabetically by display name
            options = list(merged.values())
            options.sort(key=lambda x: x["name"].lower())

            return options

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
