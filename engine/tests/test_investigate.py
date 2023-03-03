"""
Why could the vig kill the gf
"""
import typing as T
import unittest
from engine.action.base import Action
from engine.game import Game
from engine.actor import Actor
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import Role
from engine.role.base import RoleFactory

from engine.stepper import advance


class TestInvestigativePowers(unittest.TestCase):
    
    def setUp(self) -> None:
        print("\n---Starting Test---\n")
        self._game = Game()
        # test with defaults i guess
        self._rf = RoleFactory({})
        self._actors = [
            Actor(Player("Albert Yang"), self._rf.create_by_name("Godfather"), self._game),
            Actor(Player("Anthony Chen"), self._rf.create_by_name("Investigator"), self._game),
            Actor(Player("Brandon Chen"), self._rf.create_by_name("Detective"), self._game),
            Actor(Player("Jerry Feng"), self._rf.create_by_name("Lookout"), self._game),
            Actor(Player("Mimi Jiao"), self._rf.create_by_name("Agent"), self._game),
            Actor(Player("William Yuan"), self._rf.create_by_name("Vigilante"), self._game),
            Actor(Player("Kurtis Carsch"), self._rf.create_by_name("Doctor"), self._game),
            Actor(Player("Tyler Port"), self._rf.create_by_name("Escort"), self._game),
            Actor(Player("S.J Guth"), self._rf.create_by_name("Mayor"), self._game),
        ]
        self._game.add_actors(*self._actors)

        # always init to night
        for _ in range(4):
            advance(self._game)
        self.assertEqual(self._game._turn_phase, TurnPhase.NIGHT)

    def _run(self) -> None:
        """
        Run the night sequence (probably)
        """
        for _ in range(2):
            advance(self._game)

    def _add_crime_record(self, actor: "Actor", success: T.Optional[bool] = True) -> None:
        """
        Add the appropriate crime record to an Actor depending on their Role
        """
        for action in actor.role.day_actions + actor.role.night_actions:
            action: "Action" = action
            action.update_crimes(actor, success)

    def test_agent_multi_action(self) -> None:
        agent = self._actors[4]
        det = self._actors[2]
        gf = self._actors[0]

        det.choose_targets(gf)
        gf.choose_targets(det)
        agent.choose_targets(det)

        self._run()

    def tearDown(self) -> None:
        print("\n---Ending Test---\n")
