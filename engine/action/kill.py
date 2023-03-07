from enum import Enum
import random
import typing as T

from engine.crimes import Crime
from engine.action.base import Action
from engine.message import Message

if T.TYPE_CHECKING:
    from engine.actor import Actor


class KillCause(Enum):
    GENERIC = 0
    MAFIA = 1
    DISGUISER = 2
    JAILOR = 3
    SERIAL_KILLER = 4
    ARSONIST = 5
    VIGILANTE = 6
    BODYGUARD = 7
    MASS_MURDERER = 8
    VETERAN = 9
    CONSTABLE = 10
    SUICIDE = 11
    LEAVER = 12


class Kill(Action):
    """
    Transition a player state from alive to dead
    """

    ORDER = 100

    @property
    def kill_damage(self) -> int:
        return 1

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.MURDER],
            False: [Crime.TRESPASSING],
        }

    @property
    def ignore_immunity(self) -> bool:
        return False

    def attack(self, actor: "Actor") -> None:
        """
        Do the attack transaction
        """
        actor._attacked_by.append(self.__class__)
        actor.hitpoints -= self.kill_damage
        if actor.hitpoints <= 0:
            # if this hit drives them over the edge, use this assailant's death note
            actor.kill()

    def feedback_text_success(self) -> str:
        return ""

    def feedback_text_fail(self) -> str:
        return "Your target survived your attack! Tonight, they have immunity to conventional attacks!"

    def target_text_success(self) -> str:
        raise NotImplementedError("All kill subclasses must define this manually")

    def target_text_fail(self) -> str:
        return "Someone tried to kill you, but you survived their attack!"

    @classmethod
    def kill_report_text(cls) -> str:
        return "Smited by God (probably a bug, contact devs)"

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        if not self.ignore_immunity and (target.role._night_immune or target._vest_active):
            return False

        # if we get here, the attack goes through and applies damage, but might not kill
        # but we still want to generally report the attack
        self.attack(target)

        return True


class JailorKill(Kill):
    """
    Kill description should update
    """

    @property
    def ignore_immunity(self) -> bool:
        return True

    @property
    def kill_damage(self) -> int:
        """
        100 is an unblockable kill
        """
        return 100

    def announce(self) -> str:
        return "You hear the distinct report of an executioner's rifle"

    @classmethod
    def kill_report_text(cls) -> str:
        return "They were executed in a jail cell"

    def target_text_success(self) -> str:
        return "You were executed by a Jailor."


class InterroKill(JailorKill):
    
    def target_text_success(self) -> str:
        return "You were executed by an Interrogator."


class KidnapKill(JailorKill):

    def target_text_success(self) -> str:
        return "You were executed by a Kidnapper."


class MafiaKill(Kill):
    """
    Godfather / Mafioso Kill
    """

    def announce(self) -> str:
        return random.choice([
            "You hear shots echoing through the streets",
            "You hear the rat-a-tat-tat of a sub-machine-gun in the distance",
            "You hear the sound of gunfire followed by the screeching of tires",
        ])

    @classmethod
    def kill_report_text(cls) -> str:
        return "They were shot multiple times at close range"

    def target_text_success(self) -> str:
        return "You were hit by the Mafia"


class TriadKill(Kill):
    """
    Dragon Head / Enforcer Kill
    """

    def target_text_success(self) -> str:
        return "You were hit by the Triad"


class SerialKillerKill(Kill):

    def announce(self):
        return "You hear the screams of bloody murder"

    @classmethod
    def kill_report_text(cls) -> str:
        return "Stabbed multiple times with a sharp object"

    def target_text_success(self) -> str:
        return "You were killed by a Serial Killer"


class ArsonistKill(Kill):

    @property
    def ignore_immunity(self) -> bool:
        return True

    @property
    def kill_damage(self) -> int:
        """
        100 is an unblockable kill
        """
        return 100

    def announce(self):
        return "You hear the crackling of flames and the screams of doomed souls"

    @classmethod
    def kill_report_text(cls) -> str:
        return "Burned to death"

    def target_text_success(self) -> str:
        return "You were incinerated by an Arsonist"


