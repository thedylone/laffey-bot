import os
import asyncpg


async def create_db_pool(bot):
    bot.db = await asyncpg.create_pool(os.environ["DATABASE_URL"])


async def get_guild_data(bot, guild_id):
    return await bot.db.fetch("select * from guilds where guild_id = $1", guild_id)


async def delete_guild_data(bot, guild_id):
    await bot.db.execute("delete from guilds where guild_id = $1", guild_id)


async def update_guild_data(bot, guild_id: int, column, value):
    data = await bot.db.fetch(
        f"select {column} from guilds where guild_id = $1", guild_id
    )
    if len(data) == 0:
        await bot.db.execute(
            f"insert into guilds (guild_id, {column}) values ($1, $2)",
            guild_id,
            value,
        )
    else:
        await bot.db.execute(
            f"update guilds set {column} = $1 where guild_id = $2", value, guild_id
        )
    return "database updated"
