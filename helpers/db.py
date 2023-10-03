"""helper functions for database operations"""
from typing import List, Optional, TypedDict

from asyncpg import create_pool
from asyncpg.pool import Pool


class GuildData(TypedDict):
    """schema for guilds table

    attributes
    ----------
    guild_id: int
        discord id of the guild
    prefix: str
        prefix for the guild
    watch_channel: Optional[int]
        discord id of the channel to send alerts
    ping_role: Optional[int]
        discord id of the role to ping
    ping_image: Optional[str]
        url of custom image to send with ping
    feeder_messages: Optional[List[str]]
        list of messages to send when a feeder is detected
    feeder_images: Optional[List[str]]
        list of images to send when a feeder is detected
    streaker_messages: Optional[List[str]]
        list of messages to send when a streaker is detected
    """

    guild_id: int
    """discord id of the guild"""
    prefix: str
    """prefix for the guild"""
    watch_channel: Optional[int]
    """discord id of the channel to send alerts"""
    ping_role: Optional[int]
    """discord id of the role to ping"""
    ping_image: Optional[str]
    """url of custom image to send with ping"""
    feeder_messages: Optional[List[str]]
    """list of messages to send when a feeder is detected"""
    feeder_images: Optional[List[str]]
    """list of images to send when a feeder is detected"""
    streaker_messages: Optional[List[str]]
    """list of messages to send when a streaker is detected"""


class PlayerData(TypedDict):
    """schema for players table

    attributes
    ----------
    player_id: int
        discord id of the player
    guild_id: Optional[int]
        discord id of the guild the player is in
    name: Optional[str]
        valorant name of the player
    tag: Optional[str]
        valorant tag of the player
    region: Optional[str]
        valorant region of the player
    puuid: Optional[str]
        valorant puuid of the player
    lastTime: Optional[float]
        last time the player played a game
    streak: Optional[int]
        current streak of the player
    headshots: Optional[List[int]]
        list of headshots for the player per game
    bodyshots: Optional[List[int]]
        list of bodyshots for the player per game
    legshots: Optional[List[int]]
        list of legshots for the player per game
    acs: Optional[List[float]]
        list of acs for the player per game
    rank: Optional[str]
        valorant rank of the player
    """

    player_id: int
    """discord id of the player"""
    guild_id: Optional[int]
    """discord id of the guild the player is in"""
    name: Optional[str]
    """valorant name of the player"""
    tag: Optional[str]
    """valorant tag of the player"""
    region: Optional[str]
    """valorant region of the player"""
    puuid: Optional[str]
    """valorant puuid of the player"""
    lastTime: Optional[float]
    """last time the player played a game"""
    streak: Optional[int]
    """current streak of the player"""
    headshots: Optional[List[int]]
    """list of headshots for the player per game"""
    bodyshots: Optional[List[int]]
    """list of bodyshots for the player per game"""
    legshots: Optional[List[int]]
    """list of legshots for the player per game"""
    acs: Optional[List[float]]
    """list of acs for the player per game"""
    rank: Optional[str]
    """valorant rank of the player"""


class WaitlistData(TypedDict):
    """schema for waitlist table

    attributes
    ----------
    player_id: int
        discord id of the player who is being waited for
    waiting_id: Optional[List[int]]
        list of discord ids of players who are waiting for the player
    """

    player_id: int
    """discord id of the player who is being waited for"""
    waiting_id: Optional[List[int]]
    """list of discord ids of players who are waiting for the player"""


