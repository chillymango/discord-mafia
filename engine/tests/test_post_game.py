import typing as T
import unittest

from engine.game import Game
from engine.player import Player

from engine.actor import Actor
from engine.affiliation import TOWN
from engine.role.base import RoleFactory
from engine.role.neutral.jester import Jester
from engine.setup import do_setup
from engine.wincon import EvilWin
from engine.wincon import WinCondition
from engine.wincon import JesterWin
from engine.wincon import MafiaWin
from engine.wincon import SerialKillerWin
from engine.wincon import SurvivorWin
from engine.wincon import TownWin


class TestPostGame(unittest.TestCase):
    """
    Imagine running it back over and over again
    """

    def setUp(self) -> None:
        self._game = Game(config={})
        names = [
            "Theodore Roosevelt",
            "Grover Cleveland",
            "Woodrow Wilson",
            "Franklin D. Roosevelt",
            "Harry Truman",
            "Dwight D. Eisenhower",
            "John F. Kennedy",
            "Richard Nixon",
            "Jimmy Carter",
            "George H.W. Bush",
            "Bill Clinton",
            "George W. Bush",
            "Barack Obama",
            "Donald Trump",
            "Joe Biden",
        ]

        rf = RoleFactory({})
        role_names = [
            # 3 Mafia
            "Godfather",
            "Janitor",
            "Mafioso",
            # 6 Town
            "Mayor",
            "Doctor",
            "Bodyguard",
            "Investigator",
            "Lookout",
            "Detective",
            # 2 NE, 2 NK, 2 NB
            "Survivor",
            "SerialKiller",
            "MassMurderer",
            "Jester",
            "Auditor",
            "Judge",
        ]
        actors = [Actor(Player(name), rf.create_by_name(role_name), self._game) for name, role_name in zip(names, role_names)]
        self._game.add_actors(*actors)

    def _kill_all_players(self) -> None:
        for actor in self._game.actors:
            actor.kill()

    def get_actor_with_role(self, role_name: str) -> "Actor":
        for actor in self._game.actors:
            if actor.role.name == role_name:
                return actor

    def _evaluate_win(self) -> T.Tuple[T.Set[WinCondition], T.List[Actor]]:
        winners = self._game.evaluate_post_game()
        wcs = set([winner.role.win_condition() for winner in winners])
        return (wcs, winners)

    def test_mafia_win(self) -> None:
        # kill most players
        self._kill_all_players()

        # bring some back and then evaluate WC
        self.get_actor_with_role('Godfather')._is_alive = True

        wcs, winners = self._evaluate_win()
        self.assertEqual(len(winners), 3)
        self.assertIn(MafiaWin, wcs)

    def test_town_win(self) -> None:
        # kill all evils
        for actor in self._game.get_live_evil_actors():
            actor.kill()
        wcs, winners = self._evaluate_win()
        self.assertEqual(len(winners), 9)  # make sure surv also wins
        self.assertIn(TownWin, wcs)
        self.assertIn(SurvivorWin, wcs)

    def test_sk_win(self) -> None:
        for actor in self._game.get_live_actors():
            actor.kill()
        self.get_actor_with_role('Serial Killer')._is_alive = True

        wcs, winners = self._evaluate_win()
        self.assertEqual(len(winners), 1)
        self.assertIn(SerialKillerWin, wcs)

    def test_jester_win(self) -> None:
        for actor in self._game.get_live_actors():
            if isinstance(actor.role, Jester):
                actor.lynch()

        wcs, _ = self._evaluate_win()
        self.assertIn(JesterWin, wcs)

    def test_neutral_evil_win_with_mafia(self) -> None:
        for actor in self._game.get_live_actors():
            if actor.role.affiliation() == TOWN:
                actor.kill()
            if actor.role.name in ("Serial Killer", "Mass Murderer"):
                actor.kill()

        # test to make sure neut evils win
        wcs, winners = self._evaluate_win()
        judge_win = False
        auditor_win = False
        self.assertIn(EvilWin, wcs)
        for winner in winners:
            if winner.role.name == "Judge":
                judge_win = True
            elif winner.role.name == "Auditor":
                auditor_win = True

        self.assertTrue(judge_win, "The Judge has won")
        self.assertTrue(auditor_win, "The Auditor has won")


if __name__ == "__main__":
    unittest.main()
