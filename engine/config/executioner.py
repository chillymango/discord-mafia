# this file is automatically generated by engine/config/gen.py


import typing as T
from pydantic import Field
from engine.config import Section


class ExecutionerSection(Section):

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Executioner", "A1", "B15")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])

    becomes_jester_upon_failure: bool = True
    target_is_always_town: bool = True
    must_survive_to_the_end: bool = False
    invulnerable_at_night: bool = True
