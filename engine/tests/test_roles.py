"""
OH BOY

time to start writing tests for role interactions
"""
import typing as T
import unittest

from engine.actor import Actor
from engine.game import Game
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import RoleFactory
from engine.role.mafia.consigliere import Consigliere
from engine.role.mafia.godfather import Godfather
from engine.role.neutral.serialkiller import SerialKiller
from engine.role.town.doctor import Doctor
from engine.role.town.detective import Detective
from engine.role.town.escort import Escort
from engine.role.town.investigator import Investigator
from engine.role.town.sheriff import Sheriff
from engine.role.town.lookout import Lookout
from engine.role.town.partyhost import PartyHost
from engine.stepper import advance


class TestRoles(unittest.TestCase):

    def advance(self, phases: int) -> None:
        for _ in range(phases):
            advance(self._game)

    def setUp(self):
        self._config = {
            "roles": {
                "Godfather": {
                    "night_immune": True,
                    "rb_immune": True,
                    "target_immune": False,
                    "detect_immune": True,
                },
                "Lookout": {
                    "allow_self_target": True,
                },
                "SerialKiller": {
                    "intercept_rb": True,
                    "rb_immune": True,
                    "night_immune": True,
                    "detect_immune": True,
                }
            },
            "setup": {
                "role_list": [
                    "RoleGroup::TownGovernment",
                    "RoleGroup::TownRandom",
                    "RoleName::Godfather"
                ],
                "distributions": {
                    "SerialKiller": 1.0,
                    "Constable": 0.7
                }
            }
        }
        self._players = [
            Player("Albert Yang"),
            Player("Brian Yang"),
            Player("Jerry Feng"),
            Player("Mimi Jiao"),
            Player("Anthony Chen"),
            Player("William Yuan"),
            Player("Brandon Chen"),
            Player("Kurtis Carsch"),
            Player("James Holden"),
        ]
        rf = RoleFactory(self._config)
        self._roles = [
            rf.create_role(Godfather),
            rf.create_role(Consigliere),
            rf.create_role(Lookout),
            rf.create_role(Sheriff),
            rf.create_role(Escort),
            rf.create_role(SerialKiller),
            rf.create_role(Investigator),
            rf.create_role(Doctor),
            rf.create_by_name("Executioner"),
        ]
        self._game = Game()
        self._actors: T.List[Actor] = []
        for idx in range(len(self._players)):
            self._actors.append(Actor(self._players[idx], self._roles[idx], self._config, self._game))
        self._game.add_actors(*self._actors)
        self._game._turn_phase = TurnPhase.NIGHT_SEQUENCE  # do just one process
        self._game._turn_number = 1

    def assert_has_message(self, actor: "Actor", contains: str) -> T.Optional[T.NoReturn]:
        """
        Check an actor's messages to ensure that some string is contained in the message queue.
        """
        for message in actor._message_queue:
            if contains in repr(message):
                return
        self.assertTrue(False)

    def test_investigative_roles_against_det_immune(self):
        # consig targets serial killer, should get citizen
        self._actors[1].choose_targets(self._actors[5])
        advance(self._game)
        self.assert_has_message(self._actors[1], "is a Citizen")

    def test_investigative_roles_against_normal(self):
        # consig targets Sheriff, should get Sheriff
        self._actors[1].choose_targets(self._actors[3])
        advance(self._game)
        self.assert_has_message(self._actors[1], "is a Sheriff")

    def test_crimes(self):
        # Consig does investigate on N1, make sure Invest can see on N2
        self._actors[6].choose_targets(self._actors[1])
        self.advance(4)
        self.assert_has_message(self._actors[6], "not committed any crimes")
        self._actors[-1].choose_targets(self._actors[1])
        self._actors[1].choose_targets(self._actors[3])
        self.advance(2)
        self.assert_has_message(self._actors[6], "Trespassing")

    def test_lookout(self):
        # party at 3's house
        self._actors[0].choose_targets(self._actors[3])
        self._actors[1].choose_targets(self._actors[3])
        self._actors[2].choose_targets(self._actors[3])
        self.advance(2)
        self.assert_has_message(self._actors[2], "Albert")
        self.assert_has_message(self._actors[2], "Brian")
        self.assert_has_message(self._actors[2], "Jerry")

    def test_doctor_heal(self):
        # 0 kills 3, 7 heals 3, verify this works
        self._actors[0].choose_targets(self._actors[3])
        self._actors[7].choose_targets(self._actors[3])
        self.advance(2)
        self.assertTrue(self._actors[3].is_alive)

    def test_doctor_cant_heal_both(self):
        # 0 kills 3, 5 kills 3, 7 heals 3, 3 still dies
        self._actors[0].choose_targets(self._actors[3])
        self._actors[5].choose_targets(self._actors[3])
        self._actors[7].choose_targets(self._actors[3])
        self.advance(2)
        self.assertFalse(self._actors[3].is_alive)

    def test_sk_kills_roleblocker(self):
        # 4 visits 5, 5 targets 1, 5 kills 4
        self._actors[4].choose_targets(self._actors[5])
        self._actors[5].choose_targets(self._actors[1])
        self.advance(2)
        self.assertFalse(self._actors[4].is_alive)
        self.assertTrue(self._actors[5].is_alive)


if __name__ == "__main__":
    unittest.main()
