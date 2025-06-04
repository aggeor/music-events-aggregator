import asyncio

from crawler.crawler import iereies

async def main():
    await iereies()

if __name__ == "__main__":
    asyncio.run(main())