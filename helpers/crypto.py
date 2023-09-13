"""helper functions for crypto cog"""
import os
from typing import Optional

import aiohttp

from helpers.helpers import DiscordReturn

COINAPI_TOKEN: Optional[str] = os.getenv("CRYPTO_TOKEN")


async def price(sym: str) -> DiscordReturn:
    """get price of requested coin in USD.

    requires COINAPI_TOKEN to be set in .env

    parameters
    ----------
    sym: str
        symbol of coin to get price of

    returns
    -------
    DiscordReturn
        content: str
            price of coin in USD
    """
    async with aiohttp.ClientSession() as session:
        url: str = f"https://rest.coinapi.io/v1/exchangerate/{sym}/USD"
        headers: dict[str, Optional[str]] = {"X-CoinAPI-Key": COINAPI_TOKEN}
        content: str = "error getting price"
        async with session.get(url, headers=headers) as request:
            if request.status == 200:
                data: dict = await request.json()
                content: str = f"1 {sym} = {data.get('rate'):.2f} USD"
        return {
            "content": content,
        }
