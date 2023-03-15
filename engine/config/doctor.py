# this file is automatically generated by engine/config/gen.py


import typing as T
from pydantic import Field
from engine.config import Section


class DoctorSection(Section):

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        return ("Doctor", "A1", "B15")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Dict[str, str]:
        return dict([
            (sheet_section[idx][0], sheet_section[idx][1])
            for idx in range(len(sheet_section))
        ])

    know_if_target_is_attacked: bool = True
