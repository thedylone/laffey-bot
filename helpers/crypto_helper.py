"""helper functions for crypto cog"""

import os
import aiohttp

from helpers.helpers import DiscordReturn

COINAPI_TOKEN: str | None = os.getenv("CRYPTO_TOKEN")


async def price(sym: str) -> DiscordReturn:
    """
    get price of requested coin in USD.
    returns content
    """
    async with aiohttp.ClientSession() as session:
        url: str = f"https://rest.coinapi.io/v1/exchangerate/{sym}/USD"
        headers: dict[str, str | None] = {"X-CoinAPI-Key": COINAPI_TOKEN}
        async with session.get(url, headers=headers) as request:
            if request.status == 200:
                data: dict = await request.json()
                content: str = f"1 {sym} = {data.get('rate'):.2f} USD"
            else:
                content = "error getting price"
            return {
                "content": content,
            }
