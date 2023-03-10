import typing as T

from engine.action.base import Action
from engine.affiliation import MAFIA
from engine.affiliation import NEUTRAL
from engine.affiliation import TOWN
from engine.crimes import Crime
from engine.role.mafia.mafioso import Mafioso
from engine.role.neutral.scumbag import Scumbag
from engine.role.town.bodyguard import Bodyguard
from engine.role.town.citizen import Citizen

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.role.base import Role


class Audit(Action):
    """
    Auditor changes target's role.

    If target is protected by a bodyguard, or is night immune, they are
    unable to be audited.

    Townies become Citizen.
    Mafia become Mafioso.
    Neutrals become Scumbag.
    """

    # ahh yeah let the other actions
    ORDER = 1100

    @property
    def crimes(self) -> T.Dict[bool, T.Iterable["Crime"]]:
        return {
            True: [Crime.CORRUPTION],
        }

    def action_result(self, actor: "Actor", *targets: "Actor") -> None:
        """
        Action will fail if:
            * target is dead
            * target is guarded by a bodyguard
            * target is night immune
            * target is a Cultist
        """
        return True

    def target_title(self, success: bool) -> str:
        return "Audit Action"

    def feedback_text_fail(self) -> str:
        return f"Your target was too much for you! You were unable to audit them."

    def feedback_text_success(self) -> str:
        return f"You audited your target for tax evasion. They are now a " \
            f"{self._action_result.get('new_role')}."

    def target_text_success(self) -> str:
        return f"You have been audited for tax evasion! You are now a " \
            f"{self._action_result.get('new_role')}"

    def get_new_role(self, target: "Actor") -> T.Type["Role"]:
        if target.role.affiliation() == TOWN:
            return Citizen
        if target.role.affiliation() == NEUTRAL:
            return Scumbag
        if target.role.affiliation() == MAFIA:
            return Mafioso

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        if target.role._night_immune:
            return False

        # TODO: check for cult
        bgs = actor._game.get_live_actors_by_role(Bodyguard)
        for bg in bgs:
            if target in bg.targets:
                return False

        new_role = self.get_new_role(target)
        if new_role is None:
            return False
        target.game.transform_actor_role(target, new_role)
        self._action_result['new_role'] = target.role.name
        return True
