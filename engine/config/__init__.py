"""
Game Configuration
"""
import asyncio
import json
import logging
import os
import time
import typing as T
from collections import defaultdict

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from pydantic import BaseModel
from pydantic import Field

import log
from engine.config.base import Section
from engine.config.game import RoleConfigMixin
from engine.role import NAME_TO_ROLE
from util.string import camel_to_english
from util.string import fmt_to_excel_title

logger = logging.getLogger(__name__)
logger.addHandler(log.ch)
logger.setLevel(logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


TOKENFILE_PATH = os.environ.get("GOOGLE_SHEETS_API_TOKEN")
if TOKENFILE_PATH is None:
    raise OSError("Need to specify Google Sheets API token")

TOKEN = json.load(open(TOKENFILE_PATH))
GOOGLE_CREDS = creds = ServiceAccountCreds(**TOKEN)


class ConfigError(ValueError):
    """
    Exception class for a bad configuration
    """


class SheetsFetcher:
    """
    Fetch game config from Sheets API
    """

    def __init__(self, creds=GOOGLE_CREDS) -> None:
        self._creds = creds
        self._read_results: T.Dict[str, T.List[T.List[str]]] = dict()

    @property
    def read_results(self) -> T.Dict[str, T.List[T.List[str]]]:
        return self._read_results

    @staticmethod
    def fmt_range(sheet_name: str, _range: str) -> str:
        return f"'{sheet_name}'!{_range}"

    async def fetch_config(self, sheet_id: str, sections: T.Iterable[T.Type["Section"]]) -> None:
        t_i = time.time()
        async with Aiogoogle(service_account_creds=self._creds) as aiogoogle:
            await asyncio.gather(*[self.read_from_sheets(
                aiogoogle, sheet_id, section.fmt_range()
            ) for section in sections])
        delta = time.time() - t_i
        logger.info(f"Fetching sheet {sheet_id} took {delta}s")

    async def fetch_all_role_configs(self, sheet_id: str) -> None:
        t_i = time.time()
        async with Aiogoogle(service_account_creds=self._creds) as aiogoogle:
            await asyncio.gather(*[self.read_role_config(aiogoogle, sheet_id, role_name)
                                   for role_name in NAME_TO_ROLE.keys()])
        delta = time.time() - t_i
        logger.info(f"Fetching role configs from sheet {sheet_id} took {delta}s")

    async def read_role_config(self, aiogoogle, sheet_id: str, role_name: str) -> None:
        """
        All role configs are two column, up to 15 rows.
        """
        sheets_v4 = await aiogoogle.discover('sheets', 'v4')
        #role_name = camel_to_english(role_name)
        range = f"'{role_name}'!A1:B15"
        logger.info(range)
        try:
            result = await aiogoogle.as_service_account(
                sheets_v4.spreadsheets.values.get(spreadsheetId=sheet_id, range=range)
            )
            self._read_results[role_name] = result["values"]
        except Exception as exc:
            logger.warning(f"No role config for {role_name}")
            self._read_results[role_name] = [[]]

    async def read_from_sheets(self, aiogoogle, sheet_id: str, range: str) -> None:
        logger.debug(f"starting reading {range}")
        sheets_v4 = await aiogoogle.discover('sheets', 'v4')
        try:
            result = await aiogoogle.as_service_account(
                sheets_v4.spreadsheets.values.get(spreadsheetId=sheet_id, range=range)
            )
            self._read_results[range] = result["values"]
        except Exception as exc:
            logger.warning(f"No config for {range}")
            self._read_results[range] = [[]]
        logger.debug(f"finished reading {range}")


class RoleList(Section):
    """
    A list of role groups and role names that appear in the game.
    """

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Setup Configuration", "A2", "A16")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.List[str]:
        return [sheet_section[idx][0] for idx in range(len(sheet_section))]


class ExcludesList(Section):
    """
    A list of role groups and the child groups or role names that
    are excluded from them.
    """

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Setup Configuration", "C2", "D60")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.List[T.Tuple[str, str]]:
        return [
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ]


class RoleWeights(Section):
    """
    A list of roles and their relative weighting. All values should be constrained
    to between 0 and 1.
    """

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Setup Configuration", "F2", "G60")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])


class Timing(Section):
    """
    A list of timing parameters and their values
    """

    day_duration: float = 120.0
    night_duration: float = 60.0
    trial_defense_duration: float = 30.0
    lynch_vote_duration: float = 30.0
    skip_first_day: bool = True

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Timing", "A1", "B20")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0].lower().replace(' ', '_'), sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])


class RoleConfig(Section):
    """
    A role-specific config.

    This is always just a mapping.
    """

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])