class PlayerWaitlistData(PlayerData, WaitlistData):
    """schema for join waitlist query

    attributes
    ----------
    player_id: int
        discord id of the player
    guild_id: Optional[int]
        discord id of the guild the player is in
    name: Optional[str]
        valorant name of the player
    tag: Optional[str]
        valorant tag of the player
    region: Optional[str]
        valorant region of the player
    puuid: Optional[str]
        valorant puuid of the player
    lastTime: Optional[float]
        last time the player played a game
    streak: Optional[int]
        current streak of the player
    headshots: Optional[List[int]]
        list of headshots for the player per game
    bodyshots: Optional[List[int]]
        list of bodyshots for the player per game
    legshots: Optional[List[int]]
        list of legshots for the player per game
    acs: Optional[List[float]]
        list of acs for the player per game
    rank: Optional[str]
        valorant rank of the player
    waiting_id: Optional[List[int]]
        list of discord ids of players who are waiting for the player
    """


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
        self.database: Pool
        """database pool"""
        self.loaded: bool = False
        """whether database is loaded"""

    async def create_db_pool(self, url: str) -> None:
        """creates a database pool with the given url and assigns it to db.

        parameters
        ----------
        url: str
            url to connect to database

        raises
        ------
        ConnectionError
            if database could not be connected to
        """
        _db: Optional[Pool] = await create_pool(url)
        if _db is None:
            raise ConnectionError("could not connect to database")
        self.database = _db

    async def create_guilds_table(self) -> str:
        """attempts to create guilds table

        returns
        -------
        str
            output of the query
        """
        return await self.database.execute(
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
        return await self.database.execute(
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
        return await self.database.execute(
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

        raises
        ------
        ConnectionError
            if database could not be connected to
        """
        await self.create_db_pool(url)
        await self.create_guilds_table()
        await self.create_players_table()
        await self.create_waitlist_table()
        self.loaded = True

    async def get_guild_data(self, guild_id: int) -> List[GuildData]:
        """returns data for specified guild from guild_id

        parameters
        ----------
        guild_id: int
            discord id of the guild to get data from

        returns
        -------
        List[GuildData]
            data for specified guild
        """
        return await self.database.fetch(
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
        return await self.database.execute(
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
        # check if guild exists in database
        data: List[GuildData] = await self.get_guild_data(guild_id)
        if len(data) == 0:
            # if guild does not exist, insert
            cols: str = ", ".join(fields.keys())
            vals: str = ", ".join([f"${i+2}" for i in range(len(fields))])
            out: str = await self.database.execute(
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
            out: str = await self.database.execute(
                f"update guilds set {vals} where guild_id = $1",
                guild_id,
                *fields.values(),
            )
        return out

    async def get_all_players(self) -> List[PlayerData]:
        """returns all players in database

        returns
        -------
        List[PlayerData]
            all players in database
        """
        return await self.database.fetch("select * from players")

    async def get_players_ids(self) -> List[int]:
        """returns all player ids in database

        returns
        -------
        List[int]
            all player ids in database
        """
        players: List[PlayerData] = await self.database.fetch(
            "select player_id from players"
        )
        return [player["player_id"] for player in players]

    async def get_player_data(self, player_id: int) -> List[PlayerData]:
        """returns data for specified player from player_id

        parameters
        ----------
        player_id: int
            discord id of the player to get data from

        returns
        -------
        List[PlayerData]
            data for specified player
        """
        return await self.database.fetch(
            "select * from players where player_id = $1", player_id
        )

    async def get_player_data_by_puuid(self, puuid: str) -> List[PlayerData]:
        """returns data for specified player from puuid

        parameters
        ----------
        puuid: str
            puuid of the player to get data from

        returns
        -------
        List[PlayerData]
            data for specified player
        """
        return await self.database.fetch(
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
        return await self.database.execute(
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
        data: List[PlayerData] = await self.get_player_data(player_id)
        if len(data) == 0:
            cols: str = ", ".join(fields.keys())
            vals: str = ", ".join([f"${i+2}" for i in range(len(fields))])
            out: str = await self.database.execute(
                f"insert into players (player_id, {cols}) values ($1, {vals})",
                player_id,
                *fields.values(),
            )
        else:
            list_of_vals: list[str] = [
                f"{v} = ${i+2}" for i, v in enumerate(fields.keys())
            ]
            vals = ", ".join(list_of_vals)
            out: str = await self.database.execute(
                f"update players set {vals} where player_id = $1",
                player_id,
                *fields.values(),
            )
        return out

    async def get_waitlist_data(self, player_id: int) -> List[WaitlistData]:
        """returns data for specified waitlisted player from player_id

        parameters
        ----------
        player_id: int
            discord id of the waitlisted player to get data from

        returns
        -------
        List[WaitlistData]
            data for specified waitlisted player
        """
        return await self.database.fetch(
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
        return await self.database.execute(
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
        data: List[WaitlistData] = await self.database.fetch(
            "select * from waitlist where player_id = $1", player_id
        )
        if len(data) == 0:
            out: str = await self.database.execute(
                "insert into waitlist (player_id, waiting_id) values ($1, $2)",
                player_id,
                waiting_id,
            )
        else:
            out: str = await self.database.execute(
                "update waitlist set waiting_id = $2 where player_id = $1",
                player_id,
                waiting_id,
            )
        return out

    async def get_player_join_waiters(
        self, player_id: int
    ) -> List[PlayerWaitlistData]:
        """returns data for specified player from player_id and
        waitlist data for the player

        parameters
        ----------
        player_id: int
            discord id of the player to get data from

        returns
        -------
        List[PlayerWaitlistData]
            data for specified player and waitlist data for the player
        """
        left_join = "players left join waitlist"
        on_str = "on waitlist.player_id = players.player_id"
        where = "where players.player_id = $1"
        return await self.database.fetch(
            f"select * from {left_join} {on_str} {where}",
            player_id,
        )

    async def get_waiteds_join_player(self) -> List[PlayerWaitlistData]:
        """returns waitlist data for all players in waitlist and
        player data for each player

        returns
        -------
        List[PlayerWaitlistData]
            waitlist data for all players in waitlist and
            player data for each player
        """
        inner_join = "waitlist inner join players"
        on_str = "on waitlist.player_id = players.player_id"
        return await self.database.fetch(
            f"select * from {inner_join} {on_str}"
        )


db = Database()
