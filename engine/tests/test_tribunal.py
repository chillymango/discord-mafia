"""
Test the tribunal

Figure out a way to mock out the asyncio sleeps
"""
import asyncio
import mock
import unittest

from engine.game import Game
from engine.tribunal import Tribunal


class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class TestTribunal(unittest.TestCase):
    """
    Yadda
    """

    def setUp(self) -> None:
        self._game = Game()
        self._tribunal = Tribunal(self._game, {})  # test with defaults
