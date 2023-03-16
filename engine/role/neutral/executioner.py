import logging
import random
import typing as T

from engine.action.annoy import Annoy
from engine.action.base import ActionSequence
from engine.role.neutral import NeutralRole
from engine.role.town.mayor import Mayor
from engine.role.town.marshall import Marshall
from engine.role.town.constable import Constable
from engine.wincon import WinCondition
from engine.wincon import ExecutionerWin
import log

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game

logger = logging.getLogger(__name__)
logger.addHandler(log.ch)
logger.setLevel(logging.INFO)


# confirmable Town roles here
BLOCKLISTED_ROLES = (
    Mayor,
    Marshall,
    Constable,
)


class Executioner(NeutralRole):

    executioner_target: "Actor" = None

    @classmethod
    def role_description(cls) -> str:
        """
        This should describe the role at a high-level.

        Generally safe for this to be flavor-text. Probably also going to be fed into
        the ChatGPT prompt as part of input tuning.
        """
        return "An obsessed hunter whose life's goal is to get his target justly executed."

    def init_with_game(self, game: "Game") -> None:
        """
        Assign an `executioner_target` based on the game setup.
        
        TODO: target currently is always Town
        """
        tries = 0
        while tries < 15:
            tries += 1
            candidate = random.choice(game.get_live_town_actors())
            if type(candidate.role) not in BLOCKLISTED_ROLES:
                break
        else:
            logger.warning(f"Failed to select a non-blocklisted role. Picking one randomly.")

        self.executioner_target = candidate
        logger.info(f"Selected executioner target {self.executioner_target}")

    @classmethod
    def win_condition(cls) -> T.Type[WinCondition]:
        return ExecutionerWin

    @classmethod
    def day_action_description(cls) -> str:
        """
        This should describe the day action at a high-level.
        """
        return "Your role does not have a day action."

    @classmethod
    def night_action_description(cls) -> str:
        """
        This should describe the night action at a high-level.
        """
        return "Your role does not have a night action." 

    def _role_specific_config_init(self) -> None:
        self._night_immune = self._config.role_config.executioner.invulnerable_at_night
        self._target_is_always_town = self._config.role_config.executioner.target_is_always_town
        self._must_survive_to_end = self._config.role_config.executioner.must_survive_to_the_end
        self._becomes_jester_upon_failure = self._config.role_config.executioner.becomes_jester_upon_failure
