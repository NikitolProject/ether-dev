import aiohttp
import asyncio


async def test_marketplace_list():
     async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.opensea.io/api/v1/asset/0x18c7766a10df15df8c971f6e8c1d2bba7c7a410b/2519"
        ) as response:
            data = await response.json()
            print(data)


if __name__ == "__main__":
    asyncio.run(test_marketplace_list())
