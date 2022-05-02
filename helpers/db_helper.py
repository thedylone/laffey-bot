import os
import asyncpg


async def create_db_pool(bot):
    bot.db = await asyncpg.create_pool(os.environ["DATABASE_URL"])


async def create_guilds_table(bot):
    await bot.db.execute(
        """CREATE TABLE IF NOT EXISTS public.guilds(
        guild_id bigint NOT NULL,
        prefix text COLLATE pg_catalog."default",
        watch_channel bigint,
        ping_role bigint,
        ping_image text COLLATE pg_catalog."default",
        feeder_messages text[] COLLATE pg_catalog."default",
        feeder_images text[] COLLATE pg_catalog."default",
        streaker_messages text[] COLLATE pg_catalog."default"
        )"""
    )


async def create_players_table(bot):
    await bot.db.execute(
        """CREATE TABLE IF NOT EXISTS public.players(
        player_id bigint NOT NULL,
        guild_id bigint,
        name text COLLATE pg_catalog."default",
        tag text COLLATE pg_catalog."default",
        region text COLLATE pg_catalog."default",
        puuid text COLLATE pg_catalog."default",
        lastTime double precision,
        streak integer,
        headshots integer[],
        bodyshots integer[],
        legshots integer[],
        acs double precision[]
        )"""
    )


async def create_waitlist_table(bot):
    await bot.db.execute(
        """CREATE TABLE IF NOT EXISTS public.waitlist(
        player_id bigint NOT NULL,
        waiting_id bigint[]
        )"""
    )


async def get_guild_data(bot, guild_id: int):
    return await bot.db.fetch("select * from guilds where guild_id = $1", guild_id)


async def delete_guild_data(bot, guild_id: int):
    await bot.db.execute("delete from guilds where guild_id = $1", guild_id)


async def update_guild_data(bot, guild_id: int, **fields):
    data = await bot.db.fetch(
        f"select {('player_id', *fields.keys())} from guilds where guild_id = $1",
        guild_id,
    )
    if len(data) == 0:
        await bot.db.execute(
            f"insert into guilds (guild_id, {', '.join(fields.keys())}) values ($1, {', '.join(['$'+str(i+2) for i in range(len(fields))])})",
            guild_id,
            *fields.values(),
        )
    else:
        await bot.db.execute(
            f"update guilds set {', '.join([v + ' = $'+str(i+2) for i, v in enumerate(fields.keys())])} where guild_id = $1",
            guild_id,
            *fields.values(),
        )
    return "database updated"


async def get_player_data(bot, player_id: int):
    return await bot.db.fetch("select * from players where player_id = $1", player_id)


async def delete_player_data(bot, player_id: int):
    await bot.db.execute("delete from players where player_id = $1", player_id)


async def update_player_data(bot, player_id: int, **fields):
    data = await bot.db.fetch(
        f"select {('player_id', *fields.keys())} from players where player_id = $1",
        player_id,
    )
    if len(data) == 0:
        await bot.db.execute(
            f"insert into players (player_id, {', '.join(fields.keys())}) values ($1, {', '.join(['$'+str(i+2) for i in range(len(fields))])})",
            player_id,
            *fields.values(),
        )
    else:
        await bot.db.execute(
            f"update players set {', '.join([v + ' = $'+str(i+2) for i, v in enumerate(fields.keys())])} where player_id = $1",
            player_id,
            *fields.values(),
        )
    return "database updated"


async def get_waitlist_data(bot, player_id: int):
    return await bot.db.fetch("select * from waitlist where player_id = $1", player_id)


async def delete_waitlist_data(bot, player_id: int):
    await bot.db.execute("delete from waitlist where player_id = $1", player_id)


async def update_waitlist_data(bot, player_id: int, waiting_id):
    data = await bot.db.fetch(
        "select waiting_id from waitlist where player_id = $1", player_id
    )
    if len(data) == 0:
        await bot.db.execute(
            "insert into waitlist (player_id, waiting_id) values ($1, $2)",
            player_id,
            waiting_id,
        )
    else:
        await bot.db.execute(
            "update waitlist set waiting_id = $2 where player_id = $1",
            player_id,
            waiting_id,
        )
    return "waitlist updated"
