import os
import asyncpg


async def create_db_pool(bot):
    bot.db = await asyncpg.create_pool(os.environ['DATABASE_URL'])

async def get_guild_data(bot, guild_id):
    return (await bot.db.fetch('select * from guilds where guild_id = $1', guild_id))

async def update_guild_prefix(bot, guild_id: int, value):
    data = await bot.db.fetch('select prefix from guilds where guild_id = $1', guild_id)
    if len(data) == 0:
        await bot.db.execute("insert into guilds (guild_id, prefix) values ($1, $2)", guild_id, value)
    else:
        await bot.db.execute("update guilds set prefix = $1 where guild_id = $2", value, guild_id)
    return "database updated"
