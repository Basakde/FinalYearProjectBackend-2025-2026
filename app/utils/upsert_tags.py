# Helper: UPSERT TAGS (colors, materials, seasons, occasions)
from typing import Optional

from app.models.vector_helpers import normalize_label


async def upsert_tags(conn, table_name, pivot_table, pivot_field, mapped_field ,master_table, item_id, user_id, tags):
    """
    Inserts tags (like Colors, Materials, Seasons...) OR returns existing ones.

    Then links the tag to the item via pivot table.
    """
    if not tags:
        return

    for tag in tags:
        original_tag = (tag or "").strip()
        normalized_tag = original_tag.lower()
        if not normalized_tag:
            continue

        mapped_master_id = await get_master_id_by_name(conn, master_table, original_tag)

        # Insert new tag
        tag_id = await conn.fetchval(
            f"""
            INSERT INTO {table_name} (user_id, name, {mapped_field})
            VALUES ($1, $2, $3)
            ON CONFLICT(user_id, name)
            DO UPDATE SET name = EXCLUDED.name,
                {mapped_field} = EXCLUDED.{mapped_field}
            RETURNING id;
            """,
            user_id,
            original_tag,
            mapped_master_id
        )

        # Create relation (item ↔ tag)
        await conn.execute(
            f"""
            INSERT INTO {pivot_table} (item_id, {pivot_field})
            VALUES ($1::uuid, $2)
            ON CONFLICT DO NOTHING;
            """,
            item_id,
            tag_id
        )

async def get_master_id_by_name(conn, master_table: str, raw_name: str) -> Optional[str]:
    """
    Find matching master id by normalized name.
    Falls back to 'other' if exact match does not exist.
    """
    normalized = normalize_label(raw_name)

    row = await conn.fetchrow(
        f"""
        SELECT id
        FROM {master_table}
        WHERE LOWER(name) = $1
        LIMIT 1;
        """,
        normalized
    )
    if row:
        return row["id"]

    other_row = await conn.fetchrow(
        f"""
        SELECT id
        FROM {master_table}
        WHERE LOWER(name) = 'other'
        LIMIT 1;
        """
    )
    return other_row["id"] if other_row else None
