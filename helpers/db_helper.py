import os
import asyncpg


async def create_db_pool(bot):
    """creates db pool and attach to the bot"""
    bot.db = await asyncpg.create_pool(os.environ.get("DATABASE_URL"))


async def create_guilds_table(bot):
    """attempts to create guilds table"""
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
    """attempts to create players table"""
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
    """attempts to create waitlist table"""
    await bot.db.execute(
        """CREATE TABLE IF NOT EXISTS public.waitlist(
        player_id bigint NOT NULL,
        waiting_id bigint[]
        )"""
    )


async def get_guild_data(bot, guild_id: int):
    """returns data for specified guild"""
    return await bot.db.fetch(
        "select * from guilds where guild_id = $1", guild_id
    )


async def delete_guild_data(bot, guild_id: int):
    """deletes data for specified guild"""
    await bot.db.execute("delete from guilds where guild_id = $1", guild_id)


async def update_guild_data(bot, guild_id: int, **fields):
    """
    updates data for specified guild.
    specify field by using kwargs.
    e.g. key=value
    """
    cols = ("player_id", *fields.keys())
    data = await bot.db.fetch(
        f"select {cols} from guilds where guild_id = $1",
        guild_id,
    )
    if len(data) == 0:
        cols = ", ".join(fields.keys())
        vals = ", ".join([f"${i+2}" for i in range(len(fields))])
        await bot.db.execute(
            f"insert into guilds (guild_id, {cols}) values ($1, {vals})",
            guild_id,
            *fields.values(),
        )
    else:
        list_of_vals = [f"{v} = ${i+2}" for i, v in enumerate(fields.keys())]
        vals = ", ".join(list_of_vals)
        await bot.db.execute(
            f"update guilds set {vals} where guild_id = $1",
            guild_id,
            *fields.values(),
        )
    return "database updated"


async def get_player_data(bot, player_id: int):
    """returns data for specified player"""
    return await bot.db.fetch(
        "select * from players where player_id = $1", player_id
    )


async def delete_player_data(bot, player_id: int):
    """deletes data for specified player"""
    await bot.db.execute("delete from players where player_id = $1", player_id)


async def update_player_data(bot, player_id: int, **fields):
    """
    updates data for specified player.
    specify field by using kwargs.
    e.g. key=value
    """
    cols = ("player_id", *fields.keys())
    data = await bot.db.fetch(
        f"select {cols} from players where player_id = $1",
        player_id,
    )
    if len(data) == 0:
        cols = ", ".join(fields.keys())
        vals = ", ".join([f"${i+2}" for i in range(len(fields))])
        await bot.db.execute(
            f"insert into players (player_id, {cols}) values ($1, {vals})",
            player_id,
            *fields.values(),
        )
    else:
        list_of_vals = [f"{v} = ${i+2}" for i, v in enumerate(fields.keys())]
        vals = ", ".join(list_of_vals)
        await bot.db.execute(
            f"update players set {vals} where player_id = $1",
            player_id,
            *fields.values(),
        )
    return "database updated"


async def get_waitlist_data(bot, player_id: int):
    """returns data for specified waitlisted player"""
    return await bot.db.fetch(
        "select * from waitlist where player_id = $1", player_id
    )


async def delete_waitlist_data(bot, player_id: int):
    """deletes data for specified waitlisted player"""
    await bot.db.execute(
        "delete from waitlist where player_id = $1", player_id
    )


async def update_waitlist_data(bot, player_id: int, waiting_id):
    """
    updates data for specified waitlisted player.
    inserts waiting_id into player_id's row.
    """
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


async def get_players_join_waitlist(bot, player_id: int):
    """
    returns data for specified player.
    left join with waitlist.
    """
    select = "select waitlist.waiting_id"
    left_join = "players left join waitlist"
    on = "on waitlist.player_id = players.player_id"
    where = "where players.player_id = $1"
    return await bot.db.fetch(
        f"{select} from {left_join} {on} {where}",
        player_id,
    )


async def get_waitlist_join_players(bot):
    """
    returns data for waitlisted players.
    inner join with players.
    """
    select = "select * "
    inner_join = "waitlist inner join players"
    on = "on waitlist.player_id = players.player_id"
    return await bot.db.fetch(f"{select} from {inner_join} {on}")