class VigilanteKill(Kill):

    def announce(self):
        return "You hear a tight grouping of shots echoing throughout the town"

    @classmethod
    def kill_report_text(cls) -> str:
        return "Shot with a large caliber weapon"

    def target_text_success(self) -> str:
        return "You were shot by a Vigilante"


class BodyguardKill(Kill):

    def announce(self):
        return "You hear the harsh sounds of an old-fashioned shootout"

    @classmethod
    def kill_report_text(cls) -> str:
        return "Killed in a duel"

    def target_text_success(self) -> str:
        return "Your target was attacked tonight! You fight off the attacker."


class MassMurder(Kill):
    """
    Commit mass murder at somebody's house

    aka kill everybody who's at this house at night

    MM kills don't have any feedback typically. They will appear in night sequence.
    """

    def target_text_success(self) -> str:
        return ""

    def target_text_fail(self) -> str:
        return ""

    def announce(self):
        return "You hear the sickening sound of a chainsaw ripping through flesh"

    @classmethod
    def kill_report_text(cls) -> str:
        return random.choice([
            "Their entrails were spread around the house.",
            "They were torn to shreds with a chainsaw",
            "They were completely eviscerated",
        ])

    def target_text_success(self) -> str:
        return "You were killed by a Mass Murderer"

    def message_results(self, actor: "Actor", success: bool) -> None:
        """
        A public message is issued for each victim.
        All victims are messaged privately that they were killed.

        MM kill doesn't issue any feedback.
        """
        if not success:
            return

        # TODO: oh this is kinda gross we need to set the target back in order for this to work
        orig_targets = actor.targets
        try:
            for victim, result in self._action_result["victims"]:
                actor.choose_targets(victim)
                super().message_results(actor, result)
        finally:
            actor.choose_targets(*orig_targets)

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        self._action_result["victims"]: T.List[T.Tuple["Actor", bool]] = []
        # target anybody who's at the target's house
        for anon in actor.game.get_live_actors():
            if actor == anon:
                continue
            if target in anon.targets:
                print(f'Running super kill for {actor.name} to {anon.name}')
                result = super().action_result(actor, anon)
                self._action_result["victims"].append((anon, result))
        return True


class Alert(MassMurder):
    """
    The Veteran and the Mass-Murderer are similar in almost every way
    ...
    except the vet can't move and the MM is fully mobile
    just change the kill text
    """

    # this needs to go before most actions
    ORDER = 20

    @property
    def ignore_immunity(self) -> bool:
        return True

    def target_text_success(self) -> str:
        # TODO: we should return multiple entries if multiple assailants are found
        return "You were neutralized by the Veteran you targeted"

    def target_text_fail(self) -> str:
        return ""

    def announce(self):
        return "You hear sounds of combat in the town"

    def feedback_text_success(self) -> str:
        return "You notice an intruder and pull out your gun to deal with them."

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.MURDER, Crime.DESTRUCTION_OF_PROPERTY],
            False: [Crime.MURDER, Crime.DESTRUCTION_OF_PROPERTY],
        }

    @classmethod
    def kill_report_text(cls) -> str:
        return random.choice([
            "Killed by a fragmentation grenade.",
            "Killed by a military grade assault rifle.",
            "Ripped to pieces by a large caliber machine gun."
        ])


class ConstableKill(Kill):
    """
    Shoot the fucker
    """

    def feedback_text_success(self) -> str:
        return ""

    def feedback_text_fail(self) -> str:
        # should never be possible
        return "Something went wrong. Contact the game devs"

    def target_text_success(self) -> str:
        raise NotImplementedError("All kill subclasses must define this manually")

    def target_text_fail(self) -> str:
        # should never be possible
        return ""

    @classmethod
    def instant(cls) -> bool:
        return True

    @classmethod
    def kill_report_text(cls) -> str:
        return "Shot by the Constable."

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        # it's not up for debate
        target._attacked_by.append(self.__class__)
        target.kill()
        self._action_result["victim"] = target
        return True

    def message_results(self, actor: "Actor", success: bool) -> None:
        victim: "Actor" = self._action_result.get("victim")
        if victim is None:
            return
        actor.game.messenger.queue_message(Message.announce(
            actor.game,
            f"{actor.name} the Constable",
            f"Reveals a gun and shoots {victim.name}!\n\n"
            f"Their role was {victim.role.name}."
        ))
