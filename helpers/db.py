"""helper functions for database operations"""
from typing import List, Optional

import asyncpg
from asyncpg.pool import Pool


class Database:
    """postgres database to access and store data

    attributes
    ----------
    db: asyncpg.pool.Pool
        database pool
    loaded: bool
        whether database is loaded
    """

    def __init__(self) -> None:
        """initialises the class with loaded set to False"""
        self.db: Pool
        """database pool"""
        self.loaded: bool = False
        """whether database is loaded"""

    async def create_db_pool(self, url: str) -> None:
        """creates a database pool with the given url and assigns it to db.

        parameters
        ----------
        url: str
            url to connect to database
        """
        db: Optional[Pool] = await asyncpg.create_pool(url)
        if db is None:
            raise Exception("Database not initialized")
        self.db = db

    async def create_guilds_table(self) -> str:
        """attempts to create guilds table

        returns
        -------
        str
            output of the query
        """
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
        """attempts to create players table

        returns
        -------
        str
            output of the query
        """
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
            acs double precision[],
            rank text COLLATE pg_catalog."default"
            )"""
        )

    async def create_waitlist_table(self) -> str:
        """attempts to create waitlist table

        returns
        -------
        str
            output of the query
        """
        return await self.db.execute(
            """CREATE TABLE IF NOT EXISTS public.waitlist(
            player_id bigint NOT NULL,
            waiting_id bigint[]
            )"""
        )

    async def load_db(self, url: str) -> None:
        """creates database pool and tables with the given url and sets loaded
        to True

        parameters
        ----------
        url: str
            url to connect to database
        """
        await self.create_db_pool(url)
        await self.create_guilds_table()
        await self.create_players_table()
        await self.create_waitlist_table()
        self.loaded = True

    async def get_guild_data(self, guild_id: int) -> List[asyncpg.Record]:
        """returns data for specified guild from guild_id

        parameters
        ----------
        guild_id: int
            discord id of the guild to get data from

        returns
        -------
        List[asyncpg.Record]
            data for specified guild
        """
        return await self.db.fetch(
            "select * from guilds where guild_id = $1", guild_id
        )

    async def delete_guild_data(self, guild_id: int) -> str:
        """deletes data for specified guild from guild_id

        parameters
        ----------
        guild_id: int
            discord id of the guild to delete data from

        returns
        -------
        str
            output of the query
        """
        return await self.db.execute(
            "delete from guilds where guild_id = $1", guild_id
        )

    async def update_guild_data(self, guild_id: int, **fields) -> str:
        """updates data for specified guild from guild_id. specify fields to
        update by using kwargs. e.g. key=value

        parameters
        ----------
        guild_id: int
            discord id of the guild to update data for
        fields: dict
            fields to update

        returns
        -------
        str
            output of the query
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

    async def get_all_players(self) -> List[asyncpg.Record]:
        """returns all players in database

        returns
        -------
        List[asyncpg.Record]
            all players in database
        """
        return await self.db.fetch("select * from players")

    async def get_players_ids(self) -> List[int]:
        """returns all player ids in database

        returns
        -------
        List[int]
            all player ids in database
        """
        return [
            player.get("player_id")
            for player in await self.db.fetch("select player_id from players")
        ]

    async def get_player_data(self, player_id: int) -> List[asyncpg.Record]:
        """returns data for specified player from player_id

        parameters
        ----------
        player_id: int
            discord id of the player to get data from

        returns
        -------
        List[asyncpg.Record]
            data for specified player
        """
        return await self.db.fetch(
            "select * from players where player_id = $1", player_id
        )

    async def get_player_data_by_puuid(
        self, puuid: str
    ) -> List[asyncpg.Record]:
        """returns data for specified player from puuid

        parameters
        ----------
        puuid: str
            puuid of the player to get data from

        returns
        -------
        List[asyncpg.Record]
            data for specified player
        """
        return await self.db.fetch(
            "select * from players where puuid = $1", puuid
        )

    async def delete_player_data(self, player_id: int) -> str:
        """deletes data for specified player from player_id

        parameters
        ----------
        player_id: int
            discord id of the player to delete data from

        returns
        -------
        str
            output of the query
        """
        return await self.db.execute(
            "delete from players where player_id = $1", player_id
        )

    async def update_player_data(self, player_id: int, **fields) -> str:
        """updates data for specified player from player_id. specify fields to
        update by using kwargs. e.g. key=value

        parameters
        ----------
        player_id: int
            discord id of the player to update data for
        fields: dict
            fields to update
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

    async def get_waitlist_data(self, player_id: int) -> List[asyncpg.Record]:
        """returns data for specified waitlisted player from player_id

        parameters
        ----------
        player_id: int
            discord id of the waitlisted player to get data from

        returns
        -------
        List[asyncpg.Record]
            data for specified waitlisted player
        """
        return await self.db.fetch(
            "select * from waitlist where player_id = $1", player_id
        )

    async def delete_waitlist_data(self, player_id: int) -> str:
        """deletes data for specified waitlisted player from player_id

        parameters
        ----------
        player_id: int
            discord id of the waitlisted player to delete data from

        returns
        -------
        str
            output of the query
        """
        return await self.db.execute(
            "delete from waitlist where player_id = $1", player_id
        )

    async def update_waitlist_data(self, player_id: int, waiting_id) -> str:
        """updates data for specified waitlisted player from player_id and
        inserts waiting_id into player_id's waiting_id array

        parameters
        ----------
        player_id: int
            discord id of the waitlisted player to update data for
        waiting_id: int
            discord id of the player to add to the waitlist

        returns
        -------
        str
            output of the query
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

    async def get_players_join_waitlist(
        self, player_id: int
    ) -> List[asyncpg.Record]:
        """returns data for specified player from player_id and
        waitlist data for the player

        parameters
        ----------
        player_id: int
            discord id of the player to get data from

        returns
        -------
        List[asyncpg.Record]
            data for specified player and waitlist data for the player
        """
        select = "select waitlist.waiting_id"
        left_join = "players left join waitlist"
        on_str = "on waitlist.player_id = players.player_id"
        where = "where players.player_id = $1"
        return await self.db.fetch(
            f"{select} from {left_join} {on_str} {where}",
            player_id,
        )

    async def get_waitlist_join_players(self) -> List[asyncpg.Record]:
        """returns waitlist data for all players in waitlist and
        player data for each player

        returns
        -------
        List[asyncpg.Record]
            waitlist data for all players in waitlist and
            player data for each player
        """
        select = "select * "
        inner_join = "waitlist inner join players"
        on_str = "on waitlist.player_id = players.player_id"
        return await self.db.fetch(f"{select} from {inner_join} {on_str}")


db = Database()
