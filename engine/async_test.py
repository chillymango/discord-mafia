import asyncio

async def test1() -> None:
    await asyncio.sleep(1.)
    print(1)


async def test2() -> None:
    await asyncio.sleep(2.)
    print(2)


async def test3() -> None:
    await asyncio.sleep(3.)
    print(3)


async def corotest() -> None:
    task1 = asyncio.create_task(test1())
    task2 = asyncio.create_task(test2())
    task3 = asyncio.create_task(test3())
    await task1
    await task2
    await task3


if __name__ == "__main__":
    asyncio.run(corotest())
