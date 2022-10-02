import aiohttp


async def price(symbol):
    """
    get price of requested coin in USD.
    returns content
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        ) as request:
            if request.status == 200:
                data = await request.json()
                content = "1 {} is {:.2f} USD".format(
                    symbol, float(data.get("price"))
                )
            else:
                content = "error getting price"
            return content
