# Helper: UPSERT TAGS (colors, materials, seasons, occasions)
async def upsert_tags(conn, table_name, pivot_table, pivot_field, item_id, user_id, tags):
    """
    Inserts tags (like Colors, Materials, Seasons...) OR returns existing ones.

    Then links the tag to the item via pivot table.
    """
    if not tags:
        return

    for tag in tags:

        # Insert new tag
        tag_id = await conn.fetchval(
            f"""
            INSERT INTO {table_name} (user_id, name)
            VALUES ($1, $2)
            ON CONFLICT(user_id, name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
            """,
            user_id, tag
        )

        # Create relation (item ↔ tag)
        await conn.execute(
            f"""
            INSERT INTO {pivot_table} (item_id, {pivot_field})
            VALUES ($1::uuid, $2)
            ON CONFLICT DO NOTHING;
            """,
            item_id, tag_id
        )