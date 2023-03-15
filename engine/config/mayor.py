# this file is automatically generated by engine/config/gen.py


import typing as T
from pydantic import Field
from engine.config import Section


class MayorSection(Section):

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Mayor", "A1", "B15")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])

    cannot_be_healed: bool = True
    vote_count: int = 4
