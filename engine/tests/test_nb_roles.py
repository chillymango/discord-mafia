"""
Test Neutral Benign Roles
* Executioner
* Jester
* Survivor
* Amnesiac
* Lover
"""
import mock
import random
import typing as T
import unittest

from engine.game import Game
from engine.actor import Actor
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.role.neutral.executioner import Executioner
from engine.role.neutral.jester import Jester
from engine.setup import GameConfig
from engine.tribunal import Tribunal

from engine.setup import do_setup
from engine.stepper import sleep_override
from engine.stepper import Stepper
from engine.wincon import ExecutionerWin
from engine.wincon import JesterWin
from engine.wincon import WinCondition


class TestNeutralBenignRoles(unittest.TestCase):

    def setUp(self) -> None:
        print("\n---Starting Test---\n")
        role_list = [
            "SerialKiller",
            "MassMurderer",
            "Executioner",
            "Jester",
            "Survivor",
            "Godfather",
            "Janitor",
            "Kidnapper",
            "Mayor",
            "Bodyguard",
            "Investigator",
            "Jailor",
            "Detective",
            "Lookout",
            "Doctor",
        ]
        config = GameConfig.default_with_role_list(role_list)
        self._game = Game(config)
        self._game.messenger = mock.MagicMock()
        self._tribunal = Tribunal(self._game)
        self._game.tribunal = self._tribunal
        self._stepper = Stepper(self._game, sleep_override)
        # test with defaults i guess
        self._rf = RoleFactory(config)
        players = [Player(str(random.randint(1000, 10000))) for p in range(15)]
        self._game.add_players(*players)
        success, msg = do_setup(self._game, config=config)
        self.assertTrue(success, msg)

        # always init to night
        for _ in range(4):
            self._stepper.advance(self._game)
        self.assertEqual(self._game._turn_phase, TurnPhase.NIGHT)

    def _evaluate_win(self) -> T.Tuple[T.Set[WinCondition], T.List[Actor]]:
        winners = self._game.evaluate_post_game()
        wcs = set([winner.role.win_condition() for winner in winners])
        return (wcs, winners)

    def step_to_next(self, phase: TurnPhase) -> None:
        # step at least 1
        self._stepper.advance(self._game)
        while self._game.turn_phase != phase:
            self._stepper.advance(self._game)

    def test_executioner_loses_if_target_alive(self) -> None:
        # step to next daylight, evaluate win, make sure executioner loses
        self.step_to_next(TurnPhase.DAYLIGHT)
        wcs, winners = self._evaluate_win()
        self.assertNotIn(ExecutionerWin, wcs)

    def test_executioner_wins_if_target_lynched(self) -> None:
        self.step_to_next(TurnPhase.DAYLIGHT)
        exec = self._game.get_live_actors_by_role(Executioner)[0]
        target: Actor = exec.role.executioner_target
        target.lynch()
        self._game.death_reporter.report_death(target)

        wcs, winners = self._evaluate_win()
        self.assertIn(ExecutionerWin, wcs)

    def test_executioner_wins_if_target_lynched_and_exec_dies_after(self) -> None:
        self.step_to_next(TurnPhase.DAYLIGHT)
        exec = self._game.get_live_actors_by_role(Executioner)[0]
        target: Actor = exec.role.executioner_target
        target.lynch()
        self._game.death_reporter.report_death(target)
        self.step_to_next(TurnPhase.NIGHT_SEQUENCE)
        exec = self._game.get_live_actors_by_role(Executioner)[0]
        exec.kill()
        self._game.death_reporter.report_death(target)

        wcs, winners = self._evaluate_win()
        self.assertIn(ExecutionerWin, wcs)

    def test_executioner_loses_if_target_lynched_after_exec_dies(self) -> None:
        """
        My only wish was that my target would reach the grave before I did.
        While I am doubtlessly disappointed that this apparently did not happen,
        nevertheless I curse and besmirch him.
        """
        self.step_to_next(TurnPhase.DAYLIGHT)
        exec = self._game.get_live_actors_by_role(Executioner)[0]
        target: Actor = exec.role.executioner_target
        exec.kill()
        self._game.death_reporter.report_death(exec)
        self.step_to_next(TurnPhase.DAYLIGHT)
        target.kill()
        self._game.death_reporter.report_death(target)

        wcs, winners = self._evaluate_win()
        self.assertNotIn(ExecutionerWin, wcs)

    def test_executioner_loses_if_target_dies_not_lynched(self) -> None:
        self.step_to_next(TurnPhase.DAYLIGHT)
        exec = self._game.get_live_actors_by_role(Executioner)[0]
        target: Actor = exec.role.executioner_target

        target.kill()
        self._game.death_reporter.report_death(target)

        wcs, winners = self._evaluate_win()
        self.assertNotIn(ExecutionerWin, wcs)

    def test_executioner_target_dies_causes_jester_convert(self) -> None:
        """
        If the Executioner's target dies, the Executioner should switch
        into a Jester.
        """
        self.step_to_next(TurnPhase.DAYLIGHT)
        exec = self._game.get_live_actors_by_role(Executioner)[0]
        target: Actor = exec.role.executioner_target

        # e.g by constable or something
        target.kill()
        self._game.death_reporter.report_death(target)

        self.step_to_next(TurnPhase.NIGHT_SEQUENCE)
        self.assertEqual(exec.role.name, "Jester")

    def test_jester_lynch_causes_death_following_night(self) -> None:
        """
        Lynch the Jester, then make sure graveyard has a suicide in it
        """
        self.step_to_next(TurnPhase.DAYLIGHT)
        jester = self._game.get_live_actors_by_role(Jester)[0]

        jester.lynch()

        self.assertEqual(len(self._game.graveyard), 1)

        self.step_to_next(TurnPhase.DAYLIGHT)
        self.assertEqual(len(self._game.graveyard), 2)

        # make sure the Jester wins here too
        wcs, winners = self._evaluate_win()
        self.assertIn(JesterWin, wcs)

    def test_jester_killed_loses(self) -> None:
        """
        Kill the Jester and make sure the Jester loses
        """
        self.step_to_next(TurnPhase.DAYLIGHT)
        jester = self._game.get_live_actors_by_role(Jester)[0]
        jester.kill()

        wcs, winners = self._evaluate_win()
        self.assertNotIn(JesterWin, wcs)

        self.step_to_next(TurnPhase.DAYLIGHT)
        self.assertEqual(len(self._game.graveyard), 1)

    def test_jester_alive_loses(self) -> None:
        self.step_to_next(TurnPhase.DAYLIGHT)
        wcs, winners = self._evaluate_win()
        self.assertNotIn(JesterWin, wcs)


if __name__ == "__main__":
    unittest.main()
