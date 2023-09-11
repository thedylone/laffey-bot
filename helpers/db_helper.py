"""helper functions for database operations"""

from typing import List, Optional
import asyncpg
from asyncpg.pool import Pool


class Database:
    """database class"""

    def __init__(self) -> None:
        self.db: Pool
        self.loaded: bool = False

    async def create_db_pool(self, url: str) -> None:
        """creates db pool and attach to self"""
        db: Optional[Pool] = await asyncpg.create_pool(url)
        if db is None:
            raise Exception("Database not initialized")
        self.db = db
        self.loaded = True

    async def create_guilds_table(self) -> str:
        """attempts to create guilds table"""
        return await self.db.execute(
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

    async def create_players_table(self) -> str:
        """attempts to create players table"""
        return await self.db.execute(
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

    async def create_waitlist_table(self) -> str:
        """attempts to create waitlist table"""
        return await self.db.execute(
            """CREATE TABLE IF NOT EXISTS public.waitlist(
            player_id bigint NOT NULL,
            waiting_id bigint[]
            )"""
        )

    async def get_guild_data(self, guild_id: int) -> List:
        """returns data for specified guild"""
        return await self.db.fetch(
            "select * from guilds where guild_id = $1", guild_id
        )

    async def delete_guild_data(self, guild_id: int) -> None:
        """deletes data for specified guild"""
        await self.db.execute(
            "delete from guilds where guild_id = $1", guild_id
        )

    async def update_guild_data(self, guild_id: int, **fields) -> str:
        """
        updates data for specified guild.
        specify field by using kwargs.
        e.g. key=value
        """
        _cols: tuple = ("player_id", *fields.keys())
        # check if guild exists
        data: List = await self.db.fetch(
            f"select {_cols} from guilds where guild_id = $1",
            guild_id,
        )
        if len(data) == 0:
            # if guild does not exist, insert
            cols: str = ", ".join(fields.keys())
            vals: str = ", ".join([f"${i+2}" for i in range(len(fields))])
            out: str = await self.db.execute(
                f"insert into guilds (guild_id, {cols}) values ($1, {vals})",
                guild_id,
                *fields.values(),
            )
        else:
            # if guild exists, update
            list_of_vals: List[str] = [
                f"{v} = ${i+2}" for i, v in enumerate(fields.keys())
            ]
            vals = ", ".join(list_of_vals)
            out: str = await self.db.execute(
                f"update guilds set {vals} where guild_id = $1",
                guild_id,
                *fields.values(),
            )
        return out

    async def get_all_players(self) -> List:
        """returns all players"""
        return await self.db.fetch("select * from players")

    async def get_players_ids(self) -> List[int]:
        """returns all player ids"""
        return [
            player.get("player_id")
            for player in await self.db.fetch("select player_id from players")
        ]

    async def get_player_data(self, player_id: int) -> List:
        """returns data for specified player from player_id"""
        return await self.db.fetch(
            "select * from players where player_id = $1", player_id
        )

    async def get_player_data_by_puuid(self, puuid: str) -> list:
        """returns data for specified player from puuid"""
        return await self.db.fetch(
            "select * from players where puuid = $1", puuid
        )

    async def delete_player_data(self, player_id: int) -> None:
        """deletes data for specified player"""
        await self.db.execute(
            "delete from players where player_id = $1", player_id
        )

    async def update_player_data(self, player_id: int, **fields) -> str:
        """
        updates data for specified player.
        specify field by using kwargs.
        e.g. key=value
        """
        _cols: tuple = ("player_id", *fields.keys())
        data: list = await self.db.fetch(
            f"select {_cols} from players where player_id = $1",
            player_id,
        )
        if len(data) == 0:
            cols: str = ", ".join(fields.keys())
            vals: str = ", ".join([f"${i+2}" for i in range(len(fields))])
            out: str = await self.db.execute(
                f"insert into players (player_id, {cols}) values ($1, {vals})",
                player_id,
                *fields.values(),
            )
        else:
            list_of_vals: list[str] = [
                f"{v} = ${i+2}" for i, v in enumerate(fields.keys())
            ]
            vals = ", ".join(list_of_vals)
            out: str = await self.db.execute(
                f"update players set {vals} where player_id = $1",
                player_id,
                *fields.values(),
            )
        return out

    async def get_waitlist_data(self, player_id: int) -> list:
        """returns data for specified waitlisted player"""
        return await self.db.fetch(
            "select * from waitlist where player_id = $1", player_id
        )

    async def delete_waitlist_data(self, player_id: int) -> None:
        """deletes data for specified waitlisted player"""
        await self.db.execute(
            "delete from waitlist where player_id = $1", player_id
        )

    async def update_waitlist_data(self, player_id: int, waiting_id) -> str:
        """
        updates data for specified waitlisted player.
        inserts waiting_id into player_id's row.
        """
        data: list = await self.db.fetch(
            "select waiting_id from waitlist where player_id = $1", player_id
        )
        if len(data) == 0:
            out: str = await self.db.execute(
                "insert into waitlist (player_id, waiting_id) values ($1, $2)",
                player_id,
                waiting_id,
            )
        else:
            out: str = await self.db.execute(
                "update waitlist set waiting_id = $2 where player_id = $1",
                player_id,
                waiting_id,
            )
        return out

    async def get_players_join_waitlist(self, player_id: int) -> list:
        """
        returns data for specified player.
        left join with waitlist.
        """
        select = "select waitlist.waiting_id"
        left_join = "players left join waitlist"
        on_str = "on waitlist.player_id = players.player_id"
        where = "where players.player_id = $1"
        return await self.db.fetch(
            f"{select} from {left_join} {on_str} {where}",
            player_id,
        )

    async def get_waitlist_join_players(self) -> list:
        """
        returns data for waitlisted players.
        inner join with players.
        """
        select = "select * "
        inner_join = "waitlist inner join players"
        on_str = "on waitlist.player_id = players.player_id"
        return await self.db.fetch(f"{select} from {inner_join} {on_str}")


db = Database()
