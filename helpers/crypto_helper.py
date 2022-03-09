import aiohttp


async def price(symbol):
    """get price of coin in USD"""
    """return [content]"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        ) as request:
            if request.status == 200:
                data = await request.json()
                content = "1 {} is {:.2f} USD".format(symbol, float(data["price"]))
            else:
                content = "error getting price"
            return content