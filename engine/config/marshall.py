# this file is automatically generated by engine/config/gen.py


import typing as T
from pydantic import Field
from engine.config import Section


class MarshallSection(Section):

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Marshall", "A1", "B15")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])

    group_executions_allowed: int = 1
    executions_per_group: int = 3
