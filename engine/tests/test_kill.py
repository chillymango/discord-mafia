"""
Why could the vig kill the gf
"""
import mock
import unittest
from engine.game import Game
from engine.actor import Actor
from engine.phase import TurnPhase
from engine.player import Player
from engine.role.base import Role
from engine.role.base import RoleFactory
from engine.tribunal import Tribunal

from engine.stepper import sleep_override
from engine.stepper import Stepper


class TestKillingPowers(unittest.TestCase):
    
    def setUp(self) -> None:
        print("\n---Starting Test---\n")
        self._game = Game()
        self._game.messenger = mock.MagicMock()
        self._game.announce = mock.MagicMock()
        self._game.flush_all_messages = mock.MagicMock()
        self._tribunal = Tribunal(self._game, {})
        self._game.tribunal = self._tribunal
        self._stepper = Stepper(self._game, {}, sleep_override)
        # test with defaults i guess
        self._rf = RoleFactory({})
        self._actors = [
            Actor(Player("Albert Yang"), self._rf.create_by_name("Godfather"), self._game),
            Actor(Player("Anthony Chen"), self._rf.create_by_name("Vigilante"), self._game),
            Actor(Player("Brandon Chen"), self._rf.create_by_name("MassMurderer"), self._game),
            Actor(Player("Jerry Feng"), self._rf.create_by_name("SerialKiller"), self._game),
            Actor(Player("Mimi Jiao"), self._rf.create_by_name("Bodyguard"), self._game),
            Actor(Player("William Yuan"), self._rf.create_by_name("Veteran"), self._game),
            Actor(Player("Kurtis Carsch"), self._rf.create_by_name("Doctor"), self._game),
            Actor(Player("Tyler Port"), self._rf.create_by_name("Survivor"), self._game),
            Actor(Player("S.J Guth"), self._rf.create_by_name("Bodyguard"), self._game),
        ]
        self._game.add_actors(*self._actors)

        # always init to night
        for _ in range(4):
            self._stepper.advance(self._game)
        self.assertEqual(self._game._turn_phase, TurnPhase.NIGHT)

    def tearDown(self) -> None:
        print("\n---Ending Test---\n")

    def _run(self) -> None:
        for _ in range(2):
            self._stepper.advance(self._game)

    def test_godfather_ni(self) -> None:
        gf = self._actors[0]
        vig = self._actors[1]
        gf.choose_targets(vig)
        vig.choose_targets(gf)

        self._run()

        self.assertEqual(vig.is_alive, False)
        self.assertEqual(gf.is_alive, True)

    def test_vet_ignore_ni(self) -> None:
        vet = self._actors[5]
        gf = self._actors[0]
        vig = self._actors[1]
        vet.choose_targets(vet)
        gf.choose_targets(vet)
        vig.choose_targets(vet)

        self._run()

        self.assertEqual(vet.is_alive, True)
        self.assertEqual(gf.is_alive, False)
        self.assertEqual(vig.is_alive, False)

    def test_bg_ignore_ni(self) -> None:
        bg = self._actors[4]
        self.assertEqual(bg.role.name, "Bodyguard")
        gf = self._actors[0]
        self.assertEqual(gf.role.name, "Godfather")
        vig = self._actors[1]
        self.assertEqual(vig.role.name, "Vigilante")
        bg.choose_targets(vig)
        gf.choose_targets(vig)

        self._run()

        self.assertEqual(gf.is_alive, False)
        self.assertEqual(bg.is_alive, False)
        self.assertEqual(vig.is_alive, True)

    def test_gf_can_be_healed_thru_bg_fight(self) -> None:
        gf = self._actors[0]
        doc = self._actors[6]
        bg = self._actors[4]
        vig = self._actors[1]

        doc.choose_targets(gf)
        bg.choose_targets(vig)
        gf.choose_targets(vig)

        self._run()

        self.assertEqual(bg.is_alive, False)
        self.assertEqual(gf.is_alive, True)
        self.assertEqual(vig.is_alive, True)

    def test_bg_visits_vet_kills_bg(self) -> None:
        bg = self._actors[4]
        vet = self._actors[5]
        bg.choose_targets(vet)
        vet.choose_targets(vet)

        self._run()

        self.assertEqual(vet.is_alive, True)
        self.assertEqual(bg.is_alive, False)

    def test_bg_double_visit_no_kills(self) -> None:
        bg1 = self._actors[4]
        bg2 = self._actors[8]
        vig = self._actors[1]
        bg1.choose_targets(vig)
        bg2.choose_targets(vig)

        self._run()

        self.assertEqual(bg1.is_alive, True)
        self.assertEqual(bg2.is_alive, True)

    def test_bg_cannot_protect_against_two_attackers(self) -> None:
        bg = self._actors[8]
        vig = self._actors[1]
        gf = self._actors[0]
        doc = self._actors[6]

        bg.choose_targets(doc)
        vig.choose_targets(doc)
        gf.choose_targets(doc)

        self._run()
        self.assertEqual(doc.is_alive, False)
        self.assertEqual(bg.is_alive, False)
        # one of them should randomly die
        self.assertTrue(not gf.is_alive or not vig.is_alive)

    def test_doc_heal(self) -> None:
        doc = self._actors[6]
        vig = self._actors[1]
        gf = self._actors[0]
        gf.choose_targets(vig)
        doc.choose_targets(vig)

        self._run()

        self.assertEqual(vig.is_alive, True)

    def test_doc_heal_even_if_killed(self) -> None:
        doc = self._actors[6]
        vig = self._actors[1]
        gf = self._actors[0]
        gf.choose_targets(vig)
        vig.choose_targets(doc)  # that's cold man
        doc.choose_targets(vig)

        self._run()

        self.assertEqual(vig.is_alive, True)
        self.assertEqual(doc.is_alive, False)

    def test_vests_confer_ni(self) -> None:
        surv = self._actors[7]
        vig = self._actors[1]
        vig.choose_targets(surv)
        self.assertTrue(surv.put_on_vest())
        self.assertFalse(vig.put_on_vest())
        self._run()

        self.assertEqual(surv.is_alive, True)


if __name__ == "__main__":
    unittest.main()
