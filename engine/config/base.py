import typing as T

from pydantic import BaseModel
from util.string import camel_to_snake


class Section(BaseModel):
    """
    A section of a game config.

    This is just a duck type.
    """

    @classmethod
    def name(cls) -> str:
        return camel_to_snake(cls.__name__)

    @classmethod
    def fmt_range(cls) -> str:
        return "'{0}'!{1}:{2}".format(*cls.sheet_range())

    @staticmethod
    def sheet_range() -> T.Tuple[str, str, str]:
        """
        Returns the range in the default sheet.

        The range can include empty cells that are unused.
        """
        raise NotImplementedError("Inheriting classes must define a section.")

    @staticmethod
    def ingest(sheet_section: T.List[T.List[str]]) -> T.Any:
        raise NotImplementedError("Inheriting classes must define their config section")

    @classmethod
    def hydrate(cls, sheet_section: T.List[T.List[str]]) -> "Section":
        return cls(**cls.ingest(sheet_section))
