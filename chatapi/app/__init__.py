"""
The app is the way DonBot objects will interface with the Mafia game.

This effectively replaces the Discord interface for them.
"""
import asyncio
import typing as T
from fastapi import FastAPI

if T.TYPE_CHECKING:
    from engine.game import Game

app = FastAPI()


@app.get("/")
async def debug_test():
    return {"message": "Hello World"}
