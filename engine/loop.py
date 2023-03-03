"""
Drive state transitions (e.g day to night)
"""
import asyncio
import typing as T

from engine.stepper import advance
from engine.stepper import step

if T.TYPE_CHECKING:
    from engine.component import Component
    from engine.game import Game


class LoopDriver:
    """
    Whenever drive is called, it will start the drive method for all known components.
    """

    def __init__(self, game: "Game", unit_test:bool = False) -> None:
        self._game = game
        self._unit_test = unit_test
        self._components: T.List["Component"] = list()

    def add_component(self, component: "Component") -> None:
        self._components.append(component)

    def remove_component(self, component: "Component") -> None:
        self._components.remove(component)

    async def drive(self) -> None:
        # render all inputs as required?
        await asyncio.gather(*[x.drive() for x in self._components])