class GameConfig:
    """
    The body of this should boil down to a nested dictionary
    """

    # setup config segments
    SEGMENTS: T.List[T.Type["Section"]] = [
        RoleList,
        ExcludesList,
        RoleWeights,
        Timing,
    ]

    def __init__(self, config_dict: T.Dict[str, T.Any]) -> None:
        self._config_dict = config_dict
        self.role_config: RoleConfigMixin = RoleConfigMixin()

        # these are not loaded from an Excel sheet (yet)
        self.preferred_role: T.Dict[str, str] = dict()
        self.blocked_role: T.Dict[str, str] = dict()

        # this is for type annotations primarily
        self.role_weights: T.Dict[str, float] = dict()
        self.role_list: T.List[str] = list()
        self.excludes_list: T.List[T.Tuple[str, str]] = list()

        # TODO: this is kinda bad
        self.timing: Timing = Timing()

        # make the config accessible
        self.__dict__.update(self._config_dict)

        if not self.role_list:
            # this is required so we need it
            raise ConfigError("Did not find a list of weights")

        if not self.role_weights:
            default_weight = 0.3
            logger.warning(f"Did not find role weights. Defaulting to {default_weight}.")
            self.role_weights = defaultdict(lambda: default_weight)

        if not self.excludes_list:
            logger.warning(f"Did not find a list of role excludes. This is probably incorrect")

    @classmethod
    def default_with_role_list(cls, role_list: T.List[str], **kwargs) -> "GameConfig":
        config_dict = dict(role_list=role_list)
        config_dict.update(kwargs)
        return cls(config_dict)

    @classmethod
    async def parse_from_google_sheets_id(cls, sheet_id: str) -> "GameConfig":
        """
        Fetch a config stored in a Google sheet and parse it into a game config
        object. The fetch is done asynchronously.
        """
        fetcher = SheetsFetcher()
        role_config_sections = RoleConfigMixin.get_list_of_sections()
        await fetcher.fetch_config(sheet_id, cls.SEGMENTS + role_config_sections)
        config_dict: T.Dict[str, T.Any] = dict()
        for t_segment in cls.SEGMENTS:
            config_dict[t_segment.name()] = t_segment.ingest(fetcher.read_results[t_segment.fmt_range()])

        # setup the role config object
        instantiated_role_configs = [rc for rc in config_dict.values() if type(rc) in role_config_sections]
        role_config = RoleConfigMixin.construct_from_sections(instantiated_role_configs)
        output = cls(config_dict)
        output.role_config = role_config
        output.timing = Timing.hydrate(fetcher._read_results[Timing.fmt_range()])
        return output

    @classmethod
    def parse_from_dict(cls, config_dict: T.Dict) -> "GameConfig":
        logger.info(f"Parsing config from dict: {config_dict}")


if __name__ == "__main__":
    with open('service_token.json') as service_token:
        token = json.loads(service_token.read())

    creds = ServiceAccountCreds(**token)
    fetch = SheetsFetcher(creds)
    SHEET_ID = '1PMiXU_B2eATCXlZuFsEuKFa9KjDCSWdC9ONlQ6OZY6Q'

    async def main() -> None:
        config = await GameConfig.parse_from_google_sheets_id(SHEET_ID)
        print('done?')
        import pdb; pdb.set_trace()
        print('lol')

    asyncio.run(main())
