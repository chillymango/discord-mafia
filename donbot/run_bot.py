import asyncio
import typing as T


async def main() -> None:
    from donbot import DonBot

    bots = [DonBot() for _ in range(14)]
    await asyncio.gather(*[bot.run() for bot in bots])


if __name__ == "__main__":
    asyncio.run(main())
