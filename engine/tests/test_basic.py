"""
Make some shit up here
"""
import unittest

from engine.actor import Actor
from engine.game import Game
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import RoleFactory
from engine.role.mafia.godfather import Godfather
from engine.role.neutral.serialkiller import SerialKiller
from engine.role.town.doctor import Doctor
from engine.role.town.detective import Detective
from engine.role.town.escort import Escort
from engine.role.town.lookout import Lookout
from engine.role.town.partyhost import PartyHost
from engine.stepper import advance


class TestSequencesForFun(unittest.TestCase):

    def test_setup(self) -> None:
        # create a few roles for fun
        config = {
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
                    "kills_roleblocker": True,
                    "rb_immune": True,
                    "night_immune": True,
                    "detect_immune": True,
                }
            },
            "setup": {
                "role_list": [
                    "RoleGroup::TownGovernment",
                    "RoleGroup::TownRandom",
                    "RoleName::Godfather",
                ]
            }
        }
        rf = RoleFactory(config)
        det = rf.create_role(Detective)
        lo = rf.create_role(Lookout)
        escort = rf.create_role(Escort)
        gf = rf.create_role(Godfather)
        doc = rf.create_role(Doctor)
        ph = rf.create_role(PartyHost)
        sk = rf.create_role(SerialKiller)

        # TODO: a pydantic model for this would probably be good
        p1 = Player("Albert Yang")
        p2 = Player("Brian Yang")
        p3 = Player("Jerry Feng")
        p4 = Player("Mimi Jiao")
        p5 = Player("Anthony Chen")
        p6 = Player("William Yuan")
        p7 = Player("Brandon Chen")

        game = Game()
        a1 = Actor(p1, det, config, game)
        a2 = Actor(p2, lo, config, game)
        a3 = Actor(p3, escort, config, game)
        a4 = Actor(p4, gf, config, game)
        a5 = Actor(p5, doc, config, game)
        a6 = Actor(p6, ph, config, game)
        a7 = Actor(p7, sk, config, game)

        game.add_actors(a1, a2, a3, a4, a5, a6, a7)
        self.assertEqual(len(a1.get_target_options()), 6)
        self.assertEqual(len(a2.get_target_options()), 7)
        a1.choose_targets(a2)  # det follows lo
        a2.choose_targets(a3)  # lo watches escort
        a3.choose_targets(a4)  # escort RBs gf (rejected)
        a4.choose_targets(a5)  # gf kills doc
        game._turn_number = 1
        game._turn_phase = TurnPhase.NIGHT
        advance(game)
        advance(game)
        advance(game)
        self.assertEqual(game.kill_report._public, 1)


if __name__ == "__main__":
    unittest.main()
