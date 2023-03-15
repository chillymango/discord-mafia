import typing as T

from engine.action.base import Action
from engine.role.base import Role
from engine.role.mafia.consigliere import Consigliere
from engine.role.mafia.godfather import Godfather
from engine.role.mafia.mafioso import Mafioso
from engine.role.neutral.jester import Jester

if T.TYPE_CHECKING:
    from engine.actor import Actor


class Transform(Action):
    """
    Transform a player role into another role
    """

    def target_text_success(self) -> str:
        return f"You became a {self._action_result.get('new_role', 'UNKNOWN')}"

    @classmethod
    def new_role(cls) -> T.Type[Role]:
        raise NotImplementedError("Inheriting classes must define this or give some way of obtaining it.")

    def action_result(self, actor: "Actor", target: "Actor") -> T.Optional[bool]:
        # always apply to action source
        # TODO: should we attach the transformer to the actor?
        # depends on where RoleFactory comes from i guess, TBD
        target.game.transform_actor_role(target, self.new_role())
        self._action_result['new_role'] = target.role.name
        return True
        

class ConsiglierePromote(Transform):
    """
    Transform a Consigliere into a Godfather
    """

    def target_text_success(self) -> str:
        return f"With the Godfather gone, it is your turn to lead the famiglia. You are now the Godfather."

    @classmethod
    def new_role(cls) -> T.Type[Role]:
        return Godfather


class MafiosoDemote(Transform):
    """
    Transform a Mafia role into a Mafioso
    """

    def target_text_success(self) -> str:
        return f"With no killing roles left on your team, you must now act as a Mafioso."

    @classmethod
    def new_role(cls) -> T.Type[Role]:
        return Mafioso


class ExecutionerLoss(Transform):
    """
    Transform an Executioner into a Jester
    """

    def target_text_success(self) -> str:
        return f"The death of your target has driven you insane. You are now a Jester."

    @classmethod
    def new_role(cls) -> T.Type[Role]:
        return Jester
